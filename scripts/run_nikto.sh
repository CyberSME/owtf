#!/usr/bin/env bash
#
# Description:
#       Script to run nikto with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02
# Version: 2.0
#
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright 
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the <organization> nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#

if [ $# -ne 2 -a $# -ne 3 -a $# -ne 4 ]; then
        echo "Usage $0 <tool_dir> <target_ip> (<target_port>) (<target hostname>)"
	echo "Tip: Change the USER_AGENT on nikto.conf to something normal.."
        exit
fi

PORT=80
if [ $3 ]; then
        PORT=$3
fi

TOOL_DIR=$1
IP=$2
HOST_NAME=$ip
NIKTO_NOLOOKUP="-nolookup"
if [ $4 ] && [ "$4" != "$ip" ]; then
        HOST_NAME=$4
        NIKTO_NOLOOKUP="" #Host name passed: must look up
fi

NIKTO_SSL=""
SSL_HANDSHAKE_LINES=$((sleep 5 ; echo -e "^C" 2> /dev/null) |  openssl s_client -connect $HOST_NAME:$PORT 2> /dev/null | wc -l)
if [ $SSL_HANDSHAKE_LINES -gt 10 ]; then # SSL Handshake successful, proceed with nikto -ssl switch
        NIKTO_SSL="-ssl"
fi

DATE=$(date +%F_%R:%S | sed 's/:/_/g')
OUTFILE="nikto$DATE"
LOG_XML=$OUTFILE.xml
DIR=$(pwd) # Remember current dir
cd "$TOOL_DIR" # Nikto needs to be run from its own folder
COMMAND="./nikto.pl $NIKTO_NOLOOKUP -evasion 1 $NIKTO_SSL -host $HOST_NAME -port $PORT -output $DIR/$LOG_XML -Format xml"
echo "[*] Running: $COMMAND"
$COMMAND

echo
echo "[*] Done!]"
