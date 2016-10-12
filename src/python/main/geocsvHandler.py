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
## import urllib2
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import sys
import csv

my_line_break_chars = '\n\r'

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

def handle_octothorp_row(rStr, geme, verbose):
  if verbose: print("geocsv? or skip if after start: " + rStr.rstrip())

  if geme['GCStart'] == False: 
    if rStr[1:21] == ' dataset: GeoCSV 2.0': geme['GCStart'] = True
  else:
    return

def read_geocsv_lines(url_iter, gc, gm):
  try:
    rowStr = next(url_iter).decode('utf-8').rstrip(my_line_break_chars)
    gm['totalLines'] = gm['totalLines'] + 1
    gc['d'] = gc['d'] + 1
    if len(rowStr) <= 0 :
      gm['zeroLenCnt'] = gm['zeroLenCnt'] + 1
      print("^^^^^^^^^ unexpected c, gm: ", gm, " l: ", len(rowStr))
      rowStr = read_geocsv_lines(url_iter, gc, gm)
    if rowStr[0:1] == '#' :
      print("$$$$$$$$$ next: " + rowStr)
      # do geocsv processing
      rowStr = read_geocsv_lines(url_iter, gc, gm)
  except StopIteration:
    raise StopIteration
  return rowStr

def handle_csv_row(rowStr, delimiter, gm, verbose):
  # csv module interface is not setup to stream one line at a time,
  # so make a list of 1 row
  rowiter = iter(list([rowStr]))

  csvreadr = csv.reader(rowiter, delimiter = delimiter)
  for row in csvreadr:
    gm['rowCnt'] = gm['rowCnt'] + 1
    if verbose: print(gm, " l: ", len(row), "  r: ", "  <:>  ".join(row))

    if len(row) <= 0 :
      # ignore this for now, should have been caught before here,
      # count up to see if this occurs
      gm['csvZeroLenCnt'] = gm['csvZeroLenCnt'] + 1
      print("-- unexpected b, gm: ", gm, " l: ", len(row), "  r: ", "<>".join(row))

def validate(url_string, verbose):
  # put newline to separate from unit test "dot"
  if verbose: print()

  response = get_response(url_string, verbose)

  ##text = response.read()
  ##print ("**** text: " + text)

  # capture metrics about content
  # gm - geocsv metrics about geocsv content
  # oct - short for octothorp, technical name for hash symbol
  # GC - short for geocsv
  gm = {'totalLines': 0, 'rowCnt': 0, 'zeroLenCnt': 0,
    'octLeadIn': 0, 'octNotGC': 0,
    'csvZeroLenCnt': 0}

  # geocsv object
  gc = {'GCStart': False, 'd': 0}

  url_iter = response.readlines().__iter__()
  looping = True
  while looping:
    try:
      rowStr = next(url_iter).decode('utf-8').rstrip(my_line_break_chars)
      gm['totalLines'] = gm['totalLines'] + 1

      if len(rowStr) <= 0 :
        gm['zeroLenCnt'] = gm['zeroLenCnt'] + 1
        print("^^^^^^^^^ unexpected a, gm: ", gm, " l: ", len(rowStr))
        continue

      if rowStr[0:1] == '#':
        # ignore octothorp lines until start of geocsv, then read
        # lines as geocsv header lines until first non-octothorp line
        if gc['GCStart'] == False:
          if rowStr[1:21] == ' dataset: GeoCSV 2.0':
            gc['GCStart'] = True
            print("&&&&&&&&& start of geocsv")

            rowStr = read_geocsv_lines(url_iter, gc, gm)
            print("@@@@@@@@@ gc: ", gc)
            # handle first non-geocsv line
            handle_csv_row(rowStr, '|', gm, verbose)
          else:
            if gc['GCStart'] == False:
              print("^^^^^^^^^ non-geocsv line: " + rowStr.rstrip())
              gm['octLeadIn'] = gm['octLeadIn'] + 1
        else:
          # ignore octothorp lines before start of geocsv or after reading
          # initial, consecutive set of geocsv lines
          print("^^^^^^^^^ non-geocsv line: " + rowStr.rstrip())
          gm['octNotGC'] = gm['octNotGC'] + 1
          continue
      else:
        # handle most non-geocsv for generic comment lines
        handle_csv_row(rowStr, '|', gm, verbose)
    except StopIteration:
      print("** finished **")
      looping = False
    finally:
      response.close()

  if verbose: print(">>> gm: ", gm)
  if verbose: print(">>> gc: ", gc)

if __name__ == "__main__" \
    or __name__ == "geocsvValidate" \
    or __name__ == "src.python.main.geocsvValidate":
  print("len args: ", len(sys.argv))
  if len(sys.argv) > 2:
    url_string = sys.argv[1]
  else:
    url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'

  runvalidate(url_string)

