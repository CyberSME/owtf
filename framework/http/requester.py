#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;

The Requester module is in charge of simplifying HTTP requests and automatically log HTTP transactions by calling the DB module
'''
import cgi, sys
import httplib, urllib2, urllib
from framework.lib.general import *
from framework.http import transaction#, httplib_to_urllib2

# Intercept raw request trick from: http://stackoverflow.com/questions/6085709/get-headers-sent-in-urllib2-http-request
class MyHTTPConnection(httplib.HTTPConnection):
	def send(self, s):
		global RawRequest
		RawRequest.append(s) # Saving to global variable for Requester class to see
		httplib.HTTPConnection.send(self, s)

class MyHTTPHandler(urllib2.HTTPHandler):
	def http_open(self, req):
		return self.do_open(MyHTTPConnection, req)

class MyHTTPSConnection(httplib.HTTPSConnection):
	def send(self, s):
		global RawRequest
		RawRequest.append(s) # Saving to global variable for Requester class to see
		httplib.HTTPSConnection.send(self, s)

class MyHTTPSHandler(urllib2.HTTPSHandler):
	def https_open(self, req):
		return self.do_open(MyHTTPSConnection, req)

class Requester:
	def __init__(self, Core, Proxy):
		self.Core = Core
		self.Headers = { 'User-Agent' : self.Core.Config.Get('USER_AGENT') }
		self.RequestCountRefused = 0
		self.RequestCountTotal = 0
		self.LogTransactions = True
		self.Proxy = Proxy
		if None == Proxy:
			cprint("WARNING: No outbound proxy selected. It is recommended to use an outbound proxy for tactical fuzzing later")
			self.Opener = urllib2.build_opener(MyHTTPHandler, MyHTTPSHandler)
		else: # All requests must use the outbound proxy
			cprint("Setting up outbound proxy ..")
			IP, Port = Proxy
			ProxyConf = { 'http':'http://'+IP+":"+Port, 'https':'http://'+IP+":"+Port }
			ProxyHandler = urllib2.ProxyHandler(ProxyConf)
			self.Opener = urllib2.build_opener(ProxyHandler, MyHTTPHandler, MyHTTPSHandler) # works except no raw request on https
		urllib2.install_opener(self.Opener)
		#self.mhttplib_to_urllib2 = httplib_to_urllib2.httplib_to_urllib2()
		#response = opener.open('http://www.google.com/')

	def LogTransactions(self, LogTransactions = True):
		Backup = self.LogTransactions
		self.LogTransactions = LogTransactions
		return Backup

	def NeedToAskBeforeRequest(self):
		return not self.Core.PluginHandler.NormalRequestsAllowed() and self.Core.Config.Get('Interactive')

	def ProxyCheck(self):
		if self.Proxy != None and self.Core.PluginHandler.RequestsPossible(): # Verify proxy works! www.google.com might not work in a restricted network, try target URL :)
			URL = self.Core.Config.Get('PROXY_CHECK_URL')
			#if self.NeedToAskBeforeRequest() and 'y' != raw_input("Proxy Check: Need to send a GET request to "+URL+". Is this ok?: 'y'+Enter= Continue, Enter= Abort Proxy Check\n"):
			#	return [ True, "Proxy Check OK: Proxy Check Aborted by User" ]
                	RefusedBefore = self.RequestCountRefused
			cprint("Proxy Check: Avoid logging request again if already in DB..")
			LogSettingBackup = False
			if self.Core.DB.Transaction.IsTransactionAlreadyAdded(URL):
				LogSettingBackup = self.LogTransactions(False)
			Transaction = self.GET(URL)
			if LogSettingBackup:
				self.LogTransactions(LogSettingBackup)
                	RefusedAfter = self.RequestCountRefused
			if RefusedBefore < RefusedAfter: # Proxy is refusing connections
				return [ False, "ERROR: Proxy Check error: The proxy is not listening or is refusing connections" ]
			else:
				return [ True, "Proxy Check OK: The proxy appears to be working" ]
		return [ True, "Proxy Check OK: No proxy is setup or no HTTP requests will be made" ]
	
	def GetHeaders(self):
		return self.Headers

	def SetHeaders(self, Headers):
		self.Headers = Headers

	def SetHeader(self, Header, Value):
		self.Headers[Header] = Value

	def DerivePOST(self, POST = None):
		if '' == POST:
			POST = None
		if None != POST and None == Method:
			POST = urllib.urlencode(POST)
		#if Method == 'PUT':
		#	POST = "data="+POST

	def Request(self, URL, Method = None, POST = None):
		global RawRequest # kludge: necessary to get around urllib2 limitations: Need this to get the exact request that was sent

		RawRequest = [] # Init Raw Request to blank list
		POST = self.DerivePOST(POST)
		Method = DeriveHTTPMethod(Method, POST)
		URL = URL.strip() # Clean up URL
		request = urllib2.Request(URL, POST, self.Headers) # GET request
		if None != Method:
			request.get_method = lambda : Method # kludge: necessary to do anything other that GET or POST with urllib2
		# MUST create a new Transaction object each time so that lists of transactions can be created and process at plugin-level
		self.Transaction = transaction.HTTP_Transaction(self.Core.Timer) # Pass the timer object to avoid instantiating each time	
		self.Transaction.Start(URL, POST, Method, self.Core.IsInScopeURL(URL))
                self.RequestCountTotal += 1 
                try:
                        Response = urllib2.urlopen(request)
			self.Transaction.SetTransaction(True, RawRequest[0], Response)
		except urllib2.HTTPError, Error: # page NOT found
			self.Transaction.SetTransaction(False, RawRequest[0], Error) # Error is really a response for anything other than 200 OK in urllib2 :)
		except urllib2.URLError, Error: # Connection refused?
			ErrorMessage = self.ProcessHTTPErrorCode(Error, URL)
			self.Transaction.SetError(ErrorMessage)
		except IOError:
			ErrorMessage = "ERROR: Requester Object -> Unknown HTTP Request error: "+URL+"\n"+str(sys.exc_info())
			self.Transaction.SetError(ErrorMessage)
		if self.LogTransactions:
			self.Core.DB.Transaction.LogTransaction(self.Transaction) # Log transaction in DB for analysis later and return modified Transaction with ID
		return self.Transaction

	def ProcessHTTPErrorCode(self, Error, URL):
		if str(Error.reason).startswith("[Errno 111]"):
			Message = "ERROR: The connection was refused!"
                	self.RequestCountRefused += 1 
		if str(Error.reason).startswith("[Errno -2]"):
			self.Core.mError.FrameworkAbort("ERROR: cannot resolve hostname!")
		else:
			Message = "ERROR: The connection was not refused, unknown error!"
		cprint(Message)
		ErrorMessage = Message+" (Requester Object): "+URL+"\n"+str(sys.exc_info())
		return ErrorMessage

	def GET(self, URL):
		return self.Request(URL)

	def POST(self, URL, Data):
		return self.Request(URL, 'POST', Data)

	def TRACE(self, URL):
		return self.Request(URL, 'TRACE', None)

	def OPTIONS(self, URL):
		return self.Request(URL, 'OPTIONS', None)

	def HEAD(self, URL):
		return self.Request(URL, 'HEAD', None)

	def DEBUG(self, URL):
		self.BackupHeaders()
		self.Headers['Command'] = 'start-debug'
		Result = self.Request(URL, 'DEBUG', None)
		self.RestoreHeaders()
		return Result

	def PUT(self, URL, Data, ContentType = 'text/plain'):
		self.BackupHeaders()
		#Not working yet. Request is not sent, only the data is:
		#Payload = "data="+Data
		#self.Headers['Content-Type'] = ContentType
		#self.Headers['Content-Length'] = len(Payload)
		#Result = self.Request(URL, Payload, 'PUT')
		#Working (at least request is sent fine):
		self.Headers['Content-Type'] = ContentType
		self.Headers['Content-Length'] = "0"
		Result = self.Request(URL, 'PUT', None)
		self.RestoreHeaders()
		return Result

	def BackupHeaders(self):
		self.HeadersBackup = dict.copy(self.Headers)

	def RestoreHeaders(self):
		self.Headers = dict.copy(self.HeadersBackup)

	def GetTransaction(self, UseCache, URL, Method = '', Data = ''):
		Criteria = { 'URL' : URL, 'Method' : Method, 'Data' : Data } 
		if not UseCache or not self.Core.DB.Transaction.IsTransactionAlreadyAdded(Criteria): # Visit URL if not already visited
			if Method in [ '', 'GET', 'POST', 'HEAD', 'TRACE', 'OPTIONS' ]:
				return self.Request(URL, Method, Data)
			elif Method == 'DEBUG':
				return self.DEBUG(URL)
			elif Method == 'PUT':
				return self.PUT(URL, Data)
		else: # Retrieve from DB = faster
			return self.Core.DB.Transaction.GetFirst(Criteria)

	def GetTransactions(self, UseCache, URLList, Method = '', Data = ''):
		Transactions = []
		for URL in URLList:
			URL = URL.strip() # Clean up the URL first
			if not URL: continue # skip blank lines 
			if not self.Core.DB.URL.IsURL(URL): 
				self.Core.Error.Add("Minor issue: "+str(URL)+" is not a valid URL and has been ignored, processing continues")
				continue # Skip garbage URLs
			Transactions.append(self.GetTransaction(UseCache, URL, Method, Data))
		return Transactions
"""
# Fighting with httplib: server headers are lowercased and shuffled!:
	def TRACE(self, Hostname, Path):
		global RawRequest # kludge: necessary to get around urllib2 limitations: Need this to get the exact request that was sent

		connection = httplib.HTTPConnection(Hostname) 
		connection.request("TRACE", Path) 
		self.Transaction.Start(Path, Path, "TRACE")
		try:
			Response = connection.getresponse()
			self.mhttplib_to_urllib2.Sethttplib_Response(Response)
			#p(Response)
#['__doc__', '__init__', '__module__', '_check_close', '_method', '_read_chunked', '_read_status', '_safe_read', 'begin', 'chunk_left', 'chunked', 'close', 'debuglevel', 'fp', 'getheader', 'getheaders', 'isclosed', 'length', 'msg', 'read', 'reason', 'status', 'strict', 'version', 'will_close']
			#print str([ Response._method, Response.getheaders(), Response.msg, Response.read(), Response.reason, Response.status, Response.version ])
			self.Transaction.SetTransaction(None, RawRequest, self.mhttplib_to_urllib2)
		except IOError:
			ErrorMessage = "Requester Object -> Unknown HTTP Request error: "+URL+"\n"+str(sys.exc_info())
			self.Transaction.SetError(ErrorMessage)
		self.Core.DB.Transaction.LogTransaction(self.Transaction) # Log transaction in DB for analysis later and return modified Transaction with ID
		return self.Transaction
"""

