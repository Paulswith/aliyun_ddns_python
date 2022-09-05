#!/bin/bash

debug=0
export DDNS_LOG_LEVEL=WARN
logf=/var/log/aliyun-ddns.log
foip=/root/tasks/ddns/last_ip
pppoe_ether='pppoe-wan'
oip=$(cat $foip)
#nip=$(ip addr | grep -A 10 'pppoe-wan' | grep inet | grep -oE '([0-9]{1,3}[.]){3}[0-9]{1,3} ' | sed 's/ *$//g')
nip=$(ip addr  | grep -A 5 $pppoe_ether | grep inet | grep -oE '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' | head -n 1)

[[ $debug == 1 ]] && echo "new-ip='$nip', old-ip='$oip'"
if [[ "$oip" != "$nip" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] invoke update new-public-ip => $nip" >> $logf
        /usr/bin/python3 ./update-ddns.py $nip >> $logf 2>&1
        echo "$nip" > $foip
else
        [[ $debug == 1 ]] && echo "ip not change, skip"
fi