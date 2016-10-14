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

def get_response(url_string, verbose):
  try:
    if verbose: print("****** try: " + url_string)
    response = urlopen(url_string)
  except HTTPError as e:
    print(e.code)
    print(e.read())
    print("** failed on target: ", URL)
    sys.exit()

  if verbose: print("****** waiting for reply ...")

  return response

def read_geocsv_lines(url_iter, geocobj, metrcs):
  try:
    rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
    metrcs['totalLineCnt'] = metrcs['totalLineCnt'] + 1

    if len(rowStr) <= 0:
      # ignore zero length line
      metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

      # keep reading, note: will be a stack overflow for many null lines
      # are many null lines
      rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)

    if rowStr[0:1] == '#':
      # count any octothorp line as geocsv line until exiting at first non-octothorp
      metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

      # do geocsv processing
      m = re.match(KEYWORD_REGEX, rowStr)
      if m == None:
        metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
        raise Exception("error no keyword, m: " + str(metrcs) + "  rowStr: " + rowStr)
      else:
        keyword = m.group(1).strip()
        if len(keyword) <= 0:
          # poorly formed line, like #:, or # :
          print("^^^^^^^^^ unexpected - keyword is zero len, metrcs: ", metrcs, " l: ", len(rowStr), "  rowStr: ", rowStr)
          raise Exception("GeoCSV line parsed to a keyword of zero length")
        value = rowStr[len(m.group(0)):].strip()

        if sys.version_info[0] < 3:
          # avoid using unicode strings when running python 2
          keyword = keyword.encode('ascii')
          value = value.encode('ascii')

        if keyword in GEOCSV_WELL_KNOWN_KEYWORDS:
          geocobj[keyword] = value
        else:
          geocobj['non_geocsv_obj'][keyword] = value

      # keep reading as long as octothorp found
      rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)
    # if no octothorp, return out of the recursion and process rowStr
  except StopIteration:
    raise StopIteration

  return rowStr

def handle_csv_row(rowStr, delimiter, metrcs, verbose):
  # csv module interface is not setup to stream one line at a time,
  # so make a list of 1 row
  rowiter = iter(list([rowStr]))

  csvreadr = csv.reader(rowiter, delimiter = delimiter)
  for row in csvreadr:
    metrcs['rowCnt'] = metrcs['rowCnt'] + 1
    if verbose: print(metrcs, " l: ", len(row), "  row: ", row)

    if len(row) <= 0 :
      # not sure this can ever happen
      estr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
          + "  input rowStr: " + rowStr
      raise Exception(estr)

def validate(url_string, verbose):
  # put newline to separate from unit test "dot"
  if verbose: print()

  response = get_response(url_string, verbose)

  # dump response
  ##text = response.read()
  ##print ("**** text: " + text)

  # capture metrics about content
  # metrcs - geocsv metrics about geocsv content
  # octothorp - technical name for hash symbol
  # geocobj - short for geocsv
  metrcs = {'totalLineCnt': 0, 'rowCnt': 0, 'zeroLenCnt': 0,
    'ignoreLineCnt': 0, 'geocsvLineCnt': 0}

  # geocsv object
  geocobj = {'GCStart': False, 'delimiter': ',', 'non_geocsv_obj': {}}

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
        if geocobj['GCStart'] == False:
          mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
          if mObj == None:
            if geocobj['GCStart'] == False:
              metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          else:
            geocobj['GCStart'] = True
            metrcs['geocsvLineCnt'] = metrcs['geocsvLineCnt'] + 1

            if verbose: print("&&&&&&&&& start of geocsv")
            rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)
            if verbose: print("@@@@@@@@@ geocobj: ", geocobj)

            # handle first non-geocsv line after finished reading geocsv lines
            handle_csv_row(rowStr, geocobj['delimiter'], metrcs, verbose)
        else:
          # ignore octothorp lines after reading geocsv lines
          if verbose: print("^^^^^^^^^ non-header octothorp rowStr: "\
              + rowStr.rstrip())
          metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
          continue
      else:
        # handle most non-geocsv for generic comment lines
        handle_csv_row(rowStr, geocobj['delimiter'], metrcs, verbose)
    except StopIteration:
      if verbose: print("** geocsvHandler finished **")
      looping = False
    except Exception:
      print()
      print("Error +++++++ metrcs: ", metrcs)
      raise Exception("reraised it")
    finally:
      response.close()

  if verbose: print(">>> metrcs: ", metrcs)
  ##if verbose: print(">>> geocobj: ", geocobj)
  if verbose:
    for key in geocobj:
      print(">>> key: ", key, "  val: ", geocobj[key])
  ##print()
  print(">>> metrcs: ", metrcs)
  ##print(">>> geocobj: ", geocobj)

  return

if __name__ == "__main__" \
    or __name__ == "geocsvValidate" \
    or __name__ == "src.python.main.geocsvValidate":

  print("geocsvHandler argv: ", sys.argv)
  if len(sys.argv) > 1:
    url_string = sys.argv[1]
  else:
    url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'

  runvalidate(url_string)

