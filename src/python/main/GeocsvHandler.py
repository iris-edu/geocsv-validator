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

  def __init__(self):
    pass

  def get_response(self, pctl):
    try:
      if pctl['verbose']: print("******* opening input_url: " + pctl['input_url'])
      response = urlopen(pctl['input_url'])
    except HTTPError as e:
      print(e.code)
      print(e.read())
      print("******* failed on target: ", URL)
      sys.exit()

    if pctl['verbose']: print("******* waiting for reply ...")
    return response

  def read_geocsv_lines(self, url_iter, gecsv, metrcs, pctl):
    try:
      rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
      metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1
      rowStr = self.force_to_ASCII(rowStr, metrcs, pctl)

      if len(rowStr) <= 0:
        # ignore zero length line
        metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

        # keep reading, note: potential for stack overflow if many null lines
        rowStr = self.read_geocsv_lines(url_iter, gecsv, metrcs, pctl)

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
        rowStr = self.read_geocsv_lines(url_iter, gecsv, metrcs, pctl)
      # if no octothorp, return out of the recursion and process rowStr
    except StopIteration:
      raise StopIteration

    return rowStr

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
          if pctl['verbose']: print("--unicode-- ", rowStr)
          metrcs['unicodeLineCnt'] = metrcs['unicodeLineCnt'] + 1
          rowASCII = rowStr.encode('ascii', 'replace').decode('ascii')
    except UnicodeEncodeError:
      if pctl['verbose']: print("--unicode-- ", rowStr)
      metrcs['unicodeLineCnt'] = metrcs['unicodeLineCnt'] + 1
      rowASCII = rowStr.encode('ascii', 'replace')

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
        if (metrcs['rowCnt'] == 1):
          print("******* row by row metrics")
          print(metrcs.keys())
          print(metrcs.values(), " row:", row)
        else:
          print(metrcs.values(), " row:", row)

      for itm in row:
        # a length of zero for a cell item is used as the definition of null
        # csv.reader evendently converts input fields to strings
        if len(itm) <= 0:
          metrcs['nullFieldCnt'] = metrcs['nullFieldCnt'] + 1

      if len(row) <= 0:
        # not sure this can ever happen
        eStr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
            + "  input rowStr: " + rowStr
        raise Exception(eStr)

  def report_octothorp(self, pctl, metrcs, rowStr):
    if pctl['octothorp']:
      print("octothorp line: ", metrcs.values(), "  row: ", rowStr.rstrip())

  def validate(self, pctl):
    # adjustments for readability in test_mode
    if pctl['new_line']:
      print()
    if pctl['octothorp'] or pctl['verbose']:
      print("******* starting validate...")

    # geocsv object
    gecsv = {'geocsv_start_found': False, 'delimiter': ',', 'other_keywords': {}}

    response = self.get_response(pctl)

    gecsv['url_string'] = pctl['input_url']

    # capture metrics about content
    # metrcs - metrics about data content
    # octothorp - technical name for hash symbol
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

    url_iter = response.readlines().__iter__()
    looping = True
    while looping:
      try:
        rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
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

              rowStr = self.read_geocsv_lines(url_iter, gecsv, metrcs, pctl)
              if pctl['verbose']:
                print("******* geocsv header finished, GeoCSV parameters: ", gecsv)
                print("******* geocsv header finished, metrics keys: ", metrcs.keys())
                print("******* geocsv header finished, metric values: ", metrcs.values())

              # handle first non-geocsv line after finished reading geocsv lines
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
        if pctl['verbose']: print("******* geocsvHandler finished *******")
        looping = False
      finally:
        response.close()

    report = self.check_geocsv_fields(metrcs, gecsv)

    if not pctl['test_mode']:
      rstr = self.createReportStr(report)
      sys.stdout.write(rstr)

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
        rstr += "-- " + str(itm) + ": " + str(report[itm]) + "\n"
    return rstr

  def check_geocsv_fields(self, metrcs, gecsv):
    report = collections.OrderedDict()
    report['GeoCSV_validated'] = True
    report['url_string'] = gecsv['url_string']
    report['metrics'] = metrcs

    # check for start
    if (not gecsv['geocsv_start_found']):
      report['GeoCSV_validated'] = False
      report['no_geocsv_start'] = 'WARNING, start of GeoCSV not found,' + \
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
      report['geocsv_field_size_error'] = 'ERROR, geocsv inconsistent field sizes'
      showGeoCSVFldsDict = True

    # check for consistent data field values
    if len(metrcs['dataFieldsCntSet']) > 1:
      report['GeoCSV_validated'] = False
      report['data_field_size_error'] = 'ERROR, more than one size for data' + \
          'rows, row sizes: ' + str(metrcs['dataFieldsCntSet'])

    # check for consistent field sizes between data and geocsv field parameters
    if len(metrcs['dataFieldsCntSet'].union(gecsvFieldCntSet)) >\
        max(len(metrcs['dataFieldsCntSet']), len(gecsvFieldCntSet)):
      report['GeoCSV_validated'] = False
      report['geocsv_to_data_field_size_error'] = 'ERROR, row size inconsistent' + \
          'with geocsv field size, data row sizes: ' + str(metrcs['dataFieldsCntSet']) + \
          '  geocsv field sizes: ' + str(gecsvFieldCntSet)
      showGeoCSVFldsDict = True

    # check for field size of one, implying missing or wrong delimiter
    if 1 in metrcs['dataFieldsCntSet'] or 1 in gecsvFieldCntSet:
      report['GeoCSV_validated'] = False
      report['field_size_1_warning'] = 'WARNING, geocsv field size or data' + \
          'row size of one, possible problem with delimiter, data row sizes: ' + \
          str(metrcs['dataFieldsCntSet']) + '  geocsv field sizes: ' + \
          str(gecsvFieldCntSet)
      showGeoCSVFldsDict = True

    # check for null data field values
    if metrcs['nullFieldCnt'] > 0:
      report['GeoCSV_validated'] = False
      report['data_field_null_warning'] = 'WARNING, at least one data field' + \
          'was zero length (i.e. null), null count: ' + str(metrcs['nullFieldCnt'])

    # if any errors or warning are related to the field parameters in the
    # geocsv header, show the specific parameters for this file
    if showGeoCSVFldsDict:
      report['geocsv_fields'] = thisFldDict

    return report

