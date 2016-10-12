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
import test.handler_tests

print("------------------------ python environment")
print(sys.version)
print("------------------------")

print("** start, context name: " + __name__)

verbose = True
test.handler_tests.run_test_suites(verbose)

print("** end, context name: " + __name__)
