#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *


import os
import unittest
import main.GeocsvHandler

g_argv_list = False

class GeoCSVTests(unittest.TestCase):
  def setUp(self):
    # Note: this breaks if these files are relocated
    self.file_path = 'file://' +\
        os.path.dirname(os.path.realpath(__file__))\
         + '/resources/'
##    self.t1 = GeoCSVTests(self)
##  def tearDown(self):
##    self.t1.dispose()
##    self.t1 = None

  def doValidate(self, target_url):
    pctl = main.GeocsvHandler.default_program_control()
    pctl['input_url'] = target_url
    pctl['verbose'] = False
    pctl['new_line'] = False  # one blank line before report - primarily for test runs
    pctl['octothorp'] = False  # explicitly list any line with # and respective metrics
    pctl['test_mode'] = True  # turns off report when true (i.e. keeps unit test report small)

    # everything printing out
    pctl['verbose'] = True
    pctl['new_line'] = True  # one blank line before report - primarily for test runs
    pctl['octothorp'] = True  # explicitly list any line with # and respective metrics
    pctl['test_mode'] = False  # turns off report when true (i.e. keeps unit test report small)
    geocsvObj = main.GeocsvHandler.GeocsvHandler()
    return geocsvObj.validate(pctl)

  def goodIfTrue(self, target_url):
    report = self.doValidate(target_url)
    if report['GeoCSV_validated'] == False:
      self.fail(report)

  def goodIfFalse(self, target_url):
    report = self.doValidate(target_url)
    if report['GeoCSV_validated'] == True:
      self.fail(report)

  # test URLs are from live services, i.e. subject to failure if service
  # is unavailable
  def test01(self):
    GeoCSVTests.goodIfTrue(self,
        'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
        + 'query?format=text&showNumberFormatExceptions=true')

  def test02(self):
    GeoCSVTests.goodIfTrue(self,
        'http://geows.ds.iris.edu/geows-uf/intermagnet/1/'\
        + 'query?email=geows@iris.washington.edu&accept=true&content=files'\
        + '&format=text&starttime=2014-10-30&endtime=2014-11-01'\
        + '&regions=America,Asia,Europe,Pacific,Africa'\
        + '&latitudes=NH,NM,E,SM,SH&observatories=AAA,BEL,CKI,DED,EBR,FCC,GAN'\
        + '&type=best&rate=minute')

  # test URLs are from files in test folder
  def test03(self):
    GeoCSVTests.goodIfTrue(self, self.file_path + 'wovodat_sample1.geocsv')
  def test04(self):
    GeoCSVTests.goodIfTrue(self, self.file_path + 'wovodat_sample2.geocsv')
  def test05(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'wovodat_sample3.geocsv')
  def test06(self):
    GeoCSVTests.goodIfTrue(self, self.file_path + 'wovodat_sample4.geocsv')
  def test07(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'R2R_sample1.geocsv')
  def test08(self):
    GeoCSVTests.goodIfTrue(self, self.file_path + 'UNAVCO_sample1.geocsv')
  def test09(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'null_sample1.geocsv')
  def test10(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'IRIS_sample1.geocsv')
  def test11(self):
    GeoCSVTests.goodIfTrue(self, self.file_path + 'IRIS_sample2.geocsv')
  def test12(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'UNAVCO_sample2.geocsv')
  def test13(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'UNAVCO_sample3.geocsv')
  def test14(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'IRIS_sample3.geocsv')
  def test15(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'IRIS_station1.geocsv')
  def test16(self):
    GeoCSVTests.goodIfFalse(self, self.file_path + 'IRIS_sample4.geocsv')

def run_test_suites(argv_list):
  global g_argv_list
  g_argv_list = argv_list

  print ("**** run_test_suites context name: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(GeoCSVTests("test02"))
  suite.addTest(GeoCSVTests("test01"))
  suite.addTest(GeoCSVTests("test03"))
  suite.addTest(GeoCSVTests("test04"))
  suite.addTest(GeoCSVTests("test05"))
  suite.addTest(GeoCSVTests("test06"))
  suite.addTest(GeoCSVTests("test07"))
  suite.addTest(GeoCSVTests("test08"))
  suite.addTest(GeoCSVTests("test09"))
  suite.addTest(GeoCSVTests("test10"))
  suite.addTest(GeoCSVTests("test11"))
  suite.addTest(GeoCSVTests("test12"))
  suite.addTest(GeoCSVTests("test13"))
  suite.addTest(GeoCSVTests("test14"))
  suite.addTest(GeoCSVTests("test15"))
  suite.addTest(GeoCSVTests("test16"))

  runner = unittest.TextTestRunner()
  runner.run(suite)

def run_one_test(argv_list, test_name):
  global g_argv_list
  g_argv_list = argv_list

  print ("**** run_one_test context name: ", __name__)

  runner = unittest.TextTestRunner()
  runner.run(GeoCSVTests(test_name))
