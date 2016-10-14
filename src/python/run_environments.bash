#!/bin/bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

# use anaconda environment command to switch back and forth
# between python 2.x and 3.x and run the test code

if [ -z "$*" ]; then
  argu1=""
else
  argu1=$1
fi

source activate root
${dir}/run_tests.py ${argu1}


source activate py351
${dir}/run_tests.py  ${argu1}

