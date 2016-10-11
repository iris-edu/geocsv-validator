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

def validate(url_string):
  try:
    print("****** try: " + url_string)
    response = urlopen(url_string)
  except HTTPError as e:
    print(e.code)
    print(e.read())
    print("** failed on target: ", URL)
    sys.exit()

  print("****** waiting for reply ...")

  ##text = response.read()
  ##print ("**** text: " + text)

  totalCnt = 0;
  rowCnt = 0
  try:
    for line in response.readlines() :
      totalCnt = totalCnt + 1

      rowStr = line.decode('utf-8')

      if len(rowStr) == 0 :
        print ("** line of length 0")
        continue

      if rowStr[0:1] == '#' :
        print("geocsv? or skip if after start: " + rowStr.rstrip())
        continue

      # make a list of 1 so as to access csv reader interface,
      # TBD - look for a better way
      rowlist = []
      rowlist.append(rowStr)
      rowiter = iter(rowlist)

      csvreadr = csv.reader(rowiter, delimiter='|')
      for row in csvreadr:
        rowCnt = rowCnt + 1

        if len(row) <= 0 :
          print("** row of length 0")
          continue

        print(rowCnt, " l: ", len(row), "  r: ", "  <:>  ".join(row))

  finally:
    response.close()

  print("totalCnt: ", totalCnt, "  rowCnt; ", rowCnt)

if __name__ == "__main__" \
    or __name__ == "geocsvValidate" \
    or __name__ == "src.python.main.geocsvValidate":
  print("len args: ", len(sys.argv))
  if len(sys.argv) > 2:
    url_string = sys.argv[1]
  else:
    url_string = 'http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true'

  runvalidate(url_string)

