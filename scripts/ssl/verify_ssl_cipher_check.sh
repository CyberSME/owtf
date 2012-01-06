#!/usr/bin/env bash
# Description:
#       Script to extract the most security relevant details from a 
#       target SSL/TLS implementation by using ssl-cipher-check.
# 
# Requires: 
# - ssl-cipher-check.pl
# http://unspecific.com/ssl/
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
 
VERSION=0.1
 
echo ------------------------------------------------------
echo " $0 - ($VERSION) based on ssl-cipher-check.pl"
echo " Author: Abraham Aranguren @7a_ http://7-a.org"
echo ------------------------------------------------------
echo
 
if [ $# -ne 3 ]; then 
   echo Usage: $0 IP PORT
   exit
fi
 
SSL_CIPHER_CHECK=$1
HOST=$2
PORT=$3
 
# Added by Abraham: First check the service can actually speak SSL:
SSL_HANDSHAKE_LINES=$((sleep 5 ; echo -e "^C" 2> /dev/null) |  openssl s_client -connect $HOST:$PORT 2> /dev/null | wc -l)
if [ $SSL_HANDSHAKE_LINES -lt 10 ]; then # Handshake failed
	echo
	echo "[*] SSL Checks skipped!: The host $HOST does not appear to speak SSL/TLS on port: $PORT"
	echo
	exit
else # SSL Handshake successful, proceed with check
	echo
	echo "[*] SSL Handshake Check OK: The host $HOST appears to speak SSL/TLS on port: $PORT"
	echo
fi

echo  [*] Analyzing SSL/TLS on $HOST:$PORT ...
echo  [*] Step 1 - sslcan-based analysis
echo 
 
DATE=$(date +%F_%R:%S)
 
echo "[*] ssl-cipher-check-based analysis (for comparison/assurance purposes)"
echo '[*] NOTE: If you get errors below, try running: "apt-get install gnutls-bin"'
 
OUTFILE=ssl_cipher_check_$DATE
LOGFILE=$OUTFILE.log
ERRFILE=$OUTFILE.err

echo
echo [*] Running ssl-cipher-check.pl on $HOST:$PORT...
#ssl-cipher-check.pl -va $HOST $PORT >> $LOGFILE 2>> $ERRFILE
$SSL_CIPHER_CHECK -va $HOST $PORT >> $LOGFILE 2>> $ERRFILE

echo
echo [*] Testing for SSLv2 ...
grep SSLv2 $LOGFILE | grep ENABLED
echo
echo [*] Testing for NULL cipher ...
grep NULL $LOGFILE | grep ENABLED
echo
echo [*] Testing weak ciphers ...
grep ENABLED $LOGFILE | grep WEAK
echo
echo [*] Testing strong ciphers ...
grep ENABLED $LOGFILE | grep STRONG
echo
echo [*] Default cipher: ...
grep -A 1 Default $LOGFILE | grep -v Default| sed 's/  *//'

echo
echo [*] New files created:

find . -size 0 -name '*.err' -delete # Delete empty error files
ls -l $OUTFILE.* # List new files

echo
echo 
echo [*] done
echo
