import logging
import numpy as np
from skimage.transform import downscale_local_mean

from gunpowder.nodes.batch_filter import BatchFilter
from gunpowder.array import ArrayKey, Array
from gunpowder.batch_request import BatchRequest
from gunpowder.batch import Batch
from gunpowder import Coordinate

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Downsample(BatchFilter):
    """Downsample arrays in a batch by given factors.

    Args:

        source (:class:`ArrayKey` or ``list`` of :class:`ArrayKey`):

            The key(s) of the array(s) to downsample.

        factor (tuple`` of ``int``):

            The factors to downsample with.

        target (:class:`ArrayKey` or ``list`` of :class:`ArrayKey`):

            The keys(s) of the array(s) to store the downsampled `source`(s).
            The number of `target`s has to match the number of `source`s.

        mode (``str``):

            Downscaling methods:
                `subsample`: Slicing in all dimensions.
                `simulate_em_low_res`: Mean downscaling xy, slicing in z.
                `downscale_local_mean`: Mean downscaling in all dimensions.

            The chosen method will be applied to all `interpolatable` arrays.
    """

    def __init__(self, source, factor, target, mode="simulate_em_low_res"):

        if isinstance(source, ArrayKey):
            self.source = [source]
        else:
            self.source = source
        for s in self.source:
            assert isinstance(s, ArrayKey)

        for f in factor:
            assert isinstance(f, int), \
                "Scaling factor should be a tuple of ints."
        self.factor = Coordinate(factor)

        if isinstance(target, ArrayKey):
            self.target = [target]
        else:
            self.target = target
        for t in self.target:
            assert isinstance(t, ArrayKey)

        if len(self.source) != len(self.target):
            raise ValueError(
                "Number of sources and target arrays does not match.")

        self.mode = mode

    def setup(self):

        self.enable_autoskip()

        for source, target in zip(self.source, self.target):
            spec = self.spec[source].copy()
            spec.voxel_size *= self.factor

            if source == target:
                self.updates(source, spec)
            else:
                self.provides(target, spec)

    def prepare(self, request):

        deps = BatchRequest()

        for source, target in zip(self.source, self.target):
            if target in request:
                spec = request[target].copy()
                if spec.voxel_size is not None:
                    spec.voxel_size = spec.voxel_size // self.factor
                deps[source] = spec

        return deps

    def process(self, batch, request):

        outputs = Batch()

        for source, target in zip(self.source, self.target):
            if target not in request:
                continue

            # Skip if no downsampling is performed
            if self.factor == (1, 1, 1):
                outputs[target] = batch[source]
                continue

            assert np.all(np.array(batch[source].data.shape) % self.factor == 0)

            method = self.mode
            if not batch[source].spec.interpolatable:
                method = "subsample"
            assert batch[source].data.ndim == len(self.factor)
            logger.debug(f"{batch[source].data.shape=}")
            data = self._downscale(batch[source].data, method)
            logger.debug(f"{data.shape=}")

            # Transform back to integer if necessary
            if np.issubdtype(batch[source].data.dtype, np.integer) and np.issubdtype(data.dtype, np.floating):
                logger.info("Transform to integer")
                data = np.around(data).astype(batch[source].data.dtype)

            # create output array
            spec = self.spec[target].copy()
            spec.roi = request[target].roi
            outputs[target] = Array(data, spec)

        return outputs

    def _downscale(self, data, method):
        if method == "subsample":
            logger.debug("Performing discrete slicing")
            slices = tuple(
                slice(None, None, k)
                for k in self.factor)
            out = data[slices]
        elif method == 'downscale_local_mean':
            logger.debug("Performing mean downscaling")
            out = downscale_local_mean(
                image=data,
                factors=self.factor,
            )
        elif method == 'simulate_em_low_res':
            if data.ndim != 3:
                raise ValueError((
                    "Simulation of EM lower resolution only implemented "
                    "for 3D input."
                ))
            logger.debug(
                "Performing mean downscaling in xy and discrete slicing in z")

            # Data is assumed to be in zyx format
            out = downscale_local_mean(
                image=data,
                factors=(1,) + tuple(self.factor[1:3])
            )
            logger.debug(f"Shape after xy downscaling {out.shape}")

            out = out[::self.factor[0], :, :]
            logger.debug(f"Shape after z downscaling {out.shape}")
        else:
            raise ValueError(
                f"downscale method {method} not implemented."
            )

        return out
