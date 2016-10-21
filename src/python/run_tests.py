#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *

import sys
import test.handler_tests
import re

print("------------------------ python environment")
print(sys.version)
print("-------------------------------------------")


print("** start, context name: " + __name__ + "  argv: ", sys.argv)
if 'one_test' in sys.argv:
  test_name = ''
  for item in sys.argv:
    mObj = re.match('test[0-9][0-9]', item)
    if mObj == None:
      pass
      ##print("** one test - no test name for item: ", item)
    else:
      test_name = mObj.group(0)
      print("** one test - run test name: " + test_name)
      test.handler_tests.run_one_test(sys.argv, test_name)
      print("** one test - end test name: " + test_name)
else:
  test.handler_tests.run_test_suites(sys.argv)
  print("** end, context name: " + __name__)
