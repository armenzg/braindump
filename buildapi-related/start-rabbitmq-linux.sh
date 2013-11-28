#!/bin/sh
set -e
sudo invoke-rc.d rabbitmq-server restart
sudo rabbitmqctl stop_app
sudo rabbitmqctl reset
sudo invoke-rc.d rabbitmq-server restart
sudo rabbitmqctl add_user buildapi buildapi
sudo rabbitmqctl set_permissions buildapi '.*' '.*' '.*'
sudo invoke-rc.d rabbitmq-server restart 
