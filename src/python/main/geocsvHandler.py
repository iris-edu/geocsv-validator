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
    metrcs['totalLines'] = metrcs['totalLines'] + 1
    geocobj['d'] = geocobj['d'] + 1
    if len(rowStr) <= 0 :
      metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1
      print("^^^^^^^^^ unexpected c, metrcs: ", metrcs, " l: ", len(rowStr))
      # ignoring zero length row, keep reading
      rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)
    if rowStr[0:1] == '#' :
##      print("$$$$$$$$$ next: " + rowStr)
      # do geocsv processing
      m = re.match(KEYWORD_REGEX, rowStr)
      if m == None:
        print("^^^^^^^^^ unexpected - no keyword, metrcs: ", metrcs, " l: ", len(rowStr), "  rowStr: ", rowStr)
      else:
        keyword = m.group(1).strip()
        if len(keyword) <= 0:
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
      # keep reading
      rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)
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
    if verbose: print(metrcs, " l: ", len(row), "  r: ", "  <:>  ".join(row))

    if len(row) <= 0 :
      # ignore this for now, should have been caught before here,
      # count up to see if this occurs
      metrcs['csvZeroLenCnt'] = metrcs['csvZeroLenCnt'] + 1
      print("-- unexpected b, metrcs: ", metrcs, " l: ", len(row), "  r: ", "<>".join(row))

def validate(url_string, verbose):
  # put newline to separate from unit test "dot"
  if verbose: print()

  response = get_response(url_string, verbose)

  ##text = response.read()
  ##print ("**** text: " + text)

  # capture metrics about content
  # metrcs - geocsv metrics about geocsv content
  # oct - short for octothorp, technical name for hash symbol
  # geocobj - short for geocsv
  metrcs = {'totalLines': 0, 'rowCnt': 0, 'zeroLenCnt': 0,
    'octLeadIn': 0, 'octNotGC': 0,
    'csvZeroLenCnt': 0}

  # geocsv object
  geocobj = {'GCStart': False, 'd': 0, 'delimiter': ',', 'non_geocsv_obj': {}}

  url_iter = response.readlines().__iter__()
  looping = True
  while looping:
    try:
      rowStr = next(url_iter).decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
      metrcs['totalLines'] = metrcs['totalLines'] + 1

      if len(rowStr) <= 0 :
        metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1
        print("^^^^^^^^^ unexpected a, metrcs: ", metrcs, " l: ", len(rowStr))
        continue

      if rowStr[0:1] == '#':
        # ignore octothorp lines until start of geocsv, then read
        # lines as geocsv header lines until first non-octothorp line
        if geocobj['GCStart'] == False:
          m = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
          if m != None:
            geocobj['GCStart'] = True
            print("&&&&&&&&& start of geocsv")

            rowStr = read_geocsv_lines(url_iter, geocobj, metrcs)

            print("@@@@@@@@@ geocobj: ", geocobj)
            # handle first non-geocsv line after reading geocsv lines
            handle_csv_row(rowStr, geocobj['delimiter'], metrcs, verbose)
          else:
            if geocobj['GCStart'] == False:
              print("^^^^^^^^^ non-geocsv line: " + rowStr.rstrip())
              metrcs['octLeadIn'] = metrcs['octLeadIn'] + 1
        else:
          # ignore octothorp lines before start of geocsv or after reading
          # initial, consecutive set of geocsv lines
          print("^^^^^^^^^ non-header octothorp line: " + rowStr.rstrip())
          metrcs['octNotGC'] = metrcs['octNotGC'] + 1
          continue
      else:
        # handle most non-geocsv for generic comment lines
        handle_csv_row(rowStr, geocobj['delimiter'], metrcs, verbose)
    except StopIteration:
      print("** finished **")
      looping = False
    finally:
      response.close()

  if verbose: print(">>> metrcs: ", metrcs)
  if verbose: print(">>> geocobj: ", geocobj)

if __name__ == "__main__" \
    or __name__ == "geocsvValidate" \
    or __name__ == "src.python.main.geocsvValidate":
  print("len args: ", len(sys.argv))
  if len(sys.argv) > 2:
    url_string = sys.argv[1]
  else:
    url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'

  runvalidate(url_string)

