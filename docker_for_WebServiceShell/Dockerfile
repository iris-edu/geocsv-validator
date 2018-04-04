# Create an image for enpoint geows-uf/imag2
#

FROM tomcat:8.0.41-jre8

RUN apt-get update && apt-get -y install vim

## optionally, install jdk to get jar command - 
## apt-get -y install openjdk-8-jdk

RUN apt-get update \
  && apt-get -y install netcat \
  && apt-get -y install telnet \
  && apt-get -y install dnsutils \
  && apt-get -y install tcpdump \
  && apt-get -y install net-tools \
  && apt-get -y install iputils-ping

RUN apt-get update \
  && apt-get -y install perl \
  && apt-get -y install libwww-perl \
  && apt-get -y install libdbi-perl \
  && apt-get -y install libdbd-pg-perl

##RUN apt-get update \
##  && apt-get -y install python \
##  && apt-get -y install python-lxml \
##  && apt-get -y install python-setuptools  \
##  && apt-get install -y python-pip \
##  && apt-get -y install gcc \
##  && apt-get -y install python-dev
##RUN pip install pytz
##RUN pip install psutil

# for python3
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && apt-get install -y python3-dateutil
RUN pip3 install pytz \
  && pip3 install psutil \
  && pip3 install future

ADD wss_config /wss_config
ADD wss_handlers /wss_handlers

# settings here must agree with ADD command for wss_config
ADD tomcat_config/bin/setenv.sh bin/

# support for enabling hostname folder name setting in start script
ADD tomcat_config/bin/catalina.sh_input bin/
ADD tomcat_config/conf/logging.properties_input conf/
ADD tomcat_config/conf/server.xml_input conf/

ADD war_files/webserviceshell-*-wssapp.war webapps/geows#geocsv#1.war

ADD container_cmds/introduce.sh /container_cmds/
ADD container_cmds/start_tomcat_and_uptime.sh /container_cmds/

EXPOSE 8080
CMD ["/container_cmds/start_tomcat_and_uptime.sh"]

