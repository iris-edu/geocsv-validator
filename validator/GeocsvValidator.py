#!/usr/bin/env python

# Setup code that runs in python 2 and python 3
# Note: "future" must be installed in both python 2 and 3 environments
from __future__ import absolute_import, division, print_function
from builtins import *
# generate NameError if an obsolete builtin is used in python 2
from future.builtins.disabled import *

# for urllib2 compatability
# replacing this --> import urllib2
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import sys
import csv
import re
import datetime
import pytz
import argparse
import collections
import io
import dateutil.parser

GEOCSV_CURRENT_VERSION = '0.9.5'

MY_LINE_BREAK_CHARS = '\n\r'

# definition for keyword
# for regex '^# *(.+?):' select first non greedy character group starting
#   at the beginning of a line that starts with an octothorp (i.e. '#') that may
#   have 0 or more spaces and at least 1 character ending with colon
KEYWORD_REGEX = '^# *(.+?):'

GEOCSV_REQUIRED_START_REGEX = '^# *dataset *: *GeoCSV 2.0'
GEOCSV_REQUIRED_START_LITERAL = '# dataset: GeoCSV 2.0'

GEOCSV_FIELD_TYPE = 'field_type'

GEOCSV_COLUMN_VALUED_KEYWORDS = {
    'field_unit', 'field_type', 'field_long_name', 'field_standard_name',
    'field_missing'}

GEOCSV_WELL_KNOWN_KEYWORDS = {
    'dataset', 'delimiter', 'attribution', 'standard_name_cv', 'title',
    'history', 'institution', 'source', 'comment', 'references'}.union(
    GEOCSV_COLUMN_VALUED_KEYWORDS)

GEOCSV_WELL_KNOWN_FIELD_TYPE = {'string', 'integer', 'float', 'datetime'}

# set limit to 4 times channel query size, and a little more
# e.g. 96867459 * 4 = 387469836 ~ 400 MB
GEOCSV_RUNAWAY_LIMIT = 1024 * 1024 * 400


