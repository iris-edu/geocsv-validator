#!/bin/bash

docker stop -t 0 geocsv_vali
docker rm geocsv_vali
docker rmi geocsv_vali:v1
docker build --tag geocsv_vali:v1 .
docker save --output geocsv_vali_v1.tar geocsv_vali:v1

echo
echo "***********************"
echo "*********************** finished image"
echo "***********************"
echo

