""" 
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

ACTIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""

DESCRIPTION = "Active probing for juicy files (DirBuster)"

def run(Core, PluginInfo):
	#Core.Config.Show()
	# Define DirBuster Commands to use depending on Interaction Setting:
	# DirBuster allows much more control when interactive
	# DirBuster can also be run non-interactively for scripting
	DirBusterInteraction = { True : 'DirBusterInteractive', False : 'DirBusterNotInteractive' }
	return Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResourceList([ DirBusterInteraction[Core.Config.Get('INTERACTIVE')], 'DirBuster_Extract_URLs' ]), PluginInfo, "")
	#return Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResources(DirBusterInteraction[Core.Config.Get('Interactive')]), PluginInfo, Content)

