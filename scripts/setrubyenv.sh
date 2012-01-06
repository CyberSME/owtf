#!/usr/bin/env bash
#
# Description:
# Some tools (whatweb and others) require ruby 1.8 and others (i.e. BeEF) require ruby 1.9.2
# This script allows you to quickly change from ruby 1.8 to 1.9.2 and viceversa
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

if [ $# -ne 1 ]; then
	echo "Syntax: $0 <ruby_version: 1.8, 1.9.2>"
	echo 
	echo "Examples:"
	echo "- Set ruby 1.8: $0 1.8"
	echo "- Set ruby 1.9.2: $0 1.9.2"
	exit
fi

VERSION=$1
echo $VERSION

OPTION="1"
if [ '1.9.2' == $VERSION ]; then
	OPTION="2"
fi

# Export version gem paths
export GEM_PATH=/var/lib/gems/$VERSION/gems
export GEM_HOME=/var/lib/gems/$VERSION/gems
# Pick ruby version
#(sleep 2 ; echo $OPTION) | update-alternatives --config ruby > /dev/null
(sleep 2 ; echo $OPTION) | update-alternatives --config ruby
