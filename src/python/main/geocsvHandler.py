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

def get_response(url_string, argv_list):
  try:
    if 'verbose' in argv_list: print("******* opening url: " + url_string)
    response = urlopen(url_string)
  except HTTPError as e:
    print(e.code)
    print(e.read())
    print("******* failed on target: ", URL)
    sys.exit()

  if 'verbose' in argv_list: print("******* waiting for reply ...")
  return response

def read_geocsv_lines(url_iter, gecsv, metrcs, argv_list):
  try:
    rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
    metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1

    if len(rowStr) <= 0:
      # ignore zero length line
      metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

      # keep reading, note: potential for stack overflow if many null lines
      rowStr = read_geocsv_lines(url_iter, gecsv, metrcs, argv_list)

    if rowStr[0:1] == '#':
      # count any octothorp line as geocsv line until exiting at first non-octothorp
      metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

      # do geocsv processing
      mObj = re.match(KEYWORD_REGEX, rowStr)
      if mObj == None:
        # no geocsv keyword form, count and ignore
        metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
        report_octothorp(argv_list, metrcs, rowStr)
      else:
        keyword = mObj.group(1).strip()
        if len(keyword) <= 0:
          # poorly formed keyword, probably something like #:, or # :
          # count and ignore
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          report_octothorp(argv_list, metrcs, rowStr)

        value = rowStr[len(mObj.group(0)):].strip()

        if sys.version_info[0] < 3:
          # avoid using unicode strings when running python 2
          keyword = keyword.encode('ascii')
          value = value.encode('ascii')

        if keyword in GEOCSV_WELL_KNOWN_KEYWORDS:
          gecsv[keyword] = value
        else:
          gecsv['other_keywords'][keyword] = value

      # keep reading as long as octothorp found
      rowStr = read_geocsv_lines(url_iter, gecsv, metrcs, argv_list)
    # if no octothorp, return out of the recursion and process rowStr
  except StopIteration:
    raise StopIteration

  return rowStr

def handle_csv_row(rowStr, delimiter, metrcs, argv_list):
  # csv module interface is not setup to stream one line at a time,
  # so make a list of 1 row
  rowiter = iter(list([rowStr]))

  csvreadr = csv.reader(rowiter, delimiter = delimiter)
  for row in csvreadr:
    metrcs['rowCnt'] = metrcs['rowCnt'] + 1
    metrcs['dataFieldsCntSet'].add(len(row))
    if 'verbose' in argv_list: print(metrcs, "  row: ", row)

    if len(row) <= 0 :
      # not sure this can ever happen
      eStr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
          + "  input rowStr: " + rowStr
      raise Exception(eStr)

def report_octothorp(argv_list, metrcs, rowStr):
  if 'octothorp' in argv_list:
    print("octothorp ", metrcs, "  rowStr: ", rowStr.rstrip())

def validate(url_string, argv_list):
  # put newline to improve readability for unit test when not in test mode
  if not 'test_mode' in argv_list: print()

  # geocsv object
  gecsv = {'GCStart': False, 'delimiter': ',', 'other_keywords': {}}

  response = get_response(url_string, argv_list)

  gecsv['url_string'] = url_string

  # capture metrics about content
  # metrcs - metrics about file and data content
  # octothorp - technical name for hash symbol
  # gecsv - content related to geocsv
  metrcs = {'totalLineCnt': 0, 'rowCnt': 0, 'zeroLenCnt': 0,
    'ignoreLineCnt': 0, 'geocsvLineCnt': 0, 'dataFieldsCntSet': set()}

  url_iter = response.readlines().__iter__()
  looping = True
  while looping:
    try:
      rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
      metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1

      if len(rowStr) <= 0 :
        # ignore zero length line
        metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1
        continue

      if rowStr[0:1] == '#':
        # ignore octothorp lines until start of geocsv, then read
        # until first non-octothorp line
        if gecsv['GCStart'] == False:
          mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
          if mObj == None:
            if gecsv['GCStart'] == False:
              metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
              report_octothorp(argv_list, metrcs, rowStr)

          else:
            gecsv['GCStart'] = True
            metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

            rowStr = read_geocsv_lines(url_iter, gecsv, metrcs, argv_list)
            if 'verbose' in argv_list:
              print("******* geocsv header finished, metrics: ", metrcs)
              print("******* geocsv header finished, GeoCSV: ", gecsv)

            # handle first non-geocsv line after finished reading geocsv lines
            handle_csv_row(rowStr, gecsv['delimiter'], metrcs, argv_list)
        else:
          # ignore octothorp lines after reading geocsv lines
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          report_octothorp(argv_list, metrcs, rowStr)
          continue
      else:
        # handle most non-geocsv for generic comment lines
        handle_csv_row(rowStr, gecsv['delimiter'], metrcs, argv_list)
    except StopIteration:
      if 'verbose' in argv_list: print("******* geocsvHandler finished *******")
      looping = False
    finally:
      response.close()

  report = check_geocsv_fields(metrcs, gecsv)

  if not 'test_mode' in argv_list:
    printReport(report)

  return report

def printReport(report):
  for itm in report['order']:
    if isinstance(report[itm], dict) and itm == 'geocsv_field_sizes':
      print("-- ", itm, ": ")
      for it2 in report[itm]:
        print("---- ", it2, ": ", report[itm][it2])
    else:
      print("-- ", itm, ": ", report[itm])

def check_geocsv_fields(metrcs, gecsv):
  report = {'GeoCSV-validated': True,
      'order': ['GeoCSV-validated', 'url', 'metrics']}
  report['url'] = gecsv['url_string']
  report['metrics'] = metrcs

  # check for start
  if (not gecsv['GCStart']):
    report['GeoCSV-validated'] = False
    report['order'].append('no_geocsv_start')
    report['no_geocsv_start'] = 'WARNING, did not find starting GeoCSV line like: '\
        + str(GEOCSV_REQUIRED_START_LITERAL)

  # check for consistent geocsv field parameter values
  thisFldDict = {}
  showThisFldDict = False
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
    report['GeoCSV-validated'] = False
    report['order'].append('geocsv_field_size_error')
    report['geocsv_field_size_error'] = 'ERROR, geocsv inconsistent field sizes'
    showThisFldDict = True

  # check for consistent data field values
  if len(metrcs['dataFieldsCntSet']) > 1:
    report['GeoCSV-validated'] = False
    report['order'].append('data_field_size_error')
    report['data_field_size_error'] = 'ERROR, more than one size for data rows, row sizes: '\
        + str(metrcs['dataFieldsCntSet'])

  # check for consistent field sizes between data and geocsv field parameters
  if len(metrcs['dataFieldsCntSet'].union(gecsvFieldCntSet)) >\
      max(len(metrcs['dataFieldsCntSet']), len(gecsvFieldCntSet)):
    report['GeoCSV-validated'] = False
    report['order'].append('geocsv_to_data_field_size_error')
    report['geocsv_to_data_field_size_error'] =\
        'ERROR, row size inconsistent with geocsv field size, data row sizes: '\
        + str(metrcs['dataFieldsCntSet']) + '  geocsv field sizes: ' + str(gecsvFieldCntSet)
    showThisFldDict = True

  if showThisFldDict:
    report['order'].append('geocsv_field_sizes')
    report['geocsv_field_sizes'] = thisFldDict

  return report

if __name__ == "__main__" \
    or __name__ == "geocsvValidate" \
    or __name__ == "src.python.main.geocsvValidate":

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

  validate(url_string, sys.argv)

