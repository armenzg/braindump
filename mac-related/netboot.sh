#!/bin/bash

hostname=$1
domain=`host ${hostname} | grep 'has address' | cut -d' ' -f1 | cut -d'.' -f2-`

case "${domain}" in
  "relabs.releng.scl3.mozilla.com") cmd="/usr/sbin/bless --netboot --server bsdp://10.26.52.17; reboot"
                                    ;;
  "srv.releng.scl3.mozilla.com")    cmd="/usr/sbin/bless --netboot --server bsdp://10.26.52.17; reboot"
                                    ;;
  "build.releng.scl3.mozilla.com")  cmd="/usr/sbin/bless --netboot --server bsdp://10.26.52.17; reboot"
                                    ;;
  "try.releng.scl3.mozilla.com")    cmd="/usr/sbin/bless --netboot --server bsdp://10.26.52.17; reboot"
                                    ;;
  "test.releng.scl3.mozilla.com")   cmd="/usr/sbin/bless --netboot --server bsdp://10.26.56.110; reboot"
                                    ;;
  "qa.scl3.mozilla.com")            cmd="/usr/sbin/bless --netboot --server bsdp://10.22.73.45; reboot"
                                    ;;
  *)                                echo "Unknown domain: ${domain}"
                                    exit 1;;
esac

echo "Running ssh root@${hostname} \"${cmd}\""
ssh root@${hostname} "${cmd}"
