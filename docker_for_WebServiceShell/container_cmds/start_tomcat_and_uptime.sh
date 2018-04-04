#!/bin/bash

/docker_run/introduce.sh

# dynamic modification to use the current hostname in log file names
mkdir logs/${HOSTNAME}
# adjust respective files to enable writing logs into the newly made hostname folder
sed -e "s/\[\[HOSTNAME\]\]/${HOSTNAME}/" /wss_config/geows.geocsv.1-log4j.properties_input > /wss_config/geows.geocsv.1-log4j.properties
sed -e "s/\[\[HOSTNAME\]\]/${HOSTNAME}/" conf/logging.properties_input > conf/logging.properties
sed -e "s/\[\[HOSTNAME\]\]/${HOSTNAME}/" conf/server.xml_input > conf/server.xml
sed -e "s/\[\[HOSTNAME\]\]/${HOSTNAME}/" bin/catalina.sh_input > bin/catalina.sh

# run tomcat
bin/startup.sh

# run indefinitely, else the script ends and the docker container exits
echo "--------- started tomcat, uptime, sleeping 60 seconds forever"
while true; do echo -n "${HOSTNAME}  " ; uptime ; sleep 60; done