# Setup a python environment to run geocsv-validator

# 2018-01-31
# original from https://hub.docker.com/r/frolvlad/alpine-python3/~/dockerfile/

FROM alpine:3.7

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN pip install pytz && pip install future && pip install tornado

ADD validator/  /geocsv_vali/validator/
ADD service/ /geocsv_vali/service/

# run python unbuffered so as to see output in docker logs ...
CMD ["python", "-u", "/geocsv_vali/service/geocsvTornadoService.py"]

# docker build --tag geocsv_vali:v1 .

# to run in defalt mode, expose default tornado port 8989 as externl 8989
# docker run -ti -p 8989:8989 --name geocsv_vali geocsv_vali:v1
#
# to manage port and document URL
# expose (to external) port 8989 from configured (in tornado) port 8950
# docker run -ti -p 8989:8950 --env GEOCSV_LISTENING_PORT='8950' --env GEOCSV_DOCUMENT_URL='http://cube1:8988' --name geocsv_vali geocsv_vali:v1
# or as daemon
# docker run -d ...
# 
# get version information
# curl localhost:8950/geows/geocsv/1/version
#
# see forwarding request for documentation
# curl -v localhost:8950/geows/geocsv/1/
#
# to move an image, make a tar file, copy, and load it on target server
# docker save --output geocsv_vali_v1.tar geocsv_vali:v1
# docker load < geocsv_vali_v1.tar
