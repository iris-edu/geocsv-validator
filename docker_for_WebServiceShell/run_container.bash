#!/bin/bash

docker stop -t 0 geocsv_validator_wss
docker rm geocsv_validator_wss
docker rmi geocsv_validator_wss:v1

mkdir -p wss_handlers
cp ../validator/GeocsvValidator.py wss_handlers

docker build --tag geocsv_validator_wss:v1 .

# expose tomcat port 8080 as external 8995
docker run -d -p 8995:8080 --name geocsv_validator_wss geocsv_validator_wss:v1

