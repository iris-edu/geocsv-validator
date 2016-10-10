#!#!/usr/bin/env python

# these imports are to enable writing code in python 3 and
# and also enable the same code to run in python 2.
# Note: "future" must be installed in both pythong 2 and 3
# environment,
from __future__ import absolute_import, division, print_function
from builtins import *
# this is to generate NameError if an obsolete builtin is used
# in the python 2 environment
from future.builtins.disabled import *


import unittest
import main.geocsvValidate

class geocsvValidateTest1TestCase(unittest.TestCase):
  def runTest(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'
    main.geocsvValidate.runvalidate(target_url)

def run_test_cases():
  print ("*********** run_test_cases __name__: ", __name__)
  runner = unittest.TextTestRunner()

  testCase1 = geocsvValidateTest1TestCase()
  runner.run(testCase1)


