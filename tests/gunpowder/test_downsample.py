from provider_test import ProviderTest
import gunpowder
from gunpowder import (
    BatchProvider,
    ArraySpec,
    Roi,
    Batch,
    Array,
    ArrayKey,
    BatchRequest,
)

import numpy as np
import pytest
import incasem

raw = ArrayKey("RAW")
raw_ds = ArrayKey('RAW_DOWNSAMPLED')
gt = ArrayKey('GT_LABELS')
gt_ds = ArrayKey('GT_LABELS_DOWNSAMPLED')


class DownSampleTestSource(BatchProvider):

    def setup(self):

        self.provides(
            raw,
            ArraySpec(
                roi=Roi((0, 0, 0), (1000, 1000, 1000)),
                voxel_size=(4, 4, 4),
                interpolatable=True,
            )
        )

        self.provides(
            gt,
            ArraySpec(
                roi=Roi((0, 0, 0), (1000, 1000, 1000)),
                voxel_size=(4, 4, 4),
                interpolatable=False,
            )
        )

    def provide(self, request):

        batch = Batch()

        # have the pixels encode their position
        for (array_key, spec) in request.array_specs.items():

            roi = spec.roi

            for d in range(3):
                assert roi.get_begin()[d] % 4 == 0, "roi %s does not align with voxels"

            data_roi = roi / 4

            # the z,y,x coordinates of the ROI
            meshgrids = np.meshgrid(
                range(data_roi.get_begin()[0], data_roi.get_end()[0]),
                range(data_roi.get_begin()[1], data_roi.get_end()[1]),
                range(data_roi.get_begin()[2], data_roi.get_end()[2]), indexing='ij')
            data = meshgrids[0] + meshgrids[1] + meshgrids[2]

            spec = self.spec[array_key].copy()
            spec.roi = roi
            batch.arrays[array_key] = Array(
                data,
                spec)

        return batch


class TestDownSample(ProviderTest):

    def test_output(self):

        ArrayKey('RAW_DOWNSAMPLED')
        ArrayKey('GT_LABELS_DOWNSAMPLED')

        request = BatchRequest()
        request.add(raw, (200, 200, 200))
        request.add(raw_ds, (120, 120, 120))
        request.add(gt, (200, 200, 200))
        request.add(gt_ds, (200, 200, 200))

        pipeline = (
            DownSampleTestSource() +
            incasem.gunpowder.Downsample(raw, (2, 2, 2), raw_ds, mode="subsample") +
            incasem.gunpowder.Downsample(gt, (2, 2, 2), gt_ds, mode="subsample")
        )

        with gunpowder.build(pipeline):
            batch = pipeline.request_batch(request)

        for (array_key, array) in batch.arrays.items():

            # assert that pixels encode their position for supposedly unaltered
            # arrays
            if array_key in [raw, gt]:

                # the z,y,x coordinates of the ROI
                roi = array.spec.roi / 4
                meshgrids = np.meshgrid(
                    range(roi.get_begin()[0], roi.get_end()[0]),
                    range(roi.get_begin()[1], roi.get_end()[1]),
                    range(roi.get_begin()[2], roi.get_end()[2]), indexing='ij')
                data = meshgrids[0] + meshgrids[1] + meshgrids[2]

                self.assertTrue(np.array_equal(array.data, data), str(array_key))

            elif array_key == raw_ds:

                self.assertTrue(array.data[0, 0, 0] == 30)
                self.assertTrue(array.data[1, 0, 0] == 32)

            elif array_key == gt_ds:

                self.assertTrue(array.data[0, 0, 0] == 0)
                self.assertTrue(array.data[1, 0, 0] == 2)

            else:

                self.assertTrue(False, "unexpected array type")


@pytest.mark.parametrize("mode", ["subsample", "simulate_em_low_res", "downscale_local_mean"])
def test_downsample(mode):

    request = BatchRequest()
    request.add(raw, (128, 120, 120))
    request.add(raw_ds, (128, 120, 120))
    request.add(gt, (128, 120, 120))
    request.add(gt_ds, (128, 120, 120))

    pipeline = (
        DownSampleTestSource() +
        incasem.gunpowder.Downsample([raw, gt], (2, 3, 3), [raw_ds, gt_ds], mode=mode)
    )

    with gunpowder.build(pipeline):
        batch = pipeline.request_batch(request)

    for (array_key, array) in batch.arrays.items():

        print(f"{array_key} shape: {array.data.shape}")
        # assert that pixels encode their position for supposedly unaltered
        # arrays
        if array_key in [raw, gt]:

            # the z,y,x coordinates of the ROI
            roi = array.spec.roi / 4
            meshgrids = np.meshgrid(
                range(roi.get_begin()[0], roi.get_end()[0]),
                range(roi.get_begin()[1], roi.get_end()[1]),
                range(roi.get_begin()[2], roi.get_end()[2]), indexing='ij')
            data = meshgrids[0] + meshgrids[1] + meshgrids[2]

            assert np.array_equal(array.data, data), str(array_key)

        elif array_key in (raw_ds, gt_ds):
            np.issubdtype(array.spec.dtype, np.integer)


if __name__ == "__main__":
    test_downsample("simulate_em_low_res")
