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


import os
import unittest
import main.geocsvHandler

g_argv_list = False

class ExternalURLTests(unittest.TestCase):
  def setUp(self):
    # Note: this breaks if these files are relocated
    self.resource_path = os.path.dirname(os.path.realpath(__file__))\
         + '/resources'
##    self.t1 = ExternalURLTests(self)
##  def tearDown(self):
##    self.t1.dispose()
##    self.t1 = None

  # some live URLs
  def test1(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
        + 'query?format=text&showNumberFormatExceptions=true'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test2(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/intermagnet/1/'\
        + 'query?email=geows@iris.washington.edu&accept=true&content=files'\
        + '&format=text&starttime=2014-10-30&endtime=2014-11-01'\
        + '&regions=America,Asia,Europe,Pacific,Africa'\
        + '&latitudes=NH,NM,E,SM,SH&observatories=AAA,BEL,CKI,DED,EBR,FCC,GAN'\
        + '&type=best&rate=minute'
    main.geocsvHandler.validate(target_url, g_argv_list)

  # files from test area
  def test3(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test4(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample2.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test5(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample3.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test6(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample4.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test7(self):
    target_url = 'file://' + self.resource_path + '/' + 'R2R_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test8(self):
    target_url = 'file://' + self.resource_path + '/' + 'UNAVCO_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test9(self):
    target_url = 'file://' + self.resource_path + '/' + 'null_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)

def run_test_suites(argv_list):
  global g_argv_list
  g_argv_list = argv_list

  print ("**** run_test_suites context name: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(ExternalURLTests("test2"))
  suite.addTest(ExternalURLTests("test1"))
  suite.addTest(ExternalURLTests("test3"))
  suite.addTest(ExternalURLTests("test4"))
  suite.addTest(ExternalURLTests("test5"))
  suite.addTest(ExternalURLTests("test6"))
  suite.addTest(ExternalURLTests("test7"))
  suite.addTest(ExternalURLTests("test8"))
  suite.addTest(ExternalURLTests("test9"))

  runner = unittest.TextTestRunner()
  runner.run(suite)

