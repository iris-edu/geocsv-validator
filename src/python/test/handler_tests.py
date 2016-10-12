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


import unittest
import main.geocsvHandler

g_verbose = False

class ExternalURLTests(unittest.TestCase):
##  def setUp(self):
##    self.t1 = ExternalURLTests(self)
##  def tearDown(self):
##    self.t1.dispose()
##    self.t1 = None
  def test1(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
        + 'query?format=text&showNumberFormatExceptions=true'
    main.geocsvHandler.validate(target_url, g_verbose)
  def test2(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/intermagnet/1/'\
        + 'query?email=geows@iris.washington.edu&accept=true&content=files'\
        + '&format=text&starttime=2014-10-30&endtime=2014-11-01'\
        + '&regions=America,Asia,Europe,Pacific,Africa'\
        + '&latitudes=NH,NM,E,SM,SH&observatories=AAA,BEL,CKI,DED,EBR,FCC,GAN'\
        + '&type=best&rate=minute'
    main.geocsvHandler.validate(target_url, g_verbose)

def run_test_suites(verbose):
  global g_verbose
  g_verbose = verbose

  print ("**** run_test_suites context name: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(ExternalURLTests("test1"))
  suite.addTest(ExternalURLTests("test2"))

  runner = unittest.TextTestRunner()
  runner.run(suite)


