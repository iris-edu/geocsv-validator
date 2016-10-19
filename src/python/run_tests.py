#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *

import sys
import test.handler_tests

print("------------------------ python environment")
print(sys.version)
print("-------------------------------------------")

print("** start, context name: " + __name__ + "  argv: ", sys.argv)

test.handler_tests.run_test_suites(sys.argv)

print("** end, context name: " + __name__)
