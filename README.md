# GeoCSV Validator

A command line tool for validating GeoCSV content. There is also a prototype server for testing the command line tool.

- 2018-01-31 - current version loaded into iris-edu
- 2018-03-15 - version 0.93,
  - added field_type check
  - added version method
  - added runaway limit check at 1,000,000,000 bytes
  - added ability to read file rather than thru file://, breaking change to API, input_url changed to input_resrc
  - update some messages, add timestamp to tornado log messages, and control env variables
  - add validate of multiple GeoCSV data sets in same stream

## Concept of operation:

GeocsvValidator.py will read content from the resource specified with --input_resrc. By default, a short report is output showing whether the input is validated or not. Additionally, counts of other properties like null fields, type mismatch, etc. are provided in a "metrics" line.

This validator does not count null fields as a failure-to-validate as this may be allowed for a given dataset. However, if it is desired to identify lines with null_fields, setting option --null_fields to true will cause those lines to be output.

The option to show UNICODE is a side affect of creating this program to run on both python 2 and 3. The module csv.reader is used to input lines of data and this module behaves differently in respective python versions. For consistent operation, this validator will force input characters to ASCII if csv.reader has an exception processing UNICODE characters.

##  Contents by folder

Folder |  Description
--------------- | --------------------------
validator | the command line tool
service | prototype tornado service
test | unit test

## Running the validator from command line

The current version can be used as follows:

``` bash
./GeocsvValidator.py

usage: GeocsvValidator.py [-h] --input_resrc INPUT_RESRC [--verbose VERBOSE]
                          [--octothorp OCTOTHORP] [--unicode UNICODE]
                          [--null_fields NULL_FIELDS]
                          [--field_type FIELD_TYPE]
                          [--write_report WRITE_REPORT]

Read a GeoCSV file and check for conformance against the GeoCSV standard
description, see http://geows.ds.iris.edu/documents/GeoCSV.pdf

optional arguments:
  -h, --help            show this help message and exit
  --input_resrc INPUT_RESRC
                        Input a URL or filename
  --verbose VERBOSE     When true, show metrics for every data line
  --octothorp OCTOTHORP
                        When true, show metrics for lines with "#" after initial
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


./GeocsvValidator.py --input_resrc 'http://service.iris.edu/irisws/availability/1/extent?network=IU&station=ANMO&format=geocsv'
# this run will show 174 lines read and a validation of False because at least one field is null, in this particular case 63 fields are null.

```

## Running the tornado server

``` bash
./geocsvTornadoService.py

# by default, the service is listening on port 8989
# and will refer to http://localhost:8988 for documentation.

# These environmental variable maybe used to set alternative values,
# GEOCSV_LISTENING_PORT and GEOCSV_DOCUMENT_URL

# When the server is running, the following features are links are currently active.
Sample queries

http://localhost:8989/geows/geocsv/1/validate?input_resrc=http://service.iris.edu/irisws/availability/1/extent?network=IU%26station=ANMO%26format=geocsv

http://localhost:8989/geows/geocsv/1/validate?input_resrc=http://service.iris.edu/fdsnws/station/1/query?level=station%26format=geocsv%26includecomments=true%26nodata=404

http://localhost:8989/geows/geocsv/1/version

http://localhost:8989/geows/geocsv/1/vforms
```

## Docker

``` bash
# use this script to build the docker image
./build_geocsv_validator.bash

# to run locally and expose the internal, default port 8989 as external 8989
docker run -ti -p 8989:8989 --name geocsv_validator geocsv_validator:v1

# to deploy when a documentation service is available and change the
# default port tornado starts on to 8950
#
# GEOCSV_LISTENING_PORT will configure tornado to listen on 8950
# -p 8989:8950 will expose the container at port 8989 using the tornado port defined by GEOCSV_LISTENING_PORT
# GEOCSV_DOCUMENT_URL defines the URL for a documentation service when http://localhost:8989/geows/geocsv/1/ is requested or any other un-routed URL
sudo docker run -d -p 8989:8950 --env GEOCSV_LISTENING_PORT='8950' --env GEOCSV_DOCUMENT_URL='http://cube1:8988' --name geocsv_validator geocsv_validator:v1



```