class GeocsvValidator(object):
  """
  GeocsvValidator reads and validates streaming text data in GeoCSV
  format.

  See http://geows.ds.iris.edu/documents/GeoCSV.pdf
  """

  # stdwriter - a write type object with a write method, i.e.
  #             something like sys.stdout or tornado.web.RequestHandler
  def __init__(self, stdwriter):
    self.current_version = 0.95
    self.stdwriter = stdwriter

    if sys.version_info[0] < 3:
      self.force_to_ASCII_v_any = self.force_to_ASCII_py_v2
    else:
      self.force_to_ASCII_v_any = self.force_to_ASCII_py_v3

    self.field_type_test_functions = []

  def version(self):
    self.stdwriter.write(str(GEOCSV_CURRENT_VERSION))

  def try_field_type_noop(self, testStr):
    return 0

  def try_field_type_float(self, testStr):
    # consider null ok
    if len(testStr) <= 0:
      return 0

    try:
      float(testStr)
    except:
      return 1
    return 0

  def try_field_type_int(self, testStr):
    # consider null ok
    if len(testStr) <= 0:
      return 0

    try:
      int(testStr)
    except:
      return 1
    return 0

  def try_field_type_datetime_utc(self, testStr):
    # consider null ok
    if len(testStr) <= 0:
      return 0

    try:
      # Note: have to relax this for now
      # for UTC#      dt_utc = dateutil.parser.parse(testStr).astimezone(pytz.utc)
      dateutil.parser.parse(testStr)
    except:
      return 1
    return 0

  # Return a result object with an error report for the case where the
  # input parameters do not specify any input resource.
  def get_no_input_specified(self, pctl):
    result_for_get = {'data_iter': None, 'except_report': None}

    report = self.createNewReport(pctl)
    report['ERROR_no_input_specified'] = \
        'No data input option was selected'
    result_for_get['except_report'] = report
    return result_for_get

  def createNewReport(self, pctl):
    metrcs = self.createMetricsObj()
    gecsv = self.createGeocsvObj(pctl['input_resrc'], pctl['input_bytes'])
    report = self.check_geocsv_fields(metrcs, gecsv)
    return report

  def get_stdin_iterator(self, pctl):
    result_for_get = {'data_iter': None, 'except_report': None}

    try:
      self.report_verbose(pctl,
          "------- GeoCSV_Validate - getting stdin iterator")
      result_for_get['data_iter'] = sys.stdin.readlines().__iter__()
      if sys.version_info[0] < 3:
        # python 2 str is treated as bytes
        pctl['next_data_function'] = self.nextBytesFromBytes
      else:
        # python 3 stdin iterator returns a class 'str', but it needs
        # to be bytes for further processing
        pctl['next_data_function'] = self.nextBytesFromString
    except Exception as e:
      report = self.createNewReport(pctl)
      report['ERROR_Exception'] = "Failed stdin iterator create: " + str(e)
      result_for_get['except_report'] = report
      return result_for_get

    self.report_verbose(pctl,
        "------- GeoCSV_Validate - created stdin iterator,  " +
        "datetime: " + str(datetime.datetime.now(pytz.utc).isoformat()))
    return result_for_get

  def get_resrc_iterator(self, pctl):
    result_for_get = {'data_iter': None, 'except_report': None}
    if pctl['input_resrc'] == None:
      report = self.createNewReport(pctl)
      report['ERROR_get_resrc_iterator_None'] = \
          'None was entered for control parameter: input_resrc'
      result_for_get['except_report'] = report
      return result_for_get

    try:
      self.report_verbose(pctl,
          "------- GeoCSV_Validate - opening input_resrc: " + pctl['input_resrc'])
      response = urlopen(pctl['input_resrc'])
      result_for_get['data_iter'] = response.readlines().__iter__()
      pctl['next_data_function'] = self.nextBytesFromBytes
    except HTTPError as e:
      report = self.createNewReport(pctl)
      report['HTTPError_HTTPcode'] = str(e.code)
      report['HTTPError_Exception'] = str(e)
      result_for_get['except_report'] = report
      return result_for_get
    except Exception as e:
      try:
        # Input name string did not succeed as a URL, now try as a file
        file = open(pctl['input_resrc'], 'rb')
        result_for_get['data_iter'] = file.readlines().__iter__()
        pctl['next_data_function'] = self.nextBytesFromBytes
      except Exception as e2:
        report = self.createNewReport(pctl)
        # from exception e
        report['WARNING_urlopen_Exception'] = "GeocsvValidator failed to open" +\
          " input_resrc as a URL trying as a file."
        # from exception e2
        report['ERROR_open_Exception'] = "GeocsvValidator failed to open" +\
          " input_resrc as a file."
        result_for_get['except_report'] = report
        return result_for_get

    self.report_verbose(pctl,
        "------- GeoCSV_Validate - resource found, created data iterator,  " +
        "datetime: " + str(datetime.datetime.now(pytz.utc).isoformat()))
    return result_for_get

  def get_bytes_iterator(self, pctl):
    result_for_get = {'data_iter': None, 'except_report': None}
    if pctl['input_bytes'] == None:
      report = self.createNewReport(pctl)
      report['ERROR_get_bytes_iterator_None'] = \
          'None was entered for control parameter: input_bytes'
      result_for_get['except_report'] = report
      return result_for_get

    try:
      self.report_verbose(pctl,
          "------- GeoCSV_Validate - setup input_bytes len: " +
          str(len(pctl['input_bytes'])))
      bytes_obj = io.BytesIO(pctl['input_bytes'])
      result_for_get['data_iter'] = bytes_obj.readlines().__iter__()
      pctl['next_data_function'] = self.nextBytesFromBytes
    except Exception as e:
      report = self.createNewReport(pctl)
      report['ERROR_Exception'] = str(e)
      result_for_get['except_report'] = report
      return result_for_get

    self.report_verbose(pctl,
        "------- GeoCSV_Validate - read bytes iterator created,  datetime: " +
        str(datetime.datetime.now(pytz.utc).isoformat()))
    return result_for_get

  def nextBytesFromString(self, data_iter):
    return next(data_iter).encode()

  def nextBytesFromBytes(self, data_iter):
    return next(data_iter)

  def get_a_line(self, data_iter, metrcs, pctl):
    nxtLine = pctl['next_data_function'](data_iter)
    rowStr = nxtLine.decode('utf-8').rstrip(MY_LINE_BREAK_CHARS)
    metrcs['totalLineCnt'] += 1
    # this is aproximately the byte count, there may be more than one
    # line break character, but more importantly, this allow for counting
    # potentially runaway input with non data, only line breaks
    metrcs['linep1ByteCnt'] += len(rowStr) + 1
    if metrcs['linep1ByteCnt'] > GEOCSV_RUNAWAY_LIMIT:
      raise StopIteration
    rowStr = self.force_to_ASCII(rowStr, metrcs, pctl)
    return rowStr

  def read_geocsv_lines(self, data_iter, gecsv, metrcs, pctl):
    try:
      rowStr = self.get_a_line(data_iter, metrcs, pctl)

      if len(rowStr) <= 0:
        # ignore zero length line
        metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1

        # keep reading, note: potential for stack overflow if many null lines
        rowStr = self.read_geocsv_lines(data_iter, gecsv, metrcs, pctl)

      if rowStr[0:1] == '#':
        # count any octothorp line as geocsv line until exiting at first non-octothorp
        metrcs['geocsvHdrLineCnt'] = metrcs['geocsvHdrLineCnt'] + 1

        # do geocsv processing
        mObj = re.match(KEYWORD_REGEX, rowStr)
        if mObj is None:
          # no start of geocsv yet, treat as comment line, count and ignore
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
      else:
        # when no more octothorp, finish here and
        # return out of the recursion and process rowStr
        #
        # set up field_type_test_functions if available
        self.field_type_test_functions = []
        if GEOCSV_FIELD_TYPE in gecsv:
          # read csv string using csv.reader as else where in this program,
          # i.e. create a list of one row
          field_type_list = []
          rowiter = iter(list([gecsv[GEOCSV_FIELD_TYPE]]))
          csvreadr = csv.reader(rowiter, delimiter=gecsv['delimiter'])
          for row in csvreadr:
            field_type_list = row

          for ft in field_type_list:
            fiTyp = ft.strip().lower()
            if fiTyp == 'float':
              self.field_type_test_functions.append(self.try_field_type_float)
            elif fiTyp == 'integer':
              self.field_type_test_functions.append(self.try_field_type_int)
            elif fiTyp == 'datetime':
              self.field_type_test_functions.append(self.try_field_type_datetime_utc)
            elif fiTyp == 'string':
              self.field_type_test_functions.append(self.try_field_type_noop)
            else:
              metrcs['unknownFieldTypeCnt'] += 1
              self.report_verbose(pctl, "--verbose-- " + str(list(metrcs.values())) +
                  " line:" + str(row))
              self.field_type_test_functions.append(self.try_field_type_noop)
    except StopIteration:
      raise StopIteration

    return rowStr

  # Force to ASCII
  # The main reason for this is that the cvs reader in python 2 does not
  # handle unicode and station data has a few lines which contain unicode
  def handle_unicode(self, rowStr, metrcs, pctl):
    metrcs['unicodeLineCnt'] = metrcs['unicodeLineCnt'] + 1
    rowASCII = rowStr.encode('ascii', 'replace').decode('ascii')
    if pctl['verbose'] or pctl['unicode']:
      try:
        # Try to print the unicode line, but when this does not work,
        # except out and print the ASCII version
        self.stdwriter.write("--unicode-- " + str(list(metrcs.values())) +
            "  line: " + str(rowStr.rstrip()) + "\n")
      except UnicodeEncodeError:
        self.stdwriter.write("--unicode-- " + str(list(metrcs.values())) +
            "  line: " + str(rowASCII) + "\n")
    return rowASCII

  def force_to_ASCII_py_v2(self, rowStr, metrcs, pctl):
    return rowStr.decode('utf-8')

  def force_to_ASCII_py_v3(self, rowStr, metrcs, pctl):
    str(rowStr.encode('ascii'))
    return rowStr

  # python 2 csv.reader does not handle unicode values,
  # so force input data to ASCII
  def force_to_ASCII(self, rowStr, metrcs, pctl):
    try:
      rowASCII = self.force_to_ASCII_v_any(rowStr, metrcs, pctl)
    except UnicodeEncodeError:
      rowASCII = self.handle_unicode(rowStr, metrcs, pctl)

    return rowASCII

  def handle_csv_row(self, rowStr, delimiter, metrcs, pctl, isCSVHeaderLine):
    # csv module interface is not setup to stream one line at a time,
    # so make a list of 1 using the incoming row and convert to an iterator
    rowiter = iter(list([rowStr]))
    csvreadr = csv.reader(rowiter, delimiter=delimiter)
    for row in csvreadr:
      metrcs['dataLineCnt'] = metrcs['dataLineCnt'] + 1
      metrcs['dataFieldsCntSet'].add(len(row))

      anyNulls = False
      anyTypeErrs = False
      itmIdx = 0
      for itm in row:
        # a length of zero for a cell item is used as the definition of null
        # csv.reader evedently converts input fields to strings
        if len(itm) <= 0:
          metrcs['nullFieldCnt'] = metrcs['nullFieldCnt'] + 1
          anyNulls = True

        if isCSVHeaderLine:
          # i.e. not type checking on CSV header line
          pass
        else:
          if itmIdx < len(self.field_type_test_functions):
            if self.field_type_test_functions[itmIdx](itm) > 0:
              metrcs['dataTypeErrorCnt'] += 1
              anyTypeErrs = True

        itmIdx += 1

      # Note: this line should be located after any metric count update for any
      #       row so that when looking at verbose listing, the occurrence of a
      #       counter change is on the same line it occurred, not one before
      #       or one after
      self.report_verbose(pctl, "--verbose-- " + str(list(metrcs.values())) +
          " line:" + str(row))

      if anyNulls and pctl['null_fields']:
        self.stdwriter.write("--null_fields-- " + str(list(metrcs.values())) +
            "  line: " + str(rowStr.rstrip()) + "\n")

      if anyTypeErrs and pctl['field_type']:
        self.stdwriter.write("--unexpected_field_type-- " +
            str(list(metrcs.values())) + "  line: " + str(rowStr.rstrip()) +
            "\n")

      if len(row) <= 0:
        # not sure this can ever happen
        eStr = "Error, zero columns from csv procession, metrcs: " + str(metrcs)\
            + "  input rowStr: " + rowStr
        raise Exception(eStr)

  # octothorp - name for hash symbol
  def report_octothorp(self, pctl, metrcs, rowStr):
    if pctl['octothorp']:
      self.stdwriter.write("--octothorp-- " + str(list(metrcs.values())) +
          "  line: " + str(rowStr.rstrip()) + "\n")

  # Create an object to hold counts about the input text as the text is
  # processed.
  def createMetricsObj(self):
    metrcs = collections.OrderedDict()
    metrcs['totalLineCnt'] = 0
    metrcs['linep1ByteCnt'] = 0
    metrcs['dataLineCnt'] = 0
    metrcs['zeroLenCnt'] = 0
    metrcs['ignoreLineCnt'] = 0
    metrcs['geocsvHdrLineCnt'] = 0
    metrcs['dataFieldsCntSet'] = set()
    metrcs['nullFieldCnt'] = 0
    metrcs['dataTypeErrorCnt'] = 0
    metrcs['unicodeLineCnt'] = 0
    metrcs['unknownFieldTypeCnt'] = 0

    return metrcs

  # Create gecsv object - an object to contain GeoCSV defined information
  # found in the header as well as other, undefined keywords. In verbose mode,
  # this structure is printed out and can be checked for incorrect spelling of
  # keywords, etc.
  def createGeocsvObj(self, input_resrc, input_bytes):
    gecsv = {'geocsv_start_found': False, 'input_resrc': input_resrc,
        'delimiter': ',', 'other_keywords': {}}
    # don't put the raw bytes in this structure
    if input_bytes is None:
      gecsv['input_bytes_len'] = None
    else:
      gecsv['input_bytes_len'] = len(input_bytes)
    return gecsv

  def processGeocsvHeader(self, data_iter, gecsv, metrcs, pctl):
    gecsv['geocsv_start_found'] = True
    metrcs['geocsvHdrLineCnt'] = metrcs['geocsvHdrLineCnt'] + 1
    # read expected geocsv lines until a non-octothorp line is read
    rowStr = self.read_geocsv_lines(data_iter, gecsv, metrcs, pctl)

    self.report_verbose(pctl,
        "------- GeoCSV_Validate - parsed header and status parameters: " +
        str(gecsv))
    self.report_verbose(pctl,
        "------- GeoCSV_Validate - after header read metrics: " +
          str(list(metrcs.values())))

    # handle first non-geocsv line after finished reading geocsv header lines
    # This should be the one and only CSV header line
    self.handle_csv_row(rowStr, gecsv['delimiter'], metrcs, pctl, True)

  def report_any(self, pctl, str1):
    if pctl['verbose'] or pctl['octothorp'] or pctl['unicode'] or pctl['null_fields']:
      self.stdwriter.write(str1 + "\n")

  def report_verbose(self, pctl, str1):
    if pctl['verbose']:
      self.stdwriter.write(str1 + "\n")

  def validate(self, pctl, data_iter):
    metrcs = self.createMetricsObj()

    self.report_any(pctl, "\n" +
      "------- GeoCSV_Validate - starting validate  datetime: " +
      str(datetime.datetime.now(pytz.utc).isoformat()))

    gecsv = self.createGeocsvObj(pctl['input_resrc'], pctl['input_bytes'])

    # note: creating a list of keys here for compatability between py 2.x and 3.x
    msglist = list(metrcs.keys())
    self.report_any(pctl, "------- GeoCSV_Validate - metric fields: " +
      str(msglist))

    looping = True
    while looping:
      try:
        rowStr = self.get_a_line(data_iter, metrcs, pctl)

        if len(rowStr) <= 0:
          # ignore zero length line
          metrcs['zeroLenCnt'] = metrcs['zeroLenCnt'] + 1
          continue

        if rowStr[0:1] == '#':
          # ignore octothorp lines until start of geocsv, then read
          # until first non-octothorp line
          if gecsv['geocsv_start_found'] == False:
            mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
            if mObj is None:
              if gecsv['geocsv_start_found'] == False:
                metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
                self.report_octothorp(pctl, metrcs, rowStr)
            else:
              self.processGeocsvHeader(data_iter, gecsv, metrcs, pctl)
          else:
            # ignore octothorp lines after reading geocsv lines
            mObj = re.match(GEOCSV_REQUIRED_START_REGEX, rowStr)
            if mObj is None:
              metrcs['ignoreLineCnt'] = metrcs['ignoreLineCnt'] + 1
              self.report_octothorp(pctl, metrcs, rowStr)
            else:
              # a new Geocsv set is found, do report
              metrcs['totalLineCnt'] -= 1
              metrcs['linep1ByteCnt'] -= (len(rowStr) + 1)
              report = self.check_geocsv_fields(metrcs, gecsv)
              self.writeReport(pctl, report)

              # and reset metrics and geocsv obj and continue validate
              metrcs = self.createMetricsObj()
              metrcs['totalLineCnt'] += 1
              metrcs['linep1ByteCnt'] += len(rowStr) + 1
              gecsv = self.createGeocsvObj(pctl['input_resrc'], pctl['input_bytes'])

              self.processGeocsvHeader(data_iter, gecsv, metrcs, pctl)
            continue
        else:
          # handle non-octothorp lines
          self.handle_csv_row(rowStr, gecsv['delimiter'], metrcs, pctl, False)
      except StopIteration:
        self.report_any(pctl, "------- GeoCSV_Validate - finished validate," +
            " datetime: " + str(datetime.datetime.now(pytz.utc).isoformat()))
        looping = False
      finally:
        # response.close()
        pass

    report = self.check_geocsv_fields(metrcs, gecsv)
    return report

  def createReportStr(self, report):
    processing_seconds = datetime.datetime.now(pytz.utc) - self.processingStartTime
    rstr = "-- GeoCSV_Validate_Report  datetime: " + \
        str(datetime.datetime.now(pytz.utc).isoformat()) + \
        "  processing_seconds: " + str(processing_seconds.total_seconds()) + \
        "  version: " + GEOCSV_CURRENT_VERSION + "\n"
    for itm in report:
      if isinstance(report[itm], dict) and itm == 'ERROR_between_these_geocsv_fields':
        rstr += "-- " + str(itm) + ": " + "\n"
        if len(report[itm]) > 0:
          for it2 in report[itm]:
            rstr += "---- " + str(it2) + ": " + str(report[itm][it2]) + "\n"
        else:
            rstr += "---- no geocsv fields_* keywords detected" + "\n"
      else:
        if itm == 'metrics':
          # trickery to make OrderedDict look similar between 2.x and 3.x
          rstr += "-- " + str(itm) + ": " + str(list(report[itm].items())) + "\n"
        else:
          rstr += "-- " + str(itm) + ": " + str(report[itm]) + "\n"
    return rstr

  def writeReport(self, pctl, report):
    if pctl['write_report']:
      # allows for not printing report, so unit tests can be very succinct
      rstr = self.createReportStr(report)
      self.stdwriter.write(rstr)

  # doReport writes to stdout or designated web object, depending on
  # what stdwrite object was used to initialize the GeocsvValidator class.
  #
  # This control option, pctl['write_report'], can be set to false to
  # prevent writing the report output, this is intended for unit tests
  # presentation.
  def doReport(self, pctl):
    """
    Use the **pctl** map to set *control* options for doing validation.
    """
    self.processingStartTime = datetime.datetime.now(pytz.utc)

    # Check for data to read, get the respective iterator and if successful,
    # do the validate and write a report.
    if pctl['version']:
      # match other services, not in report form, just a string, no LF or CRLF
      self.version()
      return
    elif pctl['stdin']:
      result_for_get = self.get_stdin_iterator(pctl)
    elif pctl['input_resrc']:
      result_for_get = self.get_resrc_iterator(pctl)
    elif pctl['input_bytes']:
      result_for_get = self.get_bytes_iterator(pctl)
    else:
      result_for_get = self.get_no_input_specified(pctl)

    if result_for_get['except_report'] == None:
      # no error report, continue with validation
      data_iter = result_for_get['data_iter']
      report = self.validate(pctl, data_iter)
    else:
      # return error report
      report = result_for_get['except_report']

    self.writeReport(pctl, report)

    return report

  # This is where validation pass/fail is determined for a given
  # dataset. Validity is determine by checking various metrics and
  # header values against the GeoCSV standard.
  def check_geocsv_fields(self, metrcs, gecsv):
    report = collections.OrderedDict()
    report['GeoCSV_validated'] = True
    report['input_resrc'] = gecsv['input_resrc']
    report['input_bytes_len'] = gecsv['input_bytes_len']
    report['metrics'] = metrcs

    # check for start
    if (not gecsv['geocsv_start_found']):
      report['GeoCSV_validated'] = False
      report['WARNING_no_geocsv_start'] = 'No GeoCSV start-of-header found,' + \
          ' expecting this line: ' + str(GEOCSV_REQUIRED_START_LITERAL)

    # check for consistent geocsv field parameter values
    thisFldDict = collections.OrderedDict()
    showGeoCSVFldsDict = False
    gecsvFieldCntSet = set()
    fldSet = GEOCSV_COLUMN_VALUED_KEYWORDS.intersection(set(gecsv.keys()))
    for fldname in fldSet:
      rowiter = iter(list([gecsv[fldname]]))
      csvreadr = csv.reader(rowiter, delimiter=gecsv['delimiter'])
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
      report['ERROR_ geocsv_to_data_field_size'] = 'A row size is inconsistent' + \
          ' with geocsv field size, data row sizes: ' + str(metrcs['dataFieldsCntSet']) + \
          '  geocsv field sizes: ' + str(gecsvFieldCntSet)
      showGeoCSVFldsDict = True

    # check for field size of one, which may imply a missing delimiter keyword
    # Note: this check must follow the ERROR_ geocsv_to_data_field_size check
    if report['GeoCSV_validated']:
      # only check if data field and keyword fields are consistent
      if 1 in metrcs['dataFieldsCntSet'] and len(metrcs['dataFieldsCntSet']) == 1 \
         and 1 in gecsvFieldCntSet and len(gecsvFieldCntSet) == 1:
        # note: not set#report['GeoCSV_validated'] = False
        report['INFO_all_fields_sizes_are_1'] = 'This may be correct, or the delimiter ' + \
            'keyword may be missing.'

    # check for null data field values
    if metrcs['nullFieldCnt'] > 0:
      # note: not set#report['GeoCSV_validated'] = False
      report['INFO_data_field_null'] = 'At least one data field ' + \
          'was zero length (i.e. null), null count: ' + str(metrcs['nullFieldCnt'])

    if metrcs['unknownFieldTypeCnt'] > 0:
      report['GeoCSV_validated'] = False
      report['ERROR_unknown_field_type'] = 'There are one or more unknown field types ' + \
          'in the field_type keyword, count: ' + str(metrcs['unknownFieldTypeCnt']) + \
          '  field_type: ' + gecsv['field_type']

    # check for unexpected field data type
    if metrcs['dataTypeErrorCnt'] > 0:
      report['GeoCSV_validated'] = False
      report['ERROR_in_data_type'] = 'At least one data value ' + \
          'did not convert to the type specified in keyword: ' + GEOCSV_FIELD_TYPE + \
          ',  count: ' + str(metrcs['dataTypeErrorCnt'])

    # check for unicode in field values
    if metrcs['unicodeLineCnt'] > 0:
      # note: not set#report['GeoCSV_validated'] = False
      report['INFO_unicode_in_field'] = 'At least one line has a data field ' + \
          'with a UNICODE character, count: ' + str(metrcs['unicodeLineCnt'])

    # check for null data field values
    if metrcs['linep1ByteCnt'] > GEOCSV_RUNAWAY_LIMIT:
      report['GeoCSV_validated'] = False
      report['WARNING_runaway_byte_limit_exceded'] = 'The byte count of ' + \
          'incoming data on each line plus 1 byte counted for each line, ' + \
          'exceded: ' + str(GEOCSV_RUNAWAY_LIMIT)

    # if any errors or warning are related to the field parameters in the
    # geocsv header, show the specific parameters for this file
    if showGeoCSVFldsDict:
      report['ERROR_between_these_geocsv_fields'] = thisFldDict

    return report


