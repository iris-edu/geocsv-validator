#!/bin/bash

this_folder=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
isConda=`which conda`

if [ -z ${isConda} ]; then
  echo "*"
  echo "* testing with default python"
  echo "*"
  ${this_folder}/run_tests.py $*
else
  # use conda to switch between anaconda environments
  # run the test suite for each environment

  conda_envs_list=(`conda info --envs | awk '{print $1}' | grep -v '#'`) 

  for ((i=0; i<${#conda_envs_list[@]}; i+=1)); do
    pyenv=${conda_envs_list[${i}]}
    echo "*"
    echo "* testing in env: ${pyenv}"
    echo "*"
    source activate ${pyenv}
    ${this_folder}/run_tests.py $*
  done
fi

