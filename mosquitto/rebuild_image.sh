#!/bin/bash

docker images
read -p "Enter the IMAGE ID that you want to remove: " hash
docker rmi -f "$hash"
sudo chown -R "$(whoami)" .
#docker-compose up

