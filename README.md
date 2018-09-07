# GeoCSV Validator

A command line tool for validating GeoCSV content. There is also a prototype server for testing the command line tool.

- 2018-01-31 - current version loaded into iris-edu
- 2018-03-15 - version 0.93
  - added field_type check
  - added version method
  - added runaway limit check at 1,000,000,000 bytes
  - added ability to read file rather than thru file://, breaking change to API, input_url changed to input_resrc
  - update some messages, add timestamp to tornado log messages, and control env variables
  - add validate of multiple GeoCSV data sets in same stream
- 2018-04-06 - version 0.94
  - remove Docker folders
  - reset size limit to 400 MB, 4 times current channel metadata size
  - add reading from stdin when --STDIN parameter present
  - small changes to report messages
- 2018-06-29
  - add OpenAPI 3 spec
- 2018-09-07 - removed the tornado service


GeocsvValidator.py reads content from the resource specified with parameter
**input_resrc**. A short report shows validation results. Additionally, counts
of other properties like null fields, type mismatch, etc. are provided.

This validator does not count null fields as a failure. However, to identify lines
with null_fields, set parameter **null_fields** to true to report lines with null fields.

The csv.reader module used in this code behaves differently
between python 2 and 3 on UNICODE characters. For consistent behavior, UNICODE
characters are treated like ASCII. To see lines which contain of UNICODE
characters, use and the **unicode** parameter.

##  Contents by folder

Folder |  Description
--------------- | --------------------------
validator | the command line tool
test | unit test

## Running the validator from command line

The current version can be used as follows:

``` bash
validator/GeocsvValidator.py -h
usage: GeocsvValidator.py [-h] [--input_resrc INPUT_RESRC] [--verbose VERBOSE]
                         [--octothorp OCTOTHORP] [--unicode UNICODE]
                         [--null_fields NULL_FIELDS]
                         [--field_type FIELD_TYPE]
                         [--write_report WRITE_REPORT] [--STDIN] [--version]

Read a GeoCSV file and check for conformance against the GeoCSV standard
description, see http://geows.ds.iris.edu/documents/GeoCSV.pdf

optional arguments:
 -h, --help            show this help message and exit
 --input_resrc INPUT_RESRC
                       Input a URL or filename
 --verbose VERBOSE     When true, show metrics for every data line
 --octothorp OCTOTHORP
                       When true, show metrics for lines with # after initial
                       start of data lines
 --unicode UNICODE     When true, show metrics for lines with unicode
 --null_fields NULL_FIELDS
                       When true, show metrics for lines if any field is null
 --field_type FIELD_TYPE
                       When true, show metrics for lines if any field does
                       not match its respective field_type, i.e. integer,
                       float, or datetime
 --write_report WRITE_REPORT
                       Do not write report lines when false, this is used to
                       make succinct unit test reports, but may be useful in
                       a pipline workflow)
 --STDIN               When parameter exist, read data from stdin
 --version             When parameter exist, return only version, no report

validator/GeocsvValidator.py --input_resrc 'http://service.iris.edu/irisws/availability/1/extent?network=IU&station=ANMO&format=geocsv'
# this run will show 174 lines read and a validation of False because at least one field is null, in this particular case 63 fields are null.

```
