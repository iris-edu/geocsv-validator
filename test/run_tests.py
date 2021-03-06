#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *

import sys
import handler_tests
import re

print("** -------- Run all unit tests, context: " + __name__ )
print("** -------- - to run indiviudal tests, use parameter 'doTests' followed by one or more test names")
print("** --------   e.g. ./run_tests.py doTests test06 test17")
print("** -------- - to write report, set 'write_report' in pctl in handler_tests.py to True")
print("** -------- start tests, argv: ", sys.argv)
print("** -------- python environment: ", sys.version.replace('\n',' '))

# quick and dirty for one or a few test:
#   check for arg 'doTests'
#   if found loop through the args looking for a regex name match
#   else do all tests
#
# e.g. run_tests.py doTests testm1

if 'doTests' in sys.argv:
  test_name = ''
  for item in sys.argv:
    mObj = re.match('test[0-9][0-9]|testm4|testm3|testm2|testm1', item)
    if mObj == None:
      if item == 'doTests' or item == sys.argv[0]:
        pass
      else:
        print("** -------- WARNING - unknown test name: ", item)
    else:
      test_name = mObj.group(0) # i.e. same as item
      handler_tests.run_one_test(sys.argv, test_name)
else:
  handler_tests.run_test_suites(sys.argv)

print("** -------- end tests, context: " + __name__)
