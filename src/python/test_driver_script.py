#!/usr/bin/env python

# these imports are to enable writing code in python 3 and
# and also enable the same code to run in python 2.
# Note: "future" must be installed in both python 2 and 3
# environment,
from __future__ import absolute_import, division, print_function
from builtins import *
# this is to generate NameError if an obsolete builtin is used
# in the python 2 environment
from future.builtins.disabled import *

import sys
import test.test_geocsvValidate

print("*********** test driver start, context name: " + __name__ + "  python env: " + sys.version)

test.test_geocsvValidate.run_test_cases()

print("*********** test driver end, context name: ", __name__)
