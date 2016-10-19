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

MY_LINE_BREAK_CHARS = '\n\r'

# definition for keyword
# for regex '^# *(.+?):' select first non greedy character group starting
#   at the beginning of a line that starts with an octothorp (i.e. '#') that may
#   have 0 or more spaces and at least 1 character ending with colon
KEYWORD_REGEX = '^# *(.+?):'

GEOCSV_REQUIRED_START_REGEX = '^# *dataset *: *GeoCSV 2.0'

GEOCSV_WELL_KNOWN_KEYWORDS = {'dataset', 'delimiter', 'field_unit',
    'field_type', 'field_long_name', 'field_standard_name', 'field_missing',
    'attribution', 'standard_name_cv', 'title', 'history', 'institution',
    'source', 'comment', 'references'}

def get_response(url_string, argv_list):
  try:
    if 'verbose' in argv_list\
        or 'brief' in argv_list:
      print("****** try to open url_string: " + url_string)
    response = urlopen(url_string)
  except HTTPError as e:
    print(e.code)
    print(e.read())
    print("** failed on target: ", URL)
    sys.exit()

  if 'verbose' in argv_list\
      or 'brief' in argv_list:
    print("****** waiting for reply ...")

  return response

def read_geocsv_lines(url_iter, GChdr, metrcs, argv_list):
  try:
    rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
    metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1

    if len(rowStr) <= 0:
      # ignore zero length line
      metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

      # keep reading, note: will be a stack overflow for many null lines
      # are many null lines
      rowStr = read_geocsv_lines(url_iter, GChdr, metrcs, argv_list)

    if rowStr[0:1] == '#':
      # count any octothorp line as geocsv line until exiting at first non-octothorp
      metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

      # do geocsv processing
      mObj = re.match(KEYWORD_REGEX, rowStr)
      if mObj == None:
        # no geocsv keyword form, count and ignore
        metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
        if 'octothorp' in argv_list:
          print("octothorp ", metrcs, "  rowStr: ", rowStr.rstrip())
      else:
        keyword = mObj.group(1).strip()
        if len(keyword) <= 0:
          # poorly formed keyword, probably something like #:, or # :
          # count and ignore
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          if 'octothorp' in argv_list:
            print("octothorp ", metrcs, "  rowStr: ", rowStr.rstrip())
        value = rowStr[len(mObj.group(0)):].strip()

        if sys.version_info[0] < 3:
          # avoid using unicode strings when running python 2
          keyword = keyword.encode('ascii')
          value = value.encode('ascii')

        if keyword in GEOCSV_WELL_KNOWN_KEYWORDS:
          GChdr[keyword] = value
        else:
          GChdr['other_keywords'][keyword] = value

      # keep reading as long as octothorp found
      rowStr = read_geocsv_lines(url_iter, GChdr, metrcs, argv_list)
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
    if 'verbose' in argv_list: print(metrcs, " l: ", len(row), "  row: ", row)

    if len(row) <= 0 :
      # not sure this can ever happen
      estr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
          + "  input rowStr: " + rowStr
      raise Exception(estr)

def validate(url_string, argv_list):
  # put newline to separate from unit test "dot"
  if 'verbose' in argv_list\
      or 'brief' in argv_list\
      or 'metrics' in argv_list\
      or 'octothorp' in argv_list:
    print()

  response = get_response(url_string, argv_list)

  # dump response
  ##text = response.read()
  ##print ("**** text: " + text)

  # capture metrics about content
  # metrcs - geocsv metrics about geocsv content
  # octothorp - technical name for hash symbol
  # GChdr - short for geocsv
  metrcs = {'totalLineCnt': 0, 'rowCnt': 0, 'zeroLenCnt': 0,
    'ignoreLineCnt': 0, 'geocsvLineCnt': 0}

  # geocsv object
  GChdr = {'GCStart': False, 'delimiter': ',', 'other_keywords': {}}

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
        if GChdr['GCStart'] == False:
          mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
          if mObj == None:
            if GChdr['GCStart'] == False:
              metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
              if 'octothorp' in argv_list:
                print("octothorp ", metrcs, "  rowStr: ", rowStr.rstrip())
          else:
            GChdr['GCStart'] = True
            metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

            rowStr = read_geocsv_lines(url_iter, GChdr, metrcs, argv_list)
            if 'verbose' in argv_list: print("****** geocsv header finished: ", metrcs)

            # handle first non-geocsv line after finished reading geocsv lines
            handle_csv_row(rowStr, GChdr['delimiter'], metrcs, argv_list)
        else:
          # ignore octothorp lines after reading geocsv lines
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          if 'octothorp' in argv_list:
            print("octothorp ", metrcs, "  rowStr: ", rowStr.rstrip())
          continue
      else:
        # handle most non-geocsv for generic comment lines
        handle_csv_row(rowStr, GChdr['delimiter'], metrcs, argv_list)
    except StopIteration:
      if 'verbose' in argv_list: print("** geocsvHandler finished **")
      looping = False
    finally:
      response.close()

  if 'verbose' in argv_list:
    print(">>> metrcs: ", metrcs)
    print(">>> geocvs hdr: ", GChdr)

  if 'brief' in argv_list:
    print(">>> metrcs: ", metrcs)
    print(">>> geocvs hdr: ", GChdr) 

  if 'metrics' in argv_list:
    print(">>> metrcs: ", metrcs)

  return

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
    print('****** warning, there is no http:// or file:// reference on the'
        + ' command line list,')
    print("****** using default url: ", default_url_string)
    url_string = default_url_string

  validate(url_string, sys.argv)

