
import sys, logging

				
def refresh_roms_callback( userData, itemIndex, itemCount, emulatorName, operationName, fileName ):

	try:
		nameString = ( "%s [%s]" % ( operationName, emulatorName ) )
		progressString = ( "[%i/%i]" % ( ( itemIndex + 1 ), itemCount ) )
		finalString = ( " %-45s %-25s" % ( nameString, progressString ) )
		sys.stdout.write( "\r" + finalString )
		sys.stdout.flush()
	except Exception as e:
		logging.exception(e)


print "Rom Launcher Command Line Database Refresher"
print "--------------------------------------------"
		
if sys.version_info.major != 2 and sys.version_info.minor != 7:
	print( "Cannot run script: You must use python 2.7 (You are trying to use " + str( sys.version_info.major ) + "." + str( sys.version_info.minor ) + ")" )
else:
	import RomScanner, RomScraper, Config, DbConnection
	
	resourcesPath = 'resources'
	Config.config.Init( resourcesPath )
	
	dbConnection = DbConnection.DbConnection()
	dbConnection.CreateTables()
	dbConnection.CloseDb()

	for emulatorType in Config.config.emulatorTypeMap:
		totalRomsProcessed = RomScanner.RefreshRomsBackgroundThread( emulatorType[ "name" ], emulatorType[ "giantBombPlatformId" ],
			emulatorType[ "romsPath" ], emulatorType[ "romFilter" ], refresh_roms_callback, None, None, None )
			
		romPlural = "roms" if totalRomsProcessed != 1 else "rom"
		print "\n Emulator " + emulatorType[ "name" ] + " complete, " + str( totalRomsProcessed ) + " " + romPlural + " processed"
	
	print "--------------------------------------------"
	print "Operation completed\n"
