#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
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
  def test01(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
        + 'query?format=text&showNumberFormatExceptions=true'
    main.geocsvHandler.validate(target_url, g_argv_list)
    self.fail("pass report back?")
  def test02(self):
    target_url = 'http://geows.ds.iris.edu/geows-uf/intermagnet/1/'\
        + 'query?email=geows@iris.washington.edu&accept=true&content=files'\
        + '&format=text&starttime=2014-10-30&endtime=2014-11-01'\
        + '&regions=America,Asia,Europe,Pacific,Africa'\
        + '&latitudes=NH,NM,E,SM,SH&observatories=AAA,BEL,CKI,DED,EBR,FCC,GAN'\
        + '&type=best&rate=minute'
    main.geocsvHandler.validate(target_url, g_argv_list)

  # files from test area
  def test03(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
    self.assert_(False)
  def test04(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample2.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
    self.fail("pass report back on 4?")
  def test05(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample3.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test06(self):
    target_url = 'file://' + self.resource_path + '/' + 'wovodat_sample4.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test07(self):
    target_url = 'file://' + self.resource_path + '/' + 'R2R_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test08(self):
    target_url = 'file://' + self.resource_path + '/' + 'UNAVCO_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test09(self):
    target_url = 'file://' + self.resource_path + '/' + 'null_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test10(self):
    target_url = 'file://' + self.resource_path + '/' + 'IRIS_sample1.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test11(self):
    target_url = 'file://' + self.resource_path + '/' + 'IRIS_sample2.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test12(self):
    target_url = 'file://' + self.resource_path + '/' + 'UNAVCO_sample2.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)
  def test13(self):
    target_url = 'file://' + self.resource_path + '/' + 'UNAVCO_sample3.geocsv'
    main.geocsvHandler.validate(target_url, g_argv_list)

def run_test_suites(argv_list):
  global g_argv_list
  g_argv_list = argv_list

  print ("**** run_test_suites context name: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(ExternalURLTests("test02"))
  suite.addTest(ExternalURLTests("test01"))
  suite.addTest(ExternalURLTests("test03"))
  suite.addTest(ExternalURLTests("test04"))
  suite.addTest(ExternalURLTests("test05"))
  suite.addTest(ExternalURLTests("test06"))
  suite.addTest(ExternalURLTests("test07"))
  suite.addTest(ExternalURLTests("test08"))
  suite.addTest(ExternalURLTests("test09"))
  suite.addTest(ExternalURLTests("test10"))
  suite.addTest(ExternalURLTests("test11"))
  suite.addTest(ExternalURLTests("test12"))
  suite.addTest(ExternalURLTests("test13"))

  runner = unittest.TextTestRunner()
  runner.run(suite)

