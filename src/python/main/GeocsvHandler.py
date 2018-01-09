#!/usr/bin/env python

# enable code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *

# for urllib2 compatability
## replacing this --> import urllib2
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import sys
import csv
import re
import pprint
import datetime
import pytz
import argparse
import collections
import io

MY_LINE_BREAK_CHARS = '\n\r'

# definition for keyword
# for regex '^# *(.+?):' select first non greedy character group starting
#   at the beginning of a line that starts with an octothorp (i.e. '#') that may
#   have 0 or more spaces and at least 1 character ending with colon
KEYWORD_REGEX = '^# *(.+?):'

GEOCSV_REQUIRED_START_REGEX = '^# *dataset *: *GeoCSV 2.0'
GEOCSV_REQUIRED_START_LITERAL = '# dataset: GeoCSV 2.0'

GEOCSV_COLUMN_VALUED_KEYWORDS = {'field_unit', 'field_type',
   'field_long_name', 'field_standard_name', 'field_missing'}

GEOCSV_WELL_KNOWN_KEYWORDS = {'dataset', 'delimiter', 'attribution',
    'standard_name_cv', 'title', 'history', 'institution', 'source',
    'comment', 'references'}.union(GEOCSV_COLUMN_VALUED_KEYWORDS)

class GeocsvHandler(object):

  # stdwriter - an object with a write method, expecting, expecting
  #             something like sys.stdout or tornado.web.RequestHandler
  def __init__(self, stdwriter):
    self.stdwriter = stdwriter

  def get_url_iterator(self, pctl):
    result_for_get =  {'data_iter': None, 'except_report': None}
    if pctl['input_url'] == None:
      metrcs = self.createMetricsObj()
      gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])
      report = self.check_geocsv_fields(metrcs, gecsv)
      report['ERROR_get_url_iterator_None'] = \
          'None was entered for control parameter: input_url'
      result_for_get['except_report'] = report
      return result_for_get

    try:
      if pctl['verbose']:
        self.stdwriter.write("------- GeoCSV_Validate - opening input_url: " + \
            pctl['input_url'] + "\n")
      response = urlopen(pctl['input_url'])
      result_for_get['data_iter'] = response.readlines().__iter__()
    except HTTPError as e:
      metrcs = self.createMetricsObj()
      gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])
      report = self.check_geocsv_fields(metrcs, gecsv)
      report['HTTPError_HTTPcode'] = str(e.code)
      report['HTTPError_Exception'] = str(e)
      result_for_get['except_report'] = report
      return result_for_get
    except Exception as e:
      metrcs = self.createMetricsObj()
      gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])
      report = self.check_geocsv_fields(metrcs, gecsv)
      report['ERROR_Exception'] = str(e)
      result_for_get['except_report'] = report
      return result_for_get

    if pctl['verbose']:
      self.stdwriter.write("------- GeoCSV_Validate - received reply, created data iterator,  " + \
          "datetime: " + str(datetime.datetime.now(pytz.utc).isoformat()) + "\n")
    return result_for_get

  def get_bytes_iterator(self, pctl):
    result_for_get =  {'data_iter': None, 'except_report': None}
    if pctl['input_bytes'] == None:
      metrcs = self.createMetricsObj()
      gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])
      report = self.check_geocsv_fields(metrcs, gecsv)
      report['ERROR_get_bytes_iterator_None'] = \
          'None was entered for control parameter: input_bytes'
      result_for_get['except_report'] = report
      return result_for_get

    try:
      if pctl['verbose']:
        self.stdwriter.write("------- GeoCSV_Validate - setup input_bytes: " + \
            str(pctl['input_bytes']) + "\n")
      bytes_obj = io.BytesIO(pctl['input_bytes'])
      result_for_get['data_iter'] = bytes_obj.readlines().__iter__()
    except Exception as e:
      metrcs = self.createMetricsObj()
      gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])
      report = self.check_geocsv_fields(metrcs, gecsv)
      report['ERROR_Exception'] = str(e)
      result_for_get['except_report'] = report
      return result_for_get

    if pctl['verbose']:
      self.stdwriter.write("------- GeoCSV_Validate - read bytes iterator created,  datetime: " + \
          str(datetime.datetime.now(pytz.utc).isoformat()) + "\n")
    return result_for_get

  def read_geocsv_lines(self, data_iter, gecsv, metrcs, pctl):
    try:
      rowStr = next(data_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
      metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1
      rowStr = self.force_to_ASCII(rowStr, metrcs, pctl)

      if len(rowStr) <= 0:
        # ignore zero length line
        metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

        # keep reading, note: potential for stack overflow if many null lines
        rowStr = self.read_geocsv_lines(data_iter, gecsv, metrcs, pctl)

      if rowStr[0:1] == '#':
        # count any octothorp line as geocsv line until exiting at first non-octothorp
        metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

        # do geocsv processing
        mObj = re.match(KEYWORD_REGEX, rowStr)
        if mObj == None:
          # no geocsv keyword form, count and ignore
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          self.report_octothorp(pctl, metrcs, rowStr)
        else:
          keyword = mObj.group(1).strip()
          if len(keyword) <= 0:
            # poorly formed keyword, probably something like #:, or # :
            # count and ignore
            metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
            self.report_octothorp(pctl, metrcs, rowStr)

          value = rowStr[len(mObj.group(0)):].strip()

          if sys.version_info[0] < 3:
            # in python 2, csv module requires a string in input parameters
            # e.g. delimiter, the matcher object returns unicode, so the
            # keyword and value returned from matcher are forced to ASCII
            keyword = keyword.encode('ascii')
            value = value.encode('ascii')

          if keyword in GEOCSV_WELL_KNOWN_KEYWORDS:
            gecsv[keyword] = value
          else:
            gecsv['other_keywords'][keyword] = value

        # keep reading as long as octothorp found
        rowStr = self.read_geocsv_lines(data_iter, gecsv, metrcs, pctl)
      # if no octothorp, return out of the recursion and process rowStr
    except StopIteration:
      raise StopIteration

    return rowStr

  # detect unicode and force to ASCII
  def handle_unicode(self, rowStr, metrcs, pctl):
    metrcs['unicodeLineCnt'] = metrcs['unicodeLineCnt'] + 1
    if pctl['verbose'] or pctl['unicode']:
      self.stdwriter.write("--unicode-- " +  str(list(metrcs.values())) + \
          "  line: " +  str(rowStr.rstrip()) + "\n")
    rowASCII = rowStr.encode('ascii', 'replace').decode('ascii')
    return rowASCII

  # detect unicode and force to ASCII
  def force_to_ASCII(self, rowStr, metrcs, pctl):
    try:
      if sys.version_info[0] < 3:
        rowASCII = rowStr.decode('utf-8')
      else:
        try:
          str(rowStr.encode('ascii'))
          rowASCII = rowStr
        except UnicodeEncodeError:
          rowASCII = self.handle_unicode(rowStr, metrcs, pctl)
    except UnicodeEncodeError:
      rowASCII = self.handle_unicode(rowStr, metrcs, pctl)

    return rowASCII

  def handle_csv_row(self, rowStr, delimiter, metrcs, pctl):
    # csv module interface is not setup to stream one line at a time,
    # so make a list of 1 row
    # also, python 2 csv does not handle unicode values, so force to ASCII
    rowASCII = self.force_to_ASCII(rowStr, metrcs, pctl)
    rowiter = iter(list([rowASCII]))
    csvreadr = csv.reader(rowiter, delimiter = delimiter)
    for row in csvreadr:
      metrcs['rowCnt'] = metrcs['rowCnt'] + 1
      metrcs['dataFieldsCntSet'].add(len(row))
      if pctl['verbose']:
##        if (metrcs['rowCnt'] == 1):
##          print("------- GeoCSV_Validate - row by row metrics, metric fields: ", list(metrcs.keys()))
        self.stdwriter.write(str(list(metrcs.values())) + " line:" + \
            str(row) + "\n")

      anyNulls = False
      for itm in row:
        # a length of zero for a cell item is used as the definition of null
        # csv.reader evedently converts input fields to strings
        if len(itm) <= 0:
          metrcs['nullFieldCnt'] = metrcs['nullFieldCnt'] + 1
          anyNulls = True
      if anyNulls and pctl['null_fields']:
        self.stdwriter.write("--null_fields-- " + str(list(metrcs.values())) + \
            "  line: " + str(rowStr.rstrip()) + "\n")

      if len(row) <= 0:
        # not sure this can ever happen
        eStr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
            + "  input rowStr: " + rowStr
        raise Exception(eStr)

  def report_octothorp(self, pctl, metrcs, rowStr):
    if pctl['octothorp']:
      self.stdwriter.write("--octothorp-- " + str(list(metrcs.values())) + \
          "  line: " + str(rowStr.rstrip()) + "\n")

  def createMetricsObj(self):
    # capture metrics about content
    # metrcs - metrics about data content
    # octothorp - name for hash symbol
    # gecsv - content related to geocsv header information
    metrcs = collections.OrderedDict()
    metrcs['totalLineCnt'] = 0
    metrcs['rowCnt'] = 0
    metrcs['zeroLenCnt'] = 0
    metrcs['ignoreLineCnt'] = 0
    metrcs['geocsvLineCnt'] = 0
    metrcs['dataFieldsCntSet'] = set()
    metrcs['nullFieldCnt'] = 0
    metrcs['unicodeLineCnt'] = 0

    return metrcs

  def createGeocsvObj(self, input_url, input_bytes):
    gecsv = {'geocsv_start_found': False, 'input_url': input_url, \
        'delimiter': ',', 'other_keywords': {}}
    # don't put the raw bytes in this structure
    if input_bytes == None:
      gecsv['input_bytes_len'] = None
    else:
      gecsv['input_bytes_len'] = len(input_bytes)
    return gecsv

  def validate(self, pctl):
    metrcs = self.createMetricsObj()

    if pctl['verbose'] or pctl['octothorp'] or pctl['unicode'] or pctl['null_fields']:
      self.stdwriter.write("\n")
      self.stdwriter.write(
          "------- GeoCSV_Validate - starting validate  datetime: " + \
          str(datetime.datetime.now(pytz.utc).isoformat()) + "\n")

    if pctl['input_url']:
      result_for_get = self.get_url_iterator(pctl)
    else:
      result_for_get = self.get_bytes_iterator(pctl)

    if result_for_get['except_report'] == None:
      # no error report, continue
      data_iter = result_for_get['data_iter']
    else:
      # return error report
      return result_for_get['except_report']

    gecsv = self.createGeocsvObj(pctl['input_url'], pctl['input_bytes'])

    if pctl['verbose'] or pctl['octothorp'] or pctl['unicode'] or pctl['null_fields']:
      # note: creating a list here to get py 2.x and 3.x to have simple lsit
      self.stdwriter.write("------- GeoCSV_Validate - metric fields: " + \
          str(list(metrcs.keys())) + "\n")

    looping = True
    while looping:
      try:
        rowStr = next(data_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
        metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1

        if len(rowStr) <= 0:
          # ignore zero length line
          metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1
          continue

        if rowStr[0:1] == '#':
          # ignore octothorp lines until start of geocsv, then read
          # until first non-octothorp line
          if gecsv['geocsv_start_found'] == False:
            mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
            if mObj == None:
              if gecsv['geocsv_start_found'] == False:
                metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
                self.report_octothorp(pctl, metrcs, rowStr)

            else:
              gecsv['geocsv_start_found'] = True
              metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

              rowStr = self.read_geocsv_lines(data_iter, gecsv, metrcs, pctl)
              if pctl['verbose']:
                self.stdwriter.write(
                    "------- GeoCSV_Validate - parsed header and status parameters: " + \
                    str(gecsv) + "\n")
                self.stdwriter.write(
                    "------- GeoCSV_Validate - after header read metrics: " + \
                    str(list(metrcs.values())) + "\n")

              # handle first non-geocsv line after finished reading geocsv header lines
              self.handle_csv_row(rowStr, gecsv['delimiter'], metrcs, pctl)
          else:
            # ignore octothorp lines after reading geocsv lines
            metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
            self.report_octothorp(pctl, metrcs, rowStr)
            continue
        else:
          # handle most non-geocsv for generic comment lines
          self.handle_csv_row(rowStr, gecsv['delimiter'], metrcs, pctl)
      except StopIteration:
        if pctl['verbose'] or pctl['octothorp'] or pctl['unicode'] or pctl['null_fields']:
          self.stdwriter.write(
              "------- GeoCSV_Validate - finished validate, datetime: " + \
              str(datetime.datetime.now(pytz.utc).isoformat()) + "\n")
        looping = False
      finally:
        ##response.close()
        pass

    report = self.check_geocsv_fields(metrcs, gecsv)
    return report

  def createReportStr(self, report):
    rstr = "-- GeoCSV_Validate_Report  datetime: " + \
        str(datetime.datetime.now(pytz.utc).isoformat()) + "\n"
    for itm in report:
      if isinstance(report[itm], dict) and itm == 'geocsv_fields':
        rstr += "-- " + str(itm) + ": " + "\n"
        if len(report[itm]) > 0:
          for it2 in report[itm]:
            rstr += "---- " + str(it2) + ": " + str(report[itm][it2]) + "\n"
        else:
            rstr += "---- no geocsv fields_* keywords detected" + "\n"
      else:
        if itm == 'metrics':
          # trickery to make OrderedDict look the same between 2.x and 3.x
          rstr += "-- " + str(itm) + ": " + str(list(report[itm].items())) + "\n"
        else:
          rstr += "-- " + str(itm) + ": " + str(report[itm]) + "\n"
    return rstr

  def doReport(self, pctl):
    report = self.validate(pctl)
    if pctl['write_report']:
      # allows for not printing report, so unit tests can be very succinct
      rstr = self.createReportStr(report)
      self.stdwriter.write(rstr)
    return report

  def check_geocsv_fields(self, metrcs, gecsv):
    report = collections.OrderedDict()
    report['GeoCSV_validated'] = True
    report['input_url'] = gecsv['input_url']
    report['input_bytes_len'] = gecsv['input_bytes_len']
    report['metrics'] = metrcs

    # check for start
    if (not gecsv['geocsv_start_found']):
      report['GeoCSV_validated'] = False
      report['WARNING_no_geocsv_start'] = 'WARNING, start of GeoCSV not found,' + \
          ' expecting this line: ' + str(GEOCSV_REQUIRED_START_LITERAL)

    # check for consistent geocsv field parameter values
    thisFldDict = {}
    showGeoCSVFldsDict = False
    gecsvFieldCntSet = set()
    fldSet = GEOCSV_COLUMN_VALUED_KEYWORDS.intersection(set(gecsv.keys()))
    for fldname in fldSet:
      rowiter = iter(list([gecsv[fldname]]))
      csvreadr = csv.reader(rowiter, delimiter = gecsv['delimiter'])
      for row in csvreadr:
        thisFldDict[fldname] = gecsv[fldname]
        thisFldDict[fldname + "_len"] = len(row)
        gecsvFieldCntSet.add(len(row))

    if len(gecsvFieldCntSet) > 1:
      report['GeoCSV_validated'] = False
      report['ERROR_geocsv_field_size'] = 'Inconsistent geocsv field sizes'
      showGeoCSVFldsDict = True

    # check for consistent data field values
    if len(metrcs['dataFieldsCntSet']) > 1:
      report['GeoCSV_validated'] = False
      report['ERROR_data_field_size'] = 'There is more than one size for data ' + \
          'rows, row sizes: ' + str(metrcs['dataFieldsCntSet'])

    # check for consistent field sizes between data and geocsv field parameters
    if len(metrcs['dataFieldsCntSet'].union(gecsvFieldCntSet)) >\
        max(len(metrcs['dataFieldsCntSet']), len(gecsvFieldCntSet)):
      report['GeoCSV_validated'] = False
      report['ERROR_ geocsv_to_data_field_size'] = 'A row size is inconsistent ' + \
          'with geocsv field size, data row sizes: ' + str(metrcs['dataFieldsCntSet']) + \
          '  geocsv field sizes: ' + str(gecsvFieldCntSet)
      showGeoCSVFldsDict = True

    # check for field size of one, implying missing or wrong delimiter
    if 1 in metrcs['dataFieldsCntSet'] or 1 in gecsvFieldCntSet:
      report['GeoCSV_validated'] = False
      report['WARNING_field_size_1'] = 'There is a geocsv field or data ' + \
          'row of size one, this may be a delimiter problem, data row sizes: ' + \
          str(metrcs['dataFieldsCntSet']) + '  geocsv field sizes: ' + \
          str(gecsvFieldCntSet)
      showGeoCSVFldsDict = True

    # check for null data field values
    if metrcs['nullFieldCnt'] > 0:
      report['GeoCSV_validated'] = False
      report['WARNING_data_field_null'] = 'At least one data field ' + \
          'was zero length (i.e. null), null count: ' + str(metrcs['nullFieldCnt'])

    # if any errors or warning are related to the field parameters in the
    # geocsv header, show the specific parameters for this file
    if showGeoCSVFldsDict:
      report['geocsv_fields'] = thisFldDict

    return report

def str2bool(v):
  # from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
  if v.lower() in ('yes', 'true', 't', 'y', '1'):
      return True
  elif v.lower() in ('no', 'false', 'f', 'n', '0'):
      return False
  else:
      raise argparse.ArgumentTypeError('String version of Boolean value' + \
        ' expected, value given: ' + str(v))

def default_program_control():
  pctl = {}
##  pctl['input_url'] = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
##      + 'query?format=text&showNumberFormatExceptions=true'
  pctl['input_url'] = None
  # note: if both input_url and input_bytes are set, input_url will be used
  pctl['input_bytes'] = None  # of form b'line1\nline2\n'

  pctl['verbose'] = False
  pctl['octothorp'] = False  # show lines with # and respective metrics
  pctl['unicode'] = False  # show lines where unicode is detected and respective metrics
  pctl['null_fields'] = False  # show lines if any field is null and respective metrics
  pctl['write_report'] = True  # report is not written when False (i.e. keeps unit test report small)

  return pctl

def parse_cmd_lines():
  pctl = default_program_control()

  parser = argparse.ArgumentParser(description=\
      'Read a GeoCSV file and check for conformance against the recommended ' + \
      'standard, see http://geows.ds.iris.edu/documents/GeoCSV.pdf')

  parser.add_argument("--input_name", help='Input a URL, http:// or file://', \
      type=str, required=True, default='nameRequired')
  parser.add_argument('--verbose', \
      help='Show metrics for every data line', type=str2bool, default=False)
  parser.add_argument('--octothorp', \
      help='Show metrics for lines with # after initial start of data lines', \
      type=str2bool, default=False)
  parser.add_argument('--unicode', \
      help='Show metrics for lines with unicode', \
      type=str2bool, default=False)
  parser.add_argument('--null_fields', \
      help='Show metrics for lines if any field is null', \
      type=str2bool, default=False)
  parser.add_argument('--write_report', \
      help='Do not write report lines when false, this may be used to make ' + \
      'a succinct unit test report)', type=str2bool, default=True)

  args = parser.parse_args()

  pctl['input_url'] = args.input_name
  pctl['input_bytes'] = None
  pctl['verbose'] = args.verbose
  pctl['octothorp'] = args.octothorp
  pctl['unicode'] = args.unicode
  pctl['null_fields'] = args.null_fields
  pctl['write_report'] = args.write_report

  return pctl

if __name__ == "__main__" \
    or __name__ == "GeocsvValidate" \
    or __name__ == "src.python.main.GeocsvValidate":

  pctl = parse_cmd_lines()

  geocsvObj = GeocsvHandler(sys.stdout)
  geocsvObj.doReport(pctl)

