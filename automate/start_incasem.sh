#!/bin/bash


echo "Hello user, we are installing incasem for you"

check_conda() {
  STR="no"
  if command -v conda &> /dev/null; then
    STR="conda is installed no need to install it"
    echo $STR
  fi

  if [ "$STR" = "no" ]; then
    echo "Installing conda, please type yes and wait for a few minutes"
    # Get anaconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    chmod +x Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh
    # # evaluating conda
    export PATH=~/miniconda3/bin:$PATH
    rm Miniconda3-latest-Linux-x86_64.*
    source ~/.bashrc
  fi
}

check_conda 

install_path=""
repo_clone_and_setup(){
  echo "Where on your computer would you like to store incasem in? Options can be root, Desktop(recommended), Downloads or a custom path, type it below to install: "
  read -r install_location
  valid_options='["root", "desktop", "downloads"]'
  # corrects errors if the user entered the wrong thing
  correct_location=$(python3 correct_user_inputs_for_script.py "$install_location" "$valid_options")
  case $install_location in
    root)
      install_path="$HOME/incasem"
      ;;
    Desktop)
      install_path="$HOME/Desktop/incasem"
      ;;
    Downloads)
      install_path="$HOME/Downloads/incasem"
      ;;
    *)
      install_path="$install_location/incasem"
  esac
  git clone https://github.com/kirchhausenlab/incasem.git "$install_path" 
}

setup_environment() {
  env_name="incasem"

  echo "Creating the conda environment $env_name"
  conda create --name $env_name python=3.11 -y
  

  echo "running conda init"
  conda init --all

  source ~/.bashrc

  echo "Activating the environment $env_name"
  conda activate $env_name

  echo "Installing dependencies"
  install_dependencies
  python3 -m pip install -r ../requirements.txt

  conda env export > environment.yml
  mv environment.yml ../
}

install_dependencies() {
  # echo "Do you want to make a requirements.txt? (y/n)"
  # read -r res
  #
  # if [ "$res" = "y" ]; then
  if [ ! -f ../requirements.txt ]; then
    pip3 install pipreqs 
    pipreqs ../.
  fi
  #fi
}

main(){
  echo "Hello user, we're setting up incasem"
  check_conda
  echo "Conda installed!"
  repo_clone_and_setup 
  echo "Start the environment"
  setup_environment
  echo "environment" set up
}
