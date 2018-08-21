#!/bin/bash

if [ -z "$*" ]; then
    echo "*****"
    echo "Enter one or more function names:"
    echo "** These set host and port."
    echo "    setlocal - localhost:8995"
    echo "    setgeows - geows.ds.iris.edu:80"
    echo "    setservice - service.iris.edu"
    echo "    showtestdata - show GeoCSV data used in these test"
    echo "** NOTE: these require setting host and port, e.g. setlocal setex"
    echo "    showokreport - show a successful report from GeoCSV data"
    echo "    showerr1 - bad parameter"
    echo "    showerr2 - bad host name"
    echo "    showerr3 - bad service name"
    echo "*****"

    exit 0
else
    FUNCTIONS="$*"
fi

main () {
  setup
  for f in $FUNCTIONS;
  do
    lines_of_1_burst "running function ${f}";
    $f;
    lines_of_1_burst "finished function ${f}";
  done
}

setup(){
  geocsvTestData="http://service.iris.edu/fdsnws/station/1/query?level=station&format=geocsv&includecomments=true&nodata=404"

  # to pass a URL as a parameter in a URL, any & must be set to %26
  goodgeocsv=`echo "${geocsvTestData}" | sed -e "s/&/%26/g"`
  badServiceName=`echo "${geocsvTestData}" | sed -e "s/&/%26/g" -e "s/\/station\//\/badservice\//"`
  badHostName=`echo "${geocsvTestData}" | sed -e "s/&/%26/g" -e "s/.iris./.badhost./"`
  badParam=`echo "${geocsvTestData}" | sed -e "s/&/%26/g" -e "s/level=/badparam=/"`
}

setlocal(){
  host=localhost
  port=8995
  echo "host:port: ${host}:${port}"
}

setService(){
  host=service.iris.edu
  port=80
  echo "host:port: ${host}:${port}"
}

setgeows(){
  host=geows.ds.iris.edu
  port=80
  echo "host:port: ${host}:${port}"
}

showtestdata(){
  curl "${geocsvTestData}"
}

showokreport(){
  curl "http:///${host}:${port}/geows/geocsv/1/validate?input_resrc=${goodgeocsv}"
}

showerr1(){
  lines_of_1_burst "showing output from bad parameter";
  curl "${badParam}"
  lines_of_1_burst "showing validator output from bad parameter";
  curl "http://${host}:${port}/geows/geocsv/1/validate?input_resrc=${badParam}"
}

showerr2(){
  lines_of_1_burst "showing output from bad host name";
  curl "${badHostName}"
  lines_of_1_burst "showing validator output from bad host name";
  curl "http:///${host}:${port}/geows/geocsv/1/validate?input_resrc=${badHostName}"
}

showerr3(){
  lines_of_1_burst "showing head of html of output from bad service name";
  curl "${badServiceName}" | head
  lines_of_1_burst "showing validator output from bad service name";
  curl "http:///${host}:${port}/geows/geocsv/1/validate?input_resrc=${badServiceName}"
}

lines_of_1_burst() {
  echo "*********************** $1"
}

lines_of_5_burst() {
  echo
  echo "***********************"
  echo "*********************** $1"
  echo "***********************"
  echo
}

main