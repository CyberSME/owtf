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

The PluginHandler is in charge of running all plugins taking into account the chosen settings
'''
import os, sys, imp
from collections import defaultdict
from framework.lib.general import *

INTRO_BANNER_GENERAL = """
Short Intro:
Current Plugin Groups:
- web: For web assessments or when net plugins find a port that "speaks HTTP"
- net: For network assessments, discovery and port probing
- aux: Auxiliary plugins, to automate miscelaneous tasks
"""

INTRO_BANNER_WEB_PLUGIN_TYPE = """
WEB Plugin Types:
- Passive Plugins: NO requests sent to target
- Semi Passive Plugins: SOME "normal/legitimate" requests sent to target
- Active Plugins: A LOT OF "bad" requests sent to target (You better have permission!)
- Grep Plugins: NO requests sent to target. 100% based on transaction searches and plugin output parsing. Automatically run after semi_passive and active in default profile.
"""

class PluginHandler:
	PluginCount = 0

	def __init__(self, CoreObj, Options):
		self.Core = CoreObj
		#This should be dynamic from filesystem:
		#self.PluginGroups = [ 'web', 'net', 'aux' ]
		#self.PluginTypes = [ 'passive', 'semi_passive', 'active', 'grep' ]
	        #self.AllowedPluginTypes = self.GetAllowedPluginTypes(Options['PluginType'].split(','))
		self.Simulation, self.Scope, self.PluginGroup, self.Algorithm = [ Options['Simulation'], Options['Scope'], Options['PluginGroup'], Options['Algorithm'] ]
		self.OnlyPluginsList = self.ValidateAndFormatPluginList(Options['OnlyPlugins'])
		self.ExceptPluginsList = self.ValidateAndFormatPluginList(Options['ExceptPlugins'])
		#print "OnlyPlugins="+str(self.OnlyPluginsList)
		#print "ExceptPlugins="+str(self.ExceptPluginsList)
		#print "Options['PluginType']="+str(Options['PluginType'])
		if isinstance(Options['PluginType'], str): # For special plugin types like "quiet" -> "semi_passive" + "passive"
			Options['PluginType'] = Options['PluginType'].split(',')	
		self.Core.Config.Plugin.DeriveAllowedTypes(self.PluginGroup, Options['PluginType'])
		self.OnlyPluginsSet = len(self.OnlyPluginsList) > 0
		self.ExceptPluginsSet = len(self.ExceptPluginsList) > 0
		self.InitExecutionRegistry()

        def ValidateAndFormatPluginList(self, PluginList):
                List = [] # Ensure there is always a list to iterate from! :)
                if PluginList != None:
                        List = PluginList

                ValidatedList = []
		#print "List to validate="+str(List)
                for Item in List:
                        Found = False
                        for Plugin in self.Core.Config.Plugin.GetPlugins( { 'Group' : self.PluginGroup } ): # Processing Loop
                                if Item in [ Plugin['Code'], Plugin['Name'] ]:
                			ValidatedList.append(Plugin['Code'])
                                        Found = True
                                        break
                        if not Found:
                                cprint("ERROR: The code '"+Item+"' is not a valid plugin, please use the -l option to see available plugin names and codes")
                                exit()
                return ValidatedList # Return list of Codes

	def InitExecutionRegistry(self): # Initialises the Execution registry: As plugins execute they will be tracked here, useful to avoid calling plugins stupidly :)
		self.ExecutionRegistry = defaultdict(list) 
		for Target in self.Scope:
			self.ExecutionRegistry[Target] = []

	def LogPluginExecution(self, Plugin):
		Target = self.Core.Config.GetTarget()
		#print "Saving Execution: "+str(Plugin)+", for Target: "+str(Target)
		self.ExecutionRegistry[Target].append(Plugin)

	def GetLastPluginExecution(self, Plugin):
		ExecLog = self.ExecutionRegistry[self.Core.Config.GetTarget()] # Get shorcut to relevant execution log for this target for readability below :)
		NumItems = len(ExecLog)
		#print "NumItems="+str(NumItems)
		if NumItems == 0:
			return -1 # List is empty
		#print "NumItems="+str(NumItems)
		#print str(ExecLog)
		#print str(range((NumItems -1), 0))
		for Index in range((NumItems -1), -1, -1):
			#print "Index="+str(Index)
			#print str(ExecLog[Index])
			Match = True
			for Key, Value in ExecLog[Index].items(): # Compare all execution log values against the passed Plugin, if all match, return index to log record
				if Plugin[Key] != Value:
					Match = False
			if Match:
				#print str(PluginInfo)+" was found!"
				return Index
		return -1

	def HasPluginExecuted(self, Plugin):
		return (self.GetLastPluginExecution(Plugin) > -1)

	def GetExecLogSinceLastExecution(self, Plugin): # Get all execution entries from log since last time the passed plugin executed
		return self.ExecutionRegistry[self.Core.Config.GetTarget()][self.GetLastPluginExecution(Plugin):]

	def HasPluginCategoryRunSinceLastTime(self, Plugin, CategoryList):
		for PluginRec in self.GetExecLogSinceLastExecution(Plugin):
			if PluginRec['Type'] in CategoryList:
				return True
		return False

	def NormalRequestsAllowed(self):
		#AllowedPluginTypes = self.Core.Config.GetAllowedPluginTypes('web')
		#GetAllowedPluginTypes('web')
		AllowedPluginTypes = self.Core.Config.Plugin.GetAllowedTypes('web')
		return 'semi_passive' in AllowedPluginTypes or 'active' in AllowedPluginTypes

	def RequestsPossible(self):
		# Even passive plugins will make requests to external resources
		#return [ 'grep' ] != self.Core.Config.GetAllowedPluginTypes('web')
		return [ 'grep' ] != self.Core.Config.Plugin.GetAllowedTypes('web')

        def DumpPluginFile(self, Filename, Contents, Plugin):
                SaveDir = self.GetPluginOutputDir(Plugin)
                return self.Core.DumpFile(Filename, Contents, SaveDir)

        def GetPluginOutputDir(self, Plugin): # Organise results by OWASP Test type and then active, passive, semi_passive
		if Plugin['Group'] == 'web':
	                return self.Core.Config.Get('PARTIAL_URL_OUTPUT_PATH')+"/"+WipeBadCharsForFilename(Plugin['Title'])+"/"+Plugin['Type']+"/" 
		elif Plugin['Group'] == 'aux':
	                return self.Core.Config.Get('AUX_OUTPUT_PATH')+"/"+WipeBadCharsForFilename(Plugin['Title'])+"/"+Plugin['Type']+"/" 

        def PluginAlreadyRun(self, PluginInfo):
		if self.Simulation:
			return self.HasPluginExecuted(PluginInfo)
                SaveDir = self.GetPluginOutputDir(PluginInfo)
                if not os.path.exists(SaveDir): # At least one directory is missing
                        return False # This is the first time the plugin is going to run (i.e. some directory was missing)
                return True # The path already exists, therefore the plugin has been run before

	def GetModule(self, ModuleName, ModuleFile, ModulePath):# Python fiddling to load a module from a file, there is probably a better way...
	        f, Filename, desc = imp.find_module(ModuleFile.split('.')[0], [ModulePath]) #ModulePath = os.path.abspath(ModuleFile)
		return imp.load_module(ModuleName, f, Filename, desc)

	def IsChosenPlugin(self, Plugin):
		Chosen = True
		if Plugin['Group'] == self.PluginGroup:
			if self.OnlyPluginsSet and Plugin['Code'] not in self.OnlyPluginsList:
				Chosen = False # Skip plugins not present in the white-list defined by the user
			if self.ExceptPluginsSet and Plugin['Code'] in self.ExceptPluginsList:
				Chosen = False # Skip plugins present in the black-list defined by the user
		if Plugin['Type'] not in self.Core.Config.Plugin.GetAllowedTypes(Plugin['Group']):
			Chosen = False # Skip plugin: Not matching selected type
		return Chosen

	def IsActiveTestingPossible(self): # Checks if 1 active plugin is enabled = active testing possible:
		Possible = False
		#for PluginType, PluginFile, Title, Code, ReferenceURL in self.Core.Config.GetPlugins(): # Processing Loop
		#for PluginType, PluginFile, Title, Code in self.Core.Config.Plugin.GetOrder(self.PluginGroup):
		for Plugin in self.Core.Config.Plugin.GetOrder(self.PluginGroup):
			if self.IsChosenPlugin(Plugin) and Plugin['Type'] == 'active':
				Possible = True
				break
		return Possible

	def CanPluginRun(self, Plugin, ShowMessages = False):
		if not self.IsChosenPlugin(Plugin):
			return False # Skip not chosen plugins
		# Grep plugins to be always run and overwritten (they run once after semi_passive and then again after active):
		if self.PluginAlreadyRun(Plugin) and not self.Core.Config.Get('FORCE_OVERWRITE') and not ('grep' == Plugin['Type']): #not Code == 'OWASP-WU-SPID': 
			if ShowMessages:
				cprint("Plugin: "+Plugin['Title']+" ("+Plugin['Type']+") has already been run, skipping ..")
			return False 
		if 'grep' == Plugin['Type'] and self.HasPluginExecuted(Plugin) and not self.HasPluginCategoryRunSinceLastTime(Plugin, [ 'active', 'semi_passive' ]):
			return False # Grep plugins can only run if some active or semi_passive plugin was run since the last time
		return True

	def GetPluginFullPath(self, PluginDir, Plugin):
		return PluginDir+"/"+Plugin['Type']+"/"+Plugin['File'] # Path to run the plugin 

	def RunPlugin(self, PluginDir, Plugin):
		self.Core.Timer.StartTimer('Plugin') # Time how long it takes the plugin to execute
		PluginPath = self.GetPluginFullPath(PluginDir, Plugin)
		(Path, Name) = os.path.split(PluginPath)
		#(Name, Ext) = os.path.splitext(Name)
		PluginOutput = self.GetModule("", Name, Path+"/").run(self.Core, Plugin)
		self.SavePluginInfo(PluginOutput, Plugin) # Timer retrieved here

	def ProcessPlugin(self, PluginDir, Plugin, Status):
		if not self.CanPluginRun(Plugin, True):
			return None # Skip 
		Status['AllSkipped'] = False # A plugin is going to be run
		self.PluginCount += 1
		cprint("_" * 10 + " "+str(self.PluginCount)+" - Target: "+self.Core.Config.GetTarget()+" -> Plugin: "+Plugin['Title']+" ("+Plugin['Type']+") " + "_" * 10)
		self.LogPluginExecution(Plugin)
		if self.Simulation:
			return None # Skip processing in simulation mode, but show until line above to illustrate what will run
		if 'grep' == Plugin['Type'] and self.Core.DB.Transaction.NumTransactions() == 0: # DB empty = grep plugins will fail, skip!!
			cprint("Skipped - Cannot run grep plugins: The Transaction DB is empty")
			return None
		try:
			self.RunPlugin(PluginDir, Plugin)
			Status['SomeSuccessful'] = True
		except KeyboardInterrupt:
			self.SavePluginInfo("Aborted by user", Plugin) # cannot save anything here, but at least explain why
			self.Core.Error.UserAbort("Plugin")
			Status['SomeAborted'] = True
		except SystemExit:
			raise SystemExit # Abort plugin processing and get out to external exception handling, information saved elsewhere
		except PluginAbortException, PartialOutput:
			self.SavePluginInfo(str(PartialOutput.parameter)+"\nNOTE: Plugin aborted by user (Plugin Only)", Plugin) # Save the partial output, but continue to process other plugins
			Status['SomeAborted'] = True
		except FrameworkAbortException, PartialOutput:
			self.SavePluginInfo(str(PartialOutput.parameter)+"\nNOTE: Plugin aborted by user (Framework Exit)", Plugin) # Save the partial output and exit
			self.Core.Finish("Aborted by User")
		except: # BUG
			self.SavePluginInfo(self.Core.Error.Add("Plugin "+Plugin['Type']+"/"+Plugin['File']+" failed"), Plugin) # Try to save something
			#TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/

	def ProcessPlugins(self):
		Status = { 'SomeAborted' : False, 'SomeSuccessful' : False, 'AllSkipped' : True }
		if self.PluginGroup in [ 'web', 'aux' ]:
			self.ProcessPluginsForTargetList(self.PluginGroup, Status, self.Scope)
		return Status

	def GetPluginGroupDir(self, PluginGroup):
	        PluginDir = self.Core.Config.Get('PLUGINS_DIR')+PluginGroup
		return PluginDir

	def SwitchToTarget(self, Target):
		self.Core.Config.SetTarget(Target) # Tell Config that all Gets/Sets are now Target-specific

	def ProcessPluginsForTargetList(self, PluginGroup, Status, TargetList): # TargetList param will be useful for netsec stuff to call this
		PluginDir = self.GetPluginGroupDir(PluginGroup)
		cprint("PluginHandler: Processing "+PluginGroup+" plugins using "+self.Algorithm+" algorithm ..")
		if 'breadth' == self.Algorithm: # Loop plugins, then targets
			for Plugin in self.Core.Config.Plugin.GetOrder(PluginGroup):# For each Plugin
				#print "Processing Plugin="+str(Plugin)
				for Target in TargetList: # For each Target 
					#print "Processing Target="+str(Target)
					self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
					self.ProcessPlugin( PluginDir, Plugin, Status )
		elif 'depth' == self.Algorithm: # Loop Targets, then plugins
			for Target in TargetList: # For each Target
				self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
				for Plugin in self.Core.Config.Plugin.GetOrder(PluginGroup):# For each Plugin
					self.ProcessPlugin( PluginDir, Plugin, Status )

	def SavePluginInfo(self, PluginOutput, Plugin):
		self.Core.DB.SaveDBs() # Save new URLs to DB after each request
		self.Core.Reporter.SavePluginReport(PluginOutput, Plugin) # Timer retrieved by Reporter

	def ShowPluginList(self):
		if self.PluginGroup == 'web':
			self.ShowWebPluginsBanner()
		elif self.PluginGroup == 'aux':
			self.ShowAuxPluginsBanner()
		self.ShowPluginGroupPlugins(self.PluginGroup)

	def ShowAuxPluginsBanner(self):
	        print(INTRO_BANNER_GENERAL+"\n Available AUXILIARY plugins:""")

	def ShowWebPluginsBanner(self):
	        print(INTRO_BANNER_GENERAL+INTRO_BANNER_WEB_PLUGIN_TYPE+"\n Available WEB plugins:""")

	def ShowPluginGroupPlugins(self, PluginGroup):
		for PluginType in self.Core.Config.Plugin.GetTypesForGroup(PluginGroup): 
			self.ShowPluginTypePlugins(PluginType)

	def ShowPluginTypePlugins(self, PluginType):
		cprint("\n"+'*' * 40+" "+PluginType.title().replace('_', '-')+" Plugins "+'*' * 40)
		for Plugin in self.Core.Config.Plugin.GetAll(self.PluginGroup, PluginType):
			#'Name' : PluginName, 'Code': PluginCode, 'File' : PluginFile, 'Descrip' : PluginDescrip } )
			LineStart = " "+Plugin['Type']+": "+Plugin['Name']
			Pad1 = "_" * (60 - len(LineStart))
			Pad2 = "_" * (20- len(Plugin['Code']))
		        cprint(LineStart+Pad1+"("+Plugin['Code']+")"+Pad2+Plugin['Descrip'])

