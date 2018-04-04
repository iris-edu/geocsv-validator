#!/bin/bash

docker stop -t 0 geocsv_validator_tornado
docker rm geocsv_validator_tornado
docker rmi geocsv_validator_tornado:v1

ADD validator/  /geocsv_validator/validator/
ADD service/ /geocsv_validator/service/

mkdir -p validator
cp ../validator/GeocsvValidator.py validator

mkdir -p service
cp ../service/geocsvTornadoService.py service

docker build --tag geocsv_validator_tornado:v1 .

# # expose tomcat port 8989 as external 8993
docker run -d -p 8993:8989 --name geocsv_validator_tornado geocsv_validator_tornado:v1

