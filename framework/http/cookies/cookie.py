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

'''
POSSIBLE_ATTRIBUTES = [ 'secure', 'HttpOnly', 'domain', 'path', 'expires' ]
class Cookie:
	def __init__(self):
		pass

	def GetAttributeFromList(self, AttribName, AttribList):
		AttribValue = ""
		for PresentAttrib in CookieAttribs:
			if PresentAttrib.lower().startswith(Attrib.lower()): # Avoid false positives due to cookie contents
				AttribValue = PresentAttrib
				break
		return AttribValue

	def GetPossibleAttributes(self):
		return POSSIBLE_ATTRIBUTES

        def CreateFromStr(self, CookieStr):
		self.Name = CookieStr.split('=')[0]
		CookieAttribs = Cookie.replace(CookieName+"=", "").replace("; ", ";").split(";")
                self.Value = ""
		if CookieAttribs[0]:
                	self.Value = CookieAttribs[0]
			CookieAttribs = CookieAttribs[1:] # Remove value item from Attribute list to avoid issues below
		# Creating attributes as members for readability elsewhere in the code:
		self.Secure = self.GetAttributeFromList('secure', CookieAttribs)
		self.HttpOnly = self.GetAttributeFromList('HttpOnly', CookieAttribs)
		self.Domain = self.GetAttributeFromList('domain', CookieAttribs)
		self.Path = self.GetAttributeFromList('path', CookieAttribs)
		self.Expires = self.GetAttributeFromList('expires', CookieAttribs)
		# Creating attribute dictionary for ease of lookup and comparisons
		self.Attribs = { 'secure' : self.Secure, 'HttpOnly' : self.HttpOnly, 'domain' : self.Domain, 'path' : self.Path, 'expires' : self.Expires }

