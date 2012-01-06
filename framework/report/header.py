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

The reporter module is in charge of producing the HTML Report as well as provide plugins with common HTML Rendering functions
'''
import os, re, cgi, sys
from framework.lib.general import *
from collections import defaultdict

class Header:
	def __init__(self, CoreObj):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False

        def CopyAccessoryFiles(self):
                cprint("Copying report images ..")
                self.Core.Shell.shell_exec("cp -r "+self.FrameworkDir+"/images/ "+self.TargetOutputDir)
                cprint("Copying report includes (stylesheet + javascript files)..")
                self.Core.Shell.shell_exec("cp -r "+self.FrameworkDir+"/includes/ "+self.TargetOutputDir)

        def DrawRunDetailsTable(self):
                Table = self.Core.Reporter.Render.CreateTable({'class' : 'run_log'})
                Table.CreateCustomRow('<tr><th colspan="5">Run Log</th></tr>')
                Table.CreateRow(['Start', 'End', 'Runtime', 'Command', 'Status'], True)
                for line in self.Core.DB.GetData('RUN_DB'):
                        Start, End, Runtime, Command, Status = line
                        Table.CreateRow(Table.EscapeCells([Start, End, Runtime, Command, Status]))
                return Table.Render()

        def GetErrorDBButtonLabel(self):
                ErrorDBLabel = "Errors: "
                if self.Core.DB.ErrorCount() > 0:
                        ErrorDBLabel += "Found: Please report!"
                        ErrorDBLabel = "<font color='red'>"+ErrorDBLabel+"</font>"
                else:
                        ErrorDBLabel += "No errors"
                return ErrorDBLabel

        def DrawReviewDeleteOptions(self):
                return self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([
['Delete THIS Review', 'ClearReview()']
, ['Delete ALL Reviews', "DeleteStorage()"]
], 'DrawButtonJSLink', {})

        def DrawReviewMiscOptions(self):
                return self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([
['Show Used Memory (KB)', "ShowUsedMem()"]
, ['Show Used Memory (%)', 'ShowUsedMemPercentage()']
, ['Show Debug Window', 'ShowDebugWindow()']
, ['Hide Debug Window', 'HideDebugWindow()']
], 'DrawButtonJSLink', {})

        def DrawReviewImportExportOptions(self):
                return self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([
['Import Review', "ImportReview()"]
, ['Export Review as text', 'ExportReviewAsText()']
#, ['Export Review as file', 'ExportReviewAsFile()']  
#<- Component returned failure code: 0x80004005 (NS_ERROR_FAILURE) [nsIDOMHTMLDocument.execCommand]
#[Break On This Error] dlg = execCommand('SaveAs', false, filename+'.txt'); 
], 'DrawButtonJSLink', {})+'<textarea rows="20" cols="100" id="import_export_box"></textarea>'

	def DrawGeneralLogs(self):
		return self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ 
[ self.GetErrorDBButtonLabel(), str(self.Core.Config.GetAsPartialPath('ERROR_DB')) ]
, [ 'Transaction Log (HTML)', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_HTML') ]
#, [ 'All Downloaded Files', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_FILES') ]
, [ 'All Downloaded Files - To be implemented', '#' ]
, [ 'All Transactions', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_TRANSACTIONS') ]
, [ 'All Requests', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_REQUESTS') ]
, [ 'All Response Headers', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_RESPONSE_HEADERS') ]
, [ 'All Response Bodies', self.Core.Config.GetAsPartialPath('TRANSACTION_LOG_RESPONSE_BODIES') ]
], 'DrawButtonLink', {}) # {} avoid nasty python issue where it keeps a reference to the latest attributes before

	def DrawURLDBs(self, DBPrefix = ""):
		return self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ 
['All URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'ALL_URLS_DB')]
, ['File URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'FILE_URLS_DB')]
, ['Fuzzable URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'FUZZABLE_URLS_DB')]
, ['Image URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'IMAGE_URLS_DB')]
, ['Error URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'ERROR_URLS_DB')]
, ['External URLs', self.Core.Config.GetAsPartialPath(DBPrefix+'EXTERNAL_URLS_DB')]
], 'DrawButtonLink', {})

        def DrawFilters(self):
		return self.Core.Reporter.DrawCounters(True)

        def AddMiscelaneousTabs(self, Tabs):
                Tabs.AddCustomDiv('Miscelaneous:') # First create custom tab, without javascript
                Tabs.AddDiv('exploit', 'Exploitation', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ ['Hackvertor', 'http://hackvertor.co.uk/public'] , [ 'Hackarmoury', 'http://hackarmoury.com/' ], ['ExploitDB', 'http://www.exploit-db.com/'] , ['ExploitSearch', 'http://www.exploitsearch.net'], [ 'hackipedia', 'http://www.hakipedia.com/index.php/Hakipedia' ] ], 'DrawButtonLink'))
                Tabs.AddDiv('methodology', 'Methodology', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ ['OWASP', 'https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents'] , ['Pentest Standard', 'http://www.pentest-standard.org/index.php/Main_Page'], ['OSSTMM', 'http://www.isecom.org/osstmm/'] ], 'DrawButtonLink'))
                Tabs.AddDiv('calculators', 'Calculators', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ ['CVSS Advanced', 'http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2'] , ['CVSS Normal', 'http://nvd.nist.gov/cvss.cfm?calculator&version=2'] ], 'DrawButtonLink'))
                Tabs.AddDiv('learn', 'Test/Learn', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList([ [ 'taddong', 'http://blog.taddong.com/2011/10/hacking-vulnerable-web-applications.html' ], [ 'securitythoughts', 'http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/' ] , [ 'danielmiessler', 'http://danielmiessler.com/projects/webappsec_testing_resources/'] ], 'DrawButtonLink'))

        def DrawOWTFBox(self):
                OWTF = self.Core.Reporter.Render.CreateTable( { 'class' : 'report_intro' } )
                OWTF.CreateRow( [ 'Seed', 'Review Size', 'Total Size', 'Version', 'Site' ], True)
                OWTF.CreateRow( [ '<span id="seed">'+self.Core.GetSeed()+'</span>', '<div id="js_db_size"></div>', '<div id="total_js_db_size"></div>', self.Version, self.Core.Reporter.Render.DrawButtonLink('owtf.org', 'http://owtf.org') ] )
                return '<div style="position: absolute; top: 6px; right: 6px; float: right">'+OWTF.Render()+'</div>'

	def DrawBackToSummaryIcon(self):
		return self.Core.Reporter.Render.DrawLink(self.Core.Reporter.DrawImageFromConfigPair( [ 'FIXED_ICON_TO_SUMMARY', 'NAV_TOOLTIP_TO_SUMMARY' ] ), self.Core.Config.Get('HTML_REPORT'), { 'target' : '' } )
		
	def DrawURLTop(self):
		AlternativeIPsStr = ""
		if len(self.AlternativeIPs) > 0:
			AlternativeIPsStr = " [Alternative IPs: "+", ".join(self.AlternativeIPs)+"]"
		Target = self.Core.Reporter.Render.CreateTable({'class' : 'report_intro'})
		Target.CreateRow( [ 'Target URL', 'Target IP(s)', '&nbsp;' ], True)
		Target.CreateRow( [ self.Core.Reporter.Render.DrawButtonLink(self.TargetURL, self.TargetURL, {'id' : 'target_url'}), self.HostIP+AlternativeIPsStr, self.DrawBackToSummaryIcon() ] )
		return self.WrapTop(Target.Render())

	def WrapTop(self, LeftBoxStr):
		return '<div style="display: inline; align: left">'+LeftBoxStr+'</div>'+self.DrawOWTFBox()

	def DrawTop(self):
		if self.ReportType == 'URL':
			return self.DrawURLTop()
		elif self.ReportType == 'NetMap':
			return self.WrapTop('<h2>Summary Report</h2><br />')
		elif self.ReportType == 'AUX':
			return self.WrapTop('<h2>Auxiliary Plugins '+self.DrawBackToSummaryIcon()+'</h2>')

        def GetJavaScriptStorage(self): # Loads the appropriate JavaScript library files depending on the configured JavaScript Storage
                Libraries = []
                for StorageLibrary in self.Core.Config.Get('JAVASCRIPT_STORAGE').split(','):
                        Libraries.append('<script type="text/javascript" src="includes/'+StorageLibrary+'"></script>')
                return "\n".join(Libraries)

        def Save(self, Report, Options):
		self.TargetOutputDir, self.FrameworkDir, self.Version, self.TargetURL, self.HostIP, self.TransactionLogHTML, self.AlternativeIPs = self.Core.Config.GetAsList(['OUTPUT_PATH', 'FRAMEWORK_DIR', 'VERSION', 'TARGET_URL', 'HOST_IP', 'TRANSACTION_LOG_HTML', 'ALTERNATIVE_IPS'])
		self.ReportType = Options['ReportType']
		if not self.Init:
                        self.CopyAccessoryFiles()
                        self.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start
                with open(self.Core.Config.Get(Report), 'w') as file:
                        ReviewTabs = self.Core.Reporter.Render.CreateTabs()
                        ReviewTabs.AddDiv('review_import_export', 'Import/Export', self.DrawReviewImportExportOptions())
                        ReviewTabs.AddDiv('review_delete', 'Delete', self.DrawReviewDeleteOptions())
                        ReviewTabs.AddDiv('review_miscelaneous', 'Miscelaneous', self.DrawReviewMiscOptions())
                        ReviewTabs.CreateTabs()
                        ReviewTabs.CreateTabButtons()

			Tabs = self.Core.Reporter.Render.CreateTabs()
			Tabs.AddDiv('filter', 'Filter', self.DrawFilters())
                        Tabs.AddDiv('review', 'Review', ReviewTabs.Render())
                        Tabs.AddDiv('runlog', 'History', self.DrawRunDetailsTable())

			LogTable = self.Core.Reporter.Render.CreateTable({ 'class' : 'run_log' })
			LogTable.CreateRow(['General', 'Verified URLs', 'Potential URLs'], True)
			LogTable.CreateRow([self.DrawGeneralLogs(), self.DrawURLDBs(), self.DrawURLDBs("POTENTIAL_")])
			Tabs.AddDiv('logs', 'Logs', LogTable.Render())

			self.AddMiscelaneousTabs(Tabs)
			Tabs.CreateTabs() # Now create the tabs from Divs Above
			Tabs.CreateTabButtons() # Add navigation buttons to the right
                        file.write("""<html>
<head>
	<title>"""+Options['Title']+"""</title>
	<link rel="stylesheet" href="includes/stylesheet.css" type="text/css">
	<link rel="stylesheet" href="includes/jquery-ui-1.9m6/themes/base/jquery.ui.all.css">
</head>
<body>\n
"""+self.DrawTop()+"""
"""+Tabs.Render()+"""
<script type="text/javascript" src="includes/jquery-1.6.4.js"></script>\n
<script type="text/javascript" src="includes/owtf.js"></script>\n
<script type="text/javascript" src="includes/jsonStringify.js"></script>\n
"""+self.GetJavaScriptStorage()+"""
""") # Init HTML Report