# Helper for command line parsing in argparse to increase flexibility
# for accepatble values for True and False
# from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
  if v.lower() in ('yes', 'true', 't', 'y', '1'):
      return True
  elif v.lower() in ('no', 'false', 'f', 'n', '0'):
      return False
  else:
      raise argparse.ArgumentTypeError('String version of Boolean value' +
        ' expected, value given: ' + str(v))


# Create a default control structure for a validate run.
def default_program_control():
  pctl = {}

  # A regular URL that returns GeoCSV text data
  pctl['input_resrc'] = None

  # Input raw bytes, # Note: if both input_resrc and input_bytes are
  # specified, input_resrc will be used
  pctl['input_bytes'] = None  # i.e. of form b'line1\nline2\n'

  pctl['verbose'] = False

  # Show lines that start with #
  pctl['octothorp'] = False

  # Show lines where unicode is detected
  pctl['unicode'] = False

  # Show lines if any field is null
  pctl['null_fields'] = False

  # When GeoCSV field_type header line is present, check fields for
  # types integer, float, or datetime, respectively.
  pctl['field_type'] = False

  # Report is not written when False (i.e. keeps unit test report small).
  pctl['write_report'] = True

  # Set True to read from stdin.
  pctl['stdin'] = False

  # Set True to print the version of this handler and return immediately.
  pctl['version'] = False

  return pctl


