# GeoCSV Validator

A command line tool for validating GeoCSV content. There is also a prototype server for testing the command line tool.

- 2018-01-31 - current version loaded into iris-edu


##  Contents by folder

Folder |  Description
--------------- | --------------------------
validator | the command line tool
service | trial tornado service
test | unit test

## Running the validator from command line

The current version is can be used as follows:

``` bash
./GeocsvValidator.py

usage: GeocsvValidator.py [-h] --input_url INPUT_URL [--verbose VERBOSE]
                          [--octothorp OCTOTHORP] [--unicode UNICODE]
                          [--null_fields NULL_FIELDS]
                          [--write_report WRITE_REPORT]

./GeocsvValidator.py --input_url 'http://service.iris.edu/irisws/availability/1/extent?network=IU&station=ANMO&format=geocsv'
# this run will show 174 lines read and a validation of False because at least one field is null, in this particular case 63 fields are null.

```

## Running the tornado server

``` bash
./
geocsvTornadoService.py

# by default, the service is listening on port 8989
# and will refer to http://localhost:8988 for documentation.

# These environmental variable maybe used to set alternative values,
# GEOCSV_LISTENING_PORT and GEOCSV_DOCUMENT_URL

# When the server is running, the following features are links are currently active.
http://localhost:8989/geows/geocsv/1/validate?input_url=http://service.iris.edu/irisws/availability/1/extent?network=IU%26station=ANMO%26format=geocsv

http://localhost:8989/geows/geocsv/1/version

http://localhost:8989/geows/geocsv/1/vforms
```

## Docker

``` bash
# use this script to build the docker image
./build_geocsv_vali.bash

# to run
docker run -ti -p 8989:8989 --name geocsv_vali geocsv_vali:v1
```
