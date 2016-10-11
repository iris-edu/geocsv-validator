#!#!/usr/bin/env python

# these imports are to enable writing code in python 3 and
# and also enable the same code to run in python 2.
# Note: "future" must be installed in both python 2 and 3
# environment,
from __future__ import absolute_import, division, print_function
from builtins import *
# this is to generate NameError if an obsolete builtin is used
# in the python 2 environment
from future.builtins.disabled import *


import unittest
import main.geocsvValidate

class geocsvValidateTest1TestCase(unittest.TestCase):
##  def setUp(self):
##    self.t1 = geocsvValidateTest1TestCase()
##  def tearDown(self):
##    self.t1.dispose()
##    self.t1 = None
  def testrunTest1(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'
    main.geocsvValidate.runvalidate(target_url)
  def testrunTest2(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'
    main.geocsvValidate.runvalidate(target_url)

def run_test_cases():
  print ("*********** run_test_cases 2 __name__: ", __name__)
  runner = unittest.TextTestRunner()

  testCase1 = geocsvValidateTest1TestCase("testrunTest1")
  testCase2 = geocsvValidateTest1TestCase("testrunTest2")

  runner.run(testCase1)
  runner.run(testCase2)

def run_test_suites():
  print ("*********** run_test_cases suite __name__: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(geocsvValidateTest1TestCase("testrunTest1"))
  suite.addTest(geocsvValidateTest1TestCase("testrunTest2"))

  runner = unittest.TextTestRunner()
  runner.run(suite)


