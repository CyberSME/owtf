#!/usr/bin/env bash
#
# Description:
#       Script to run w3af with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02
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

if [ $# -ne 2 -a $# -ne 3 ]; then
        echo "Usage $0 <tool_dir> <target url> (<user agent -spaces replaced by # symbol->)"
        exit
fi

TOOL_DIR=$1
URL=$2
USER_AGENT="Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0" # Default to something less obvious
if [ $3 ]; then
	USER_AGENT=$(echo $3 | sed 's/#/ /g') # Expand to real User Agent
fi

DATE=$(date +%F_%R:%S | sed 's/:/_/g')
OUTFILE="w3af_report$DATE"
REPORT_HTTP=$OUTFILE.http.txt
REPORT_TXT=$OUTFILE.txt
REPORT_HTML=$OUTFILE.html
W3AF_SCRIPT=$OUTFILE.script.w3af
DIR=$(pwd) # Remember current dir
cd "$TOOL_DIR" # W3AF needs to be run from its own folder

echo "# w3af script used for testing
cleanup
profiles 
use full_audit
back
plugins
bruteforce !basicAuthBrute,!formAuthBrute
discovery webSpider,sharedHosting,allowedMethods,digitSum,content_negotiation,robotsReader,serverStatus,urlFuzzer
output htmlFile,textFile
output config htmlFile
set fileName $REPORT_HTML
back
output config textFile
set httpFileName $REPORT_HTTP
set fileName $REPORT_TXT
back
back
misc-settings
set fuzzFileName True
set fuzzCookie True
set fuzzFormComboValues all
set maxDiscoveryTime 240
back
http-settings
set timeout 60
set userAgent $USER_AGENT
set maxRetrys 3
back
target
set target $URL
back
start
exit
" > $W3AF_SCRIPT
#Redirecting stdout/stderr is messy due to having to use a background tail process with remains hanging if "Control+C"
#echo "./w3af_console -n -s $W3AF_SCRIPT" > $LOG_TXT 2> $ERR_FILE
COMMAND="./w3af_console -n -s $W3AF_SCRIPT"
echo "[*] Running: $COMMAND"
./w3af_console -n -s $W3AF_SCRIPT

mv $OUTFILE* $DIR
cd $DIR # Back to working folder
strings $REPORT_HTTP > $REPORT_HTTP.tmp # Removing binary garbage
mv $REPORT_HTTP.tmp $REPORT_HTTP

echo
echo "[*] Done!]"

#discovery webSpider,sharedHosting,allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,urlFuzzer
#discovery detectReverseProxy,detectTransparentProxy
#discovery archiveDotOrg,bing_spider,dnsWildcard,domain_dot,findDVCS,findGit,fingerBing,fingerPKS,ghdb,phishtank,sharedHosting,xssedDotCom,yahooSiteExplorer,zone_h
#discovery fingerprint_os,frontpage_version,halberd,hmap,oracleDiscovery,phpEggs,phpinfo,pykto,ria_enumerator,dotNetErrors,wordpress_fingerprint,wsdlFinder
#discovery detectReverseProxy,detectTransparentProxy
#discovery archiveDotOrg,bing_spider,dnsWildcard,domain_dot,findDVCS,findGit,fingerBing,fingerPKS,ghdb,phishtank,sharedHosting,xssedDotCom,yahooSiteExplorer,zone_h
#discovery fingerprint_os,frontpage_version,halberd,hmap,oracleDiscovery,phpEggs,phpinfo,pykto,ria_enumerator,dotNetErrors,wordpress_fingerprint,wsdlFinder
#discovery afd,fingerprint_WAF,favicon_identification,findBackdoor,findCaptchas
#discovery allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,sitemapReader,urlFuzzer,userDir
#discovery all,!wordnet <- crap!!
#discovery webSpider,sharedHosting,allowedMethods,digitSum,content_negotiation,dir_bruter,robotsReader,serverStatus,sitemapReader,urlFuzzer
