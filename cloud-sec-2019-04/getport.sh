#!/bin/bash

# Take container name as argument to inspect image to find and output remote ip and port. This script
# is specific to my lab which uses the exposed port 8080/tcp.
# Richard Bradt

# USAGE: ./getport.sh <container_name>

c_name=$1
echo "Got container name: $c_name"

h_ip=$(docker inspect $c_name | jq '.[].NetworkSettings.Ports."8080/tcp"[].HostIP')

if [ "$h_ip" == "null" ]
then
	h_ip=localhost
fi

# Strip double quotations off string
h_ip="${h_ip%\"}"
h_ip="${h_ip#\"}"
echo "IP: $h_ip"

h_port=$(docker inspect $c_name | jq '.[].NetworkSettings.Ports."8080/tcp"[].HostPort')

if [ "$h_port" == "null" ]
then
	echo "Port unassigned"
else
	h_port="${h_port%\"}"
	h_port="${h_port#\"}"
	echo "Port: $h_port"
	echo "URL is http://$h_ip:$h_port"
fi
