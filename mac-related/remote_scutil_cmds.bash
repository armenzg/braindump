#!/bin/bash
# This script is used to reset the HostName and LocalHostName
# of a remote Mac via sshsudo[1]. Having these values unset can
# sometimes cause puppet to fail at boot. This seems to happen 
# reasonably frequently with lion (OS X 10.7).
# 
# Invocation looks something like this:
# 
# Single host:
#  sshsudo -v -r -u cltbld talos-r4-lion-001.build.scl1.mozilla.com \
#    remote_scutil_cmds.bash
# 
# Multiple hosts:
#  sshsudo -v -r -u cltbld hostlist.file remote_scutil_cmds.bash
# ...where hostlist.file contains a list (one per line) of the hosts
# to run on.
# 
# 1. https://code.google.com/p/sshsudo/

ip=`ifconfig | grep 'inet 10' | cut -f2 | cut -f2 -d' '`
fqdn=`host $ip | cut -f5 -d' ' | sed 's/\.$//'`
shortname=`echo $fqdn | cut -d'.' -f1`

scutil --set HostName $fqdn
scutil --set LocalHostName $shortname
scutil --get HostName
scutil --get LocalHostName

