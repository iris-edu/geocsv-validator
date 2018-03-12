#!/bin/bash

docker stop -t 0 geocsv_validator
docker rm geocsv_validator
docker rmi geocsv_validator:v1
docker build --tag geocsv_validator:v1 .
docker save --output geocsv_validator_v1.tar geocsv_validator:v1

echo
echo "***********************"
echo "*********************** finished image"
echo "***********************"
echo