def default_program_control():
  pctl = {}
  pctl['input_url'] = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
      + 'query?format=text&showNumberFormatExceptions=true'
  pctl['verbose'] = True
  pctl['new_line'] = True  # one blank line before report - primarily for test runs
  pctl['octothorp'] = True  # explicitly list any line with # and respective metrics
  pctl['test_mode'] = False  # turns off report when true (i.e. keeps unit test report small)

  return pctl

def parse_cmd_lines():
  parser = argparse.ArgumentParser(description=\
    'Read text file of json objects, one per line, do statistics on key_of_number')
  # note, if having trouble reading negative shift, put quotes and a space in front e.g.  -1.0:9.5367431640625e-07"
  parser.add_argument("--input_file_name", \
    help='file name, expecting JSON object per line', \
    type=str, required=True, default='nameRequired')
  args = parser.parse_args()
  print("************** type args: ", type(args))
  print("geocsvHandler args: ", args)

  return default_program_control()

if __name__ == "__main__" \
    or __name__ == "GeocsvValidate" \
    or __name__ == "src.python.main.GeocsvValidate":

  print("geocsvHandler argv: ", sys.argv)

  default_url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/'\
      + 'query?format=text&showNumberFormatExceptions=true'
  url_string = ''
  for item in sys.argv:
    if item.find('http://') >= 0\
        or item.find('file://') >= 0:
      url_string = item
      break

  if len(url_string) <= 0:
    print('******* warning, there is no http:// or file:// reference on the'
        + ' command line list,')
    print("******* using default url: ", default_url_string)
    url_string = default_url_string

  print("************** type argv: ", type(sys.argv))

  pctl = parse_cmd_lines()

  geocsvObj = GeocsvHandler()
  geocsvObj.validate(pctl)

