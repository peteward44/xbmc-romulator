
import sys, logging, os

g_exitted = False

print "Rom Launcher Command Line Configurator"
print "--------------------------------------------"
		
		
def GetUserOption( caption, validMin, validMax ):

	try:
		selection = raw_input( caption )
		selectionInt = int( selection )
		if selectionInt >= validMin and selectionInt <= validMax:
			return selectionInt
	except:
		pass
	return None
	
	
def DisplayMenuOptions( caption, optionsList ):

	optionIndex = 0
	for ( optionName, optionCallback ) in optionsList:
		optionIndex += 1
		print "[" + str( optionIndex ) + "] " + optionName
	
	while True:
		selection = GetUserOption( 'Select an option: ', 1, len( optionsList ) )

		if selection is not None:
			( selectedName, selectedCallback ) = optionsList[ selection - 1 ]
			printAgain = selectedCallback()
			if not g_exitted and printAgain:
				DisplayMenuOptions( caption, optionsList )
			return
		else:
			print "Invalid option. Specify a value between [1-" + str( optionIndex ) + "]"
	

def ListEmulators( displayIndex ):
	
	optionIndex = 0
	for emulatorTypeMap in Config.config.emulatorTypeMap:
		optionIndex += 1
		indexString = ( "[" + str( optionIndex ) + "] " ) if displayIndex == True else ""
		print indexString + emulatorTypeMap[ 'name' ]
		print "\tPATH: " + emulatorTypeMap[ 'romsPath' ] + "\t" + emulatorTypeMap[ 'romFilter' ]
		print "\tCOMMAND: " + emulatorTypeMap[ 'exe_file' ] + "\t" + emulatorTypeMap[ 'exe_args' ]

		
def DoSearchForPlatform():

	running = 1
	while running == 1:
		searchEmuName = ''
		while len( searchEmuName ) == 0:
			searchEmuName = raw_input( 'Search name of emulator: ' )

		platformList = RomScraper.GetRomScraper().SearchForPlatformBlock( searchEmuName )
		
		if platformList is not None and len( platformList ) > 0:
			platformIndex = 0
			for platformDict in platformList:
				platformIndex += 1
				print "[" + str( platformIndex ) + "] " + platformDict[ 'name' ]
				print "\t" + platformDict[ 'description' ]
				print ""
			print "[" + str( platformIndex + 1 ) + "] None of these"
			print ""
			
			selectionIndex = None
			while selectionIndex == None:
				selectionIndex = GetUserOption( 'Select an option: ', 1, len( platformList ) + 1 )
			
			if selectionIndex != ( len( platformList ) + 1 ):
				return platformList[ selectionIndex-1 ]
		else:
			print( "Could not find any platforms by that name." )
			
		response = raw_input( "Search again [Yes]? " )
		running = 0 if response.lower() == 'no' else 1
		
	return None
	
	
def OnAddEmulator():
	print "Add an emulator"
	print "---------------"
	localEmuName = raw_input( 'Local name of emulator to add? ' )
	if len( localEmuName ) == 0:
		localEmuName = "default emulator"
	
	doScrapeText = raw_input( 'Search for platform on GiantBomb [Yes]? ' )
	doScrape = 0 if doScrapeText.lower() == 'no' else 1
	
	gbombId = ''
	if doScrape > 0:
		platformDict = DoSearchForPlatform()
		if platformDict is not None:
			gbombId = platformDict['giantBombPlatformId']

	exe_file = ''
	while len( exe_file ) == 0:
		exe_file = raw_input( 'Specify location of emulator to run: ' )
		if not os.path.isfile( exe_file ):
			print "Invalid file location"
			exe_file = ''
			
	exe_args = raw_input( 'Specify command line arguments for emulator (Use %ROM% for rom filename) [%ROM%]: ' )
	if len( exe_args ) == 0:
		exe_args = '%ROM%'
		
	roms_path = ''
	while len( roms_path ) == 0:
		roms_path = raw_input( 'Specify directory where rom files are stored: ' )
		if not os.path.isdir( roms_path ):
			print "Invalid directory location"
			roms_path = ''
			
	roms_filter = raw_input( 'Specify file filter for rom files [*.*]: ' )
	if len( roms_filter ) == 0:
		roms_filter = '*.*'

	Config.config.emulatorTypeMap.append( { 'name':localEmuName, 'romsPath':roms_path, 'romFilter':roms_filter,
		'exe_file':exe_file, 'exe_args':exe_args, 'giantBombPlatformId':gbombId } )
	
	Config.config.SaveConfig()
	return True
	

def OnRemoveEmulator():
	print "Remove emulator"
	print "---------------"
	
	if len( Config.config.emulatorTypeMap ) > 0:
		ListEmulators( True )
		
		selection = None
		while selection == None:
			selection = GetUserOption( 'Which emulator to remove? ', 1, len( Config.config.emulatorTypeMap ) )
			if selection is not None:
				Config.config.emulatorTypeMap.remove( Config.config.emulatorTypeMap[ selection - 1 ] )
				Config.config.SaveConfig()
	else:
		print "No emulators present, add one in the main menu"
		
	return True
	
	
def OnListEmulators():
	print "List emulators"
	print "---------------"
	ListEmulators( False )
	print "---------------"
	
	return True
	
	
def OnExit():
	g_exitted = True
	return False
	
	
if sys.version_info.major != 2 and sys.version_info.minor != 7:
	print( "Cannot run script: You must use python 2.7 (You are trying to use " + str( sys.version_info.major ) + "." + str( sys.version_info.minor ) + ")" )
else:
	import Config, DbConnection, RomScraper
	
	resourcesPath = 'resources'
	Config.config.Init( resourcesPath )
	
	dbConnection = DbConnection.DbConnection()
	dbConnection.CreateTables()
	dbConnection.CloseDb()

	DisplayMenuOptions( 'Please select an option', [ ( 'Add emulator', OnAddEmulator ), ( 'Remove emulator', OnRemoveEmulator ),
		( 'List emulators', OnListEmulators ), ( 'Exit', OnExit ) ] )
	
	print "--------------------------------------------"

	