#!/bin/bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

# use anaconda environment command to switch back and forth
# between python 2.x and 3.x and run the test code

source activate root
${dir}/test_driver_script.py


source activate py351
${dir}/test_driver_script.py

