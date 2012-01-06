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

Description:
The core is the glue that holds the components together and allows some of them to communicate with each other
'''
import os, re
from framework import timer, shell, error_handler, random
from framework.config import config
from framework.http import requester
from framework.db import db
from framework.plugin import plugin_handler, plugin_helper, plugin_params
from framework.report import reporter, summary
from framework.selenium import selenium_handler
from framework.lib.general import *
from collections import defaultdict

class Core:
	def __init__(self, RootDir):
		cprint("Loading framework please wait..")
		# Tightly coupled, cohesive framework components:
		self.Error = error_handler.ErrorHandler(self)
		self.Shell = shell.Shell(self) # Config needs to find plugins via shell = instantiate shell first
		self.Config = config.Config(RootDir, self)
		self.Config.Init() # Now the the config is hooked to the core, init config sub-components
		self.PluginHelper = plugin_helper.PluginHelper(self) # Plugin Helper needs access to automate Plugin tasks
		self.Random = random.Random()
		self.IsIPInternalRegexp = re.compile("^127.\d{123}.\d{123}.\d{123}$|^10.\d{123}.\d{123}.\d{123}$|^192.168.\d{123}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{123}.[0-9]{123}$")
		self.Reporter = reporter.Reporter(self) # Reporter needs access to Core to access Config, etc
		self.Selenium = selenium_handler.Selenium(self)

        def IsInScopeURL(self, URL): # To avoid following links to other domains
		URLHostName = URL.split("/")[2]
		for HostName in self.Config.GetAll('HOST_NAME'): # Get all known Host Names in Scope
			if URLHostName == HostName:
				return True
		return False

	def CreateMissingDirs(self, Path):
		Dir = os.path.dirname(Path)
                if not os.path.exists(Dir):
                        os.makedirs(Dir) # Create any missing directories

        def DumpFile(self, Filename, Contents, Directory):
                SavePath=Directory+WipeBadCharsForFilename(Filename)
                self.CreateMissingDirs(Directory)
                with open(SavePath, 'wb') as file:
                        file.write(Contents)
                return SavePath

        def GetPartialPath(self, Path):
		#return MultipleReplace(Path, List2DictKeys(RemoveListBlanks(self.Config.GetAsList( [ 'HOST_OUTPUT', 'OUTPUT_PATH' ]))))
		#print str(self.Config.GetAsList( [ 'HOST_OUTPUT', 'OUTPUT_PATH' ] ))
		#print "Path before="+Path
		Path = MultipleReplace(Path, List2DictKeys(RemoveListBlanks(self.Config.GetAsList( [ 'OUTPUT_PATH' ]))))
		#print "Path after="+Path
		if '/' == Path[0]: # Stripping out leading "/" if present
			Path = Path[1:]
		return Path

	def GetCommand(self, argv):
		# Format command to remove directory and space-separate arguments
		return " ".join(argv).replace(os.path.dirname(argv[0])+"/", '') 

	def AnonymiseCommand(self, Command):
		for Host in self.Config.GetAll('HOST_NAME'): # Host name setting value for all targets in scope
			if Host: # Value is not blank
				Command.replace(Host, 'some.target.com')
		return Command

	def Start(self, Options):
		self.PluginHandler = plugin_handler.PluginHandler(self, Options)
		self.Config.ProcessOptions(Options)
		self.PluginParams = plugin_params.PluginParams(self, Options)
		self.Timer = timer.Timer(self.Config.Get('DATE_TIME_FORMAT'))
		if Options['ListPlugins']:
			self.PluginHandler.ShowPluginList()
			return False # No processing required, just list available modules
		self.DB = db.DB(self) # DB is initialised from some Config settings, must be hooked at this point
		self.DB.Init()
		Command = self.GetCommand(Options['argv'])
                self.DB.Run.StartRun(Command) # Log owtf run options, start time, etc
		if self.Config.Get('SIMULATION'):
			cprint("WARNING: In Simulation mode plugins are not executed only plugin sequence is simulated")
		self.Requester = requester.Requester(self, Options['Proxy'])
		# Proxy Check
		ProxySuccess, Message = self.Requester.ProxyCheck()
		cprint(Message)
		if not ProxySuccess: # Regardless of interactivity settings if the proxy check fails = no point to move on
			self.Error.FrameworkAbort(Message) # Abort if proxy check failed
		# Each Plugin adds its own results to the report, the report is updated on the fly after each plugin completes (or before!)
		self.Error.SetCommand(self.AnonymiseCommand(Command)) # Set anonymised invoking command for error dump info
		Status = self.PluginHandler.ProcessPlugins()
		if Status['AllSkipped']:
			self.Finish('Complete: Nothing to do')
		elif not Status['SomeSuccessful'] and Status['SomeAborted']:
			self.Finish('Aborted')
			return False
		elif not Status['SomeSuccessful']: # Not a single plugin completed successfully, major crash or something
			self.Finish('Crashed')
			return False
		return True # Scan was successful

	def Finish(self, Status = 'Complete', Report = True):
		if not self.Config.Get('SIMULATION'):
			try:
				cprint("Saving DBs")
				self.DB.Run.EndRun(Status)
		                self.DB.SaveDBs() # Save DBs prior to producing the report :)
				if Report:
					cprint("Finishing iteration and assembling report again (with updated run information)")
					PreviousTarget = self.Config.GetTarget()
					for Target in self.Config.GetTargets(): # We have to finish all the reports in this run to update run information
						self.Config.SetTarget(Target) # Much save the report for each target
			       	         	self.Reporter.ReportFinish() # Must save the report again at the end regarless of Status => Update Run info
					self.Config.SetTarget(PreviousTarget) # Restore previous target
				cprint("owtf iteration finished")
				if self.DB.ErrorCount() > 0: # Some error occurred (counter not accurate but we only need to know if sth happened)
					cprint("Please report the sanitised errors saved to "+self.Config.Get('ERROR_DB'))
			except AttributeError: # DB not instantiated yet!
				cprint("owtf finished: No time to report anything! :P")
			exit()

	def GetSeed(self):
		try:
			return self.DB.GetSeed()
		except AttributeError: # DB not instantiated yet
			return ""

        def IsIPInternal(self, IP):
		return len(self.IsIPInternalRegexp.findall(IP)) == 1

def Init(RootDir):
	return Core(RootDir)