def parse_cmd_lines():
  pctl = default_program_control()

  parser = argparse.ArgumentParser(
      description='Read a GeoCSV file and check for conformance against' +
      ' the GeoCSV standard description,' +
      ' see http://geows.ds.iris.edu/documents/GeoCSV.pdf')

  parser.add_argument("--input_resrc", help='Input a URL or filename',
      type=str, required=False)
  parser.add_argument('--verbose',
      help='When true, show metrics for every data line', type=str2bool, default=False)
  parser.add_argument('--octothorp',
      help='When true, show metrics for lines with # after initial start of data lines',
      type=str2bool, default=False)
  parser.add_argument('--unicode',
      help='When true, show metrics for lines with unicode',
      type=str2bool, default=False)
  parser.add_argument('--null_fields',
      help='When true, show metrics for lines if any field is null',
      type=str2bool, default=False)
  parser.add_argument('--field_type',
      help='When true, show metrics for lines if any field does not match its ' +
      'respective field_type, i.e. integer, float, or datetime',
      type=str2bool, default=False)
  parser.add_argument('--write_report',
      help='Do not write report lines when false, this is used to make ' +
      'succinct unit test reports, but may be useful in a pipline workflow)',
      type=str2bool, default=True)
  # 'store_true' is builtin action that set parameter to true if it exist on the
  # command line without an argument
  parser.add_argument('--STDIN',
      help='When parameter exist, read data from stdin', action='store_true')
  parser.add_argument('--version',
      help='When parameter exist, return only version, no report', action='store_true')

  args = parser.parse_args()

  pctl['input_resrc'] = args.input_resrc
  pctl['input_bytes'] = None
  pctl['verbose'] = args.verbose
  pctl['octothorp'] = args.octothorp
  pctl['unicode'] = args.unicode
  pctl['null_fields'] = args.null_fields
  pctl['field_type'] = args.field_type
  pctl['write_report'] = args.write_report
  pctl['stdin'] = args.STDIN
  pctl['version'] = args.version

  return pctl

if __name__ == "__main__" \
   or __name__ == "GeocsvValidate" \
   or __name__ == "validator.GeocsvValidate":

  pctl = parse_cmd_lines()
  validateObj = GeocsvValidator(sys.stdout)
  validateObj.doReport(pctl)
