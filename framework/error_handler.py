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

The time module allows the rest of the framework to time how long it takes for certain actions to execute and present this information in both seconds and human-readable form
'''
import traceback, sys, cgi
from framework.lib.general import *

class ErrorHandler:
	Command = ''
	PaddingLength = 100

	def __init__(self, CoreObj):
		self.Core = CoreObj
		self.Padding = "\n" + "_" * self.PaddingLength + "\n\n"
		self.SubPadding = "\n" + "*" * self.PaddingLength + "\n"

	def SetCommand(self, Command):
		self.Command = Command

	def FrameworkAbort(self, Message, Report = True):
		Message = "Aborted by Framework: "+Message
		cprint(Message)
		self.Core.Finish(Message, Report)
		return Message

        def UserAbort(self, Level, PartialOutput = ''): # Levels so far can be Command or Plugin
                Message = cprint("\nThe "+Level+" was aborted by the user: Please check the report and plugin output files")
                Options = ""
                if 'Command' == Level:
                	Options = ", 'p'+Enter= Move on to next plugin"
                Option = raw_input("Options: 'e'+Enter= Exit"+Options+", Enter= Next test\n")
                if 'e' == Option:
			if 'Command' == Level: # Try to save partial plugin results
				raise FrameworkAbortException(PartialOutput)
                        self.Core.Finish("Aborted by user") # Interrupted
                elif 'p' == Option: # Move on to next plugin
                        raise PluginAbortException(PartialOutput) # Jump to next handler and pass partial output to avoid losing results
                return Message

	def LogError(self, Message):
		try:
			self.Core.DB.AddError(Message) # Log error in the DB
		except AttributeError:
			cprint("ERROR: DB is not setup yet: cannot log errors to file!")

	def AddOWTFBug(self, Message):
		exc_type, exc_value, exc_traceback = sys.exc_info()
		ErrorTrace = "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
		#traceback.print_exc()
		#print repr(traceback.format_stack())
		#print repr(traceback.extract_stack())
		Output = self.Padding+"OWTF BUG: Please report the sanitised information below to help make this better. Thank you."+self.SubPadding
		Output += "\nMessage: "+Message+"\n"
		Output += "\nCommand: "+self.Command+"\n"
		Output += "\nError Trace:"
		Output += "\n"+ErrorTrace
		Output += "\n"+self.Padding
		cprint(Output)
		self.LogError(Output)
		return "<pre>"+cgi.escape(Output)+"</pre>"
#TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/

	def Add(self, Message, BugType = 'owtf'):
		if 'owtf' == BugType:
			return self.AddOWTFBug(Message)
		else:
			Output = self.Padding+Message+self.SubPadding
			cprint(Output)
			self.LogError(Output)

