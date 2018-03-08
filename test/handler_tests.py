#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *


import os
import sys
# setup to treat this folder as a peer to validator folder
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

import unittest
import validator.GeocsvValidator

g_argv_list = False

class GeoCSVTests(unittest.TestCase):
  def setUp(self):
    # Note: this breaks if these files are relocated
    self.rsrc_path = os.path.dirname(os.path.realpath(__file__))\
         + '/resources/'
    self.rsrc_URL_path = 'file://' + self.rsrc_path

    #rootDir     = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
##    self.t1 = GeoCSVTests(self)
##  def tearDown(self):
##    self.t1.dispose()
##    self.t1 = None

  def do_geocsv_run(self, expected_outcome, target_url, byte_str):
    pctl = validator.GeocsvValidator.default_program_control()
    pctl['input_resrc'] = target_url
    pctl['input_bytes'] = byte_str
    pctl['verbose'] = False
    pctl['octothorp'] = False  # explicitly list any line with # and respective metrics
    pctl['unicode'] = False  # show lines where unicode is detected and respective metrics
    pctl['null_fields'] = False  # show lines if any field is null and respective metrics
    pctl['write_report'] = False  # report is not written when false (i.e. keeps unit test report small)

    if pctl['write_report']:
      print()
      print("****** expected outcome: ", expected_outcome)
      print("****** target_url: ", target_url)
      print("****** byte_str: ", byte_str)
      print("****** results:")

    geocsvObj = validator.GeocsvValidator.GeocsvValidator(sys.stdout)
    report = geocsvObj.doReport(pctl)
    if report['GeoCSV_validated'] == expected_outcome:
      pass
    else:
      self.fail(report)

  # ******* tests

  def testm4(self):
    IRIS_sample2_bytes = \
b'''
# dataset: GeoCSV 2.0
# delimiter: |
# field_unit: ASCII | ASCII | degrees_north | degrees_east | meters| ASCII| UTC| UTC
# field_type: string | string | float | float | float | string | datetime | datetime
Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime
IU|ANMO|34.9459|-106.4572|1850.0|Albuquerque, New Mexico, USA|1989-08-29T00:00:00|1995-07-14T00:00:00
IU|ANMO|34.9459|-106.4572|1850.0|Albuquerque, New Mexico, USA|1995-07-14T00:00:00|2000-10-19T16:00:00
'''
    self.do_geocsv_run(True, None, IRIS_sample2_bytes)

  def testm3(self):
    IRIS_sample1_bytes = \
b'''
# dataset: GeoCSV 2.0
# delimiter: |
# field_unit: ASCII | ASCII | degrees_north | degrees_east | meters| UTC| UTC
# field_type: string | string | float | float | float | string | datetime | datetime
Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime
IU|ANMO|34.9459|-106.4572|1850.0|Albuquerque, New Mexico, USA|1989-08-29T00:00:00|1995-07-14T00:00:00
IU|ANMO|34.9459|-106.4572|1850.0|Albuquerque, New Mexico, USA|1995-07-14T00:00:00|2000-10-19T16:00:00
'''
    self.do_geocsv_run(False, None, IRIS_sample1_bytes)

  def testm2(self):
    self.do_geocsv_run(False, None, None)

  def testm1(self):
    self.do_geocsv_run(False, 'http://www.google.com/xyzcba', None)

  def test00(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'bad_url.geocsv', None)

  # test URLs are from live services, i.e. subject to failure if service
  # is unavailable
  def test01(self):
    # deactivate external dependency
    ##self.do_geocsv_run(True,
    ##    'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
    ##    + 'query?format=text&showNumberFormatExceptions=true', None)
    self.do_geocsv_run(True, self.rsrc_URL_path + 'wovodat_sample1.geocsv', None)

  def test02(self):
    # deactivate external dependency
    ##self.do_geocsv_run(True,
    ##    'http://geows.ds.iris.edu/geows-uf/intermagnet/1/'\
    ##    + 'query?email=geows@iris.washington.edu&accept=true&content=files'\
    ##    + '&format=text&starttime=2014-10-30&endtime=2014-11-01'\
    ##    + '&regions=America,Asia,Europe,Pacific,Africa'\
    ##    + '&latitudes=NH,NM,E,SM,SH&observatories=AAA,BEL,CKI,DED,EBR,FCC,GAN'\
    ##    + '&type=best&rate=minute', None)
    self.do_geocsv_run(True, self.rsrc_URL_path + 'Intermagnet_sample1.geocsv', None)

  # test URLs are from files in test folder
  def test03(self):
    self.do_geocsv_run(True, self.rsrc_URL_path + 'wovodat_sample1.geocsv', None)
  def test04(self):
    self.do_geocsv_run(True, self.rsrc_URL_path + 'wovodat_sample2.geocsv', None)
  def test05(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'wovodat_sample3.geocsv', None)
  def test06(self):
    self.do_geocsv_run(True, self.rsrc_URL_path + 'wovodat_sample4.geocsv', None)
  def test07(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'R2R_sample1.geocsv', None)
  def test08(self):
    self.do_geocsv_run(True, self.rsrc_URL_path + 'UNAVCO_sample1.geocsv', None)
  def test09(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'null_sample1.geocsv', None)
  def test10(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'IRIS_sample1.geocsv', None)
  def test11(self):
    self.do_geocsv_run(True, self.rsrc_URL_path + 'IRIS_sample2.geocsv', None)
  def test12(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'UNAVCO_sample2.geocsv', None)
  def test13(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'UNAVCO_sample3.geocsv', None)
  def test14(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'IRIS_sample3.geocsv', None)
  def test15(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'IRIS_station1.geocsv', None)
  def test16(self):
    self.do_geocsv_run(False, self.rsrc_URL_path + 'IRIS_sample4.geocsv', None)
  def test17(self):
    # stream multiple files together
    multiple_sets = b''
    with open(self.rsrc_path + 'IRIS_sample1.geocsv', "rb") as geocsv_file:
      multiple_sets += geocsv_file.read()
      multiple_sets += "\n".encode('utf-8')
    with open(self.rsrc_path + 'UNAVCO_sample1.geocsv', "rb") as geocsv_file:
      multiple_sets += geocsv_file.read()
      multiple_sets += "\n".encode('utf-8')
    with open(self.rsrc_path + 'wovodat_sample1.geocsv', "rb") as geocsv_file:
      multiple_sets += geocsv_file.read()

    # setting expected_outcome to expected value for last file set only,
    # at this time, there is no concept of pass/fail for multiple sets
    self.do_geocsv_run(True, None, multiple_sets)

def run_test_suites(argv_list):
  global g_argv_list
  g_argv_list = argv_list

  print("**** ----------------------------------------------")
  print ("**** run_test_suites, context: ", __name__)

  suite = unittest.TestSuite()
  suite.addTest(GeoCSVTests("testm4"))
  suite.addTest(GeoCSVTests("testm3"))
  suite.addTest(GeoCSVTests("testm2"))
  suite.addTest(GeoCSVTests("testm1"))
  suite.addTest(GeoCSVTests("test00"))
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
  suite.addTest(GeoCSVTests("test17"))

  runner = unittest.TextTestRunner()
  runner.run(suite)

def run_one_test(argv_list, test_name):
  global g_argv_list
  g_argv_list = argv_list

  print("**** ----------------------------------------------")
  print("**** run_one_test, context: ", __name__, "  test_name: ", test_name)

  runner = unittest.TextTestRunner()
  runner.run(GeoCSVTests(test_name))
