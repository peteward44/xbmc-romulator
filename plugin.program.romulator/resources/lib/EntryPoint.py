import urllib, urllib2, xbmcplugin, xbmcgui, re, string, sys, os, traceback, xbmcaddon, logging

import Config, DbConnection, ScriptParams, Launcher, RomScanner
import AddEmulatorDialog
import GuiGameInfoWindow, XbmcDirectoryListing
import xbmc, logging, time


def FindEmulatorTypeByName( emuTypeList, name ):
	for emuType in emuTypeList:
		if emuType[ 'name' ] == name:
			return emuType
	return None
	
	
def AddRomMenuItem( directoryListing, romDictionary ):
	romImage = Config.config.GetImagePath( "unknownRomIcon.png" )
	romCacheImage = Config.config.GetRomsImageCacheFile( romDictionary[ "name" ] )
	if romCacheImage != None and len( romCacheImage ) > 0 and os.path.isfile( romCacheImage ):
		romImage = romCacheImage
#	print "ROM IMAGE: " + romImage
	directoryListing.AddItem( romDictionary[ "name" ], '', romImage, { 'mode':'showgameinfo', 'romid':str( romDictionary[ "id" ] ) }, False, False )


def init_db():
	dbConnection = DbConnection.DbConnection()
	dbConnection.CreateTables()
	dbConnection.CloseDb()

	
def build_main_directory():

	viewTypeList = [ ( 'View All', 'all' ), ( 'View Favourites', 'favourites' ), ( 'View By Emulator', 'emulator' ),
		( 'View By Genre', 'genre' ), ( 'View By Developer', 'developer' ), ( 'View By Publisher', 'publisher' ) ]
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	for ( friendlyName, urlName ) in viewTypeList:
		dir.AddItem( friendlyName, '', Config.config.GetImagePath( 'icon.png' ), { 'mode':'browse', 'view':urlName }, True, True )
	dir.AddItem( "Settings", '', Config.config.GetImagePath( 'settings.png' ), { 'mode':'settings', 'addFolderToHierarchy':'1' }, True, True )
	dir.Commit( True )
	
	
def build_emulator_directory( startItemIndex, itemCount, addFolderToHierarchy ):

	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'browse', 'view':'emulator' } )
	
	emuCount = len( Config.config.emulatorTypeMap )
	topRange = startItemIndex + itemCount
	if topRange > emuCount:
		topRange = emuCount
		
	for emuIndex in range( startItemIndex, topRange ):
		emulator = Config.config.emulatorTypeMap[ emuIndex ]
		dir.AddItem( emulator[ 'name' ], '', Config.config.GetImagePath( 'icon.png' ), { 'mode':'romview_emulator', 'emulator':emulator[ 'name' ] }, True, True )
		
	dir.AddNextPageItem( startItemIndex, itemCount, emuCount, { 'mode':'browse', 'view':'emulator' } )
	dir.Commit( addFolderToHierarchy )


def build_emulator_romview_directory( emulatorDictionary, startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( romList, totalRomCount ) = dbConnection.SelectEmulatorRoms( emulatorDictionary[ 'name' ], 0, 1, 0, 'name', 0, startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'romview_emulator', 'emulator':emulatorDictionary[ 'name' ] } )
	
	for rom in romList:
		AddRomMenuItem( dir, rom )

	dir.AddNextPageItem( startItemIndex, itemCount, totalRomCount, { 'mode':'romview_emulator', 'emulator':emulatorDictionary[ 'name' ] } )
	dir.Commit( addFolderToHierarchy )
	

def build_genre_directory( startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( genreList, totalGenreCount ) = dbConnection.GetGenreList( startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'browse', 'view':'genre' } )

	for genre in genreList:
		dir.AddItem( genre[ 'name' ], '', Config.config.GetGenresImageCacheFile( genre[ 'name' ] ), { 'mode':'romview_genre', 'genreid':genre[ 'id' ] }, True, True )

	dir.AddNextPageItem( startItemIndex, itemCount, totalGenreCount, { 'mode':'browse', 'view':'genre' } )
	dir.Commit( addFolderToHierarchy )

	
def build_genre_romview_directory( genreId, startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( romList, totalRomCount ) = dbConnection.GetRomsByGenre( genreId, startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'romview_genre', 'genreid':genreId } )
	
	for rom in romList:
		AddRomMenuItem( dir, rom )

	dir.AddNextPageItem( startItemIndex, itemCount, totalRomCount, { 'mode':'romview_genre', 'genreid':genreId } )
	dir.Commit( addFolderToHierarchy )
	
	
def build_developer_directory( startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( developerList, totalDevCount ) = dbConnection.GetDeveloperList( startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'browse', 'view':'developer' } )

	for dev in developerList:
		dir.AddItem( dev[ 'name' ], '', Config.config.GetCompaniesImageCacheFile( dev[ 'name' ]	), { 'mode':'romview_developer', 'developerid':dev[ 'id' ] }, True, True )

	dir.AddNextPageItem( startItemIndex, itemCount, totalDevCount, { 'mode':'browse', 'view':'developer' } )
	dir.Commit( addFolderToHierarchy )
		
		
def build_developer_romview_directory( developerId, startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( romList, totalRomCount ) = dbConnection.GetRomsByDeveloperId( developerId, startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'romview_developer', 'developerid':developerId } )
	
	for rom in romList:
		AddRomMenuItem( dir, rom )

	dir.AddNextPageItem( startItemIndex, itemCount, totalRomCount, { 'mode':'romview_developer', 'developerid':developerId } )
	dir.Commit( addFolderToHierarchy )
	

def build_publisher_directory( startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( publisherList, totalPubCount ) = dbConnection.GetPublisherList( startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'browse', 'view':'publisher' } )

	for pub in publisherList:
		dir.AddItem( pub[ 'name' ], '', Config.config.GetCompaniesImageCacheFile( pub[ 'name' ]	), { 'mode':'romview_publisher', 'publisherid':pub[ 'id' ] }, True, True )

	dir.AddNextPageItem( startItemIndex, itemCount, totalPubCount, { 'mode':'browse', 'view':'publisher' } )
	dir.Commit( addFolderToHierarchy )

		
def build_publisher_romview_directory( publisherId, startItemIndex, itemCount, addFolderToHierarchy ):

	dbConnection = DbConnection.DbConnection()
	( romList, totalRomCount ) = dbConnection.GetRomsByPublisherId( publisherId, startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'romview_publisher', 'publisherid':publisherId } )
	
	for rom in romList:
		AddRomMenuItem( dir, rom )

	dir.AddNextPageItem( startItemIndex, itemCount, totalRomCount, { 'mode':'romview_publisher', 'publisherid':publisherId } )
	dir.Commit( addFolderToHierarchy )
	
	
	
def build_romview_directory( viewName, startItemIndex, itemCount, addFolderToHierarchy ):

	showFavourites = 0
	if viewName == 'favourites':
		showFavourites = 1

	dbConnection = DbConnection.DbConnection()
	isBestVersion = 1
	( romDataDictionaryList, totalRomCount ) = dbConnection.SelectEmulatorRoms( '*', None,
		isBestVersion, showFavourites, 'name', 0, startItemIndex, itemCount )
	dbConnection.CloseDb()
	
	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddPreviousPageItem( startItemIndex, itemCount, { 'mode':'browse', 'view':viewName } )

	for rom in romDataDictionaryList:
		AddRomMenuItem( dir, rom )

	dir.AddNextPageItem( startItemIndex, itemCount, totalRomCount, { 'mode':'browse', 'view':viewName } )
	dir.Commit( addFolderToHierarchy )


def build_settings_directory( addFolderToHierarchy ):

	dir = XbmcDirectoryListing.XbmcDirectoryListing()
	dir.AddItem( "Add Emulator", '', Config.config.GetImagePath( 'settings.png' ), { 'mode':'settings_add' }, True, False )
	dir.AddItem( "Refresh All", '', Config.config.GetImagePath( 'settings.png' ), { 'mode':'settings_refreshall' }, True, False )
	dir.Commit( addFolderToHierarchy )

	
def launch_rom( romId ):

	dbConnection = DbConnection.DbConnection()
	romDataDictionary = dbConnection.GetRomById( romId )
	dbConnection.CloseDb()
	
	emuDict = Config.config.GetEmulatorByName( romDataDictionary[ 'emulatorName' ] )

	print "Launching rom " + str( romId )
	Launcher.LaunchRom( emuDict, romDataDictionary )
	
	
def refresh_roms_callback( progressBar, itemIndex, itemCount, emulatorName, operationName, fileName ):

	sleepValue = 50
#	if itemCount < 100:
#		sleepValue = 100
#	elif itemCount < 1000:
#		sleepValue = 50
	
	if progressBar != None:
#		print "Updating progress bar FI: " + str( fileIndex ) + " FC: " + str( fileCount ) + " %:" + str( int( ( float( fileIndex ) / float( fileCount ) ) * 100.0 ) )
		try:
#			print "Calling progressBar.update"
			progressBar.update( int( ( float( itemIndex ) / float( itemCount ) ) * 100.0 ), operationName + " [" + emulatorName + "]", fileName )
		except:
			pass
			
	try:
		xbmc.sleep( sleepValue )
	except:
		pass

	if progressBar != None:
		try:
			if progressBar.iscanceled():
				return False
				
		except Exception as e:
			return False
			
	return True

	
def refresh_roms( viewName ):

	progressBar = None
	
	try:
		progressBar = xbmcgui.DialogProgressBG()
	except:
		progressBar = xbmcgui.DialogProgress()
	
	if progressBar != None:
		progressBar.create('Refreshing Roms...')
#	xbmc.executebuiltin( "ActivateWindow(busydialog)" )

	emuList = Config.config.emulatorTypeMap

	if len( viewName ) > 0:
		emulatorType = FindEmulatorTypeByName( emuList, viewName )
		if progressBar != None:
			try:
				progressBar.update( 0, emulatorType[ 'name' ] )
			except:
				pass
		RomScanner.RefreshRoms( emulatorType[ "name" ], emulatorType[ "giantBombPlatformId" ], emulatorType[ "romsPath" ],
			emulatorType[ "romFilter" ], refresh_roms_callback, progressBar )
	else:
		RefreshNextEmulator( ( progressBar, 0 ) );

		
def RefreshNextEmulator( ( progressBar, emuIndex ) ):

	if progressBar != None and progressBar.iscanceled():
		return

	emuList = Config.config.emulatorTypeMap
	if emuIndex < len( emuList ):
		emulatorType = emuList[ emuIndex ];
		if progressBar != None:
			try:
				progressBar.update( 0, emulatorType[ 'name' ] )
			except:
				pass
		RomScanner.RefreshRoms( emulatorType[ "name" ], emulatorType[ "giantBombPlatformId" ],
			emulatorType[ "romsPath" ], emulatorType[ "romFilter" ], refresh_roms_callback, progressBar, RefreshNextEmulator, ( progressBar, emuIndex + 1 ) )
	
	
def ShouldAddPageToHierarchy( scriptParams ):

	# has it come through script params?
	addPageDirective = bool( int( scriptParams.GetParamDefault( "addFolderToHierarchy", '1' ) ) )
	
	# is there a previous page handle in the script params?
	previousPageHandle = int( scriptParams.GetParamDefault( "previousPageHandle", '0' ) )
	currentPageHandle = int( sys.argv[1] )
	
	if previousPageHandle > 0:
		# this checks to see if the user has clicked '...' at the top to go backwards, if it is then the
		# page handles will not be consecutive. If they have clicked '...', then always add the page to hierarchy,
		# otherwise just obey the 'addFolderToHierarchy' directive
		isTraversedPage = previousPageHandle + 1 == currentPageHandle
		if not isTraversedPage:
			return True
	
	return addPageDirective
	

def StartApp( ADDON ):
	paramsString = ""		
	if len( sys.argv ) >= 3:
		paramsString = sys.argv[2]
	scriptParams = ScriptParams.ScriptParams( paramsString )
	mode = scriptParams.GetParamDefault( "mode", "" )
	addFolderToHierarchy = ShouldAddPageToHierarchy( scriptParams )

	addonPath = ADDON.getAddonInfo('path')
	resourcesPath = os.path.join( addonPath, "resources" )

	Config.config.Init( resourcesPath )
	
	print "Starting with params: " + paramsString
	
#	for x in range( 0, len( sys.argv ) ):
#		print "ARG" + str( x ) + ": " + str( sys.argv[x] )
		
	if mode == "":
		init_db()
		build_main_directory()

	elif mode == "browse":
		viewName = scriptParams.GetParamDefault( "view", "all" )
		startItemIndex = int( scriptParams.GetParamDefault( "startItemIndex", 0 ) )
		itemCount = int( scriptParams.GetParamDefault( "itemCount", Config.config.RomItemCount ) )

		if viewName == 'all' or viewName == 'favourites':
			build_romview_directory( viewName, startItemIndex, itemCount, addFolderToHierarchy )
		elif viewName == 'emulator':
			build_emulator_directory( startItemIndex, itemCount, addFolderToHierarchy )
		elif viewName == 'genre':
			build_genre_directory( startItemIndex, itemCount, addFolderToHierarchy )
		elif viewName == 'developer':
			build_developer_directory( startItemIndex, itemCount, addFolderToHierarchy )
		elif viewName == 'publisher':
			build_publisher_directory( startItemIndex, itemCount, addFolderToHierarchy )
					
	elif mode == "romview_genre":
		genreId = scriptParams.GetParamDefault( 'genreid', '0' )
		startItemIndex = int( scriptParams.GetParamDefault( "startItemIndex", 0 ) )
		itemCount = int( scriptParams.GetParamDefault( "itemCount", Config.config.RomItemCount ) )

		build_genre_romview_directory( genreId, startItemIndex, itemCount, addFolderToHierarchy )
					
	elif mode == "romview_developer":
		developerId = scriptParams.GetParamDefault( 'developerid', '0' )
		startItemIndex = int( scriptParams.GetParamDefault( "startItemIndex", 0 ) )
		itemCount = int( scriptParams.GetParamDefault( "itemCount", Config.config.RomItemCount ) )

		build_developer_romview_directory( developerId, startItemIndex, itemCount, addFolderToHierarchy )
					
	elif mode == "romview_publisher":
		publisherId = scriptParams.GetParamDefault( 'publisherid', '0' )
		startItemIndex = int( scriptParams.GetParamDefault( "startItemIndex", 0 ) )
		itemCount = int( scriptParams.GetParamDefault( "itemCount", Config.config.RomItemCount ) )

		build_publisher_romview_directory( publisherId, startItemIndex, itemCount, addFolderToHierarchy )

	elif mode == "romview_emulator":
		emulatorName = scriptParams.GetParamDefault( 'emulator', '' )
		emulatorDictionary = FindEmulatorTypeByName( Config.config.emulatorTypeMap, emulatorName )
		startItemIndex = int( scriptParams.GetParamDefault( "startItemIndex", 0 ) )
		itemCount = int( scriptParams.GetParamDefault( "itemCount", Config.config.RomItemCount ) )
		
		build_emulator_romview_directory( emulatorDictionary, startItemIndex, itemCount, addFolderToHierarchy )
		
	elif mode == "launch":
		romId = int( scriptParams.GetParamDefault( "romid", 0 ) )
		launch_rom( romId )

	elif mode == "showgameinfo":
		romId = int( scriptParams.GetParamDefault( "romid", 0 ) )
		skin = ADDON.getSetting( 'skin' )
		GuiGameInfoWindow.CreateWindow( addonPath, skin, romId )

	elif mode == "refresh":
		#print "Refresh roms " + scriptParams.GetParamDefault( "view", "All" )
		refresh_roms( scriptParams.GetParamDefault( "view", "All" ) )

	elif mode == "settings":
		build_settings_directory( addFolderToHierarchy )

	elif mode == "settings_add":
	#	AddEmulatorDialog.DoAddDialog()
	
		scriptToRun = ''
		if sys.platform == 'win32':
			scriptToRun = os.path.join( addonPath, 'config.cmd' )
		else:
			scriptToRun = os.path.join( addonPath, 'config.sh' )
	
		thirdLine = ''
		if len( scriptToRun ) > 50:
			thirdLine = scriptToRun[50:]
			scriptToRun = scriptToRun[:50]
	
		dialog = xbmcgui.Dialog()
		dialog.ok( "", "To add a new emulator, use the config script located at", scriptToRun, thirdLine )
		
		build_settings_directory( False )

	elif mode == "settings_refreshall":
		refresh_roms( "" )
		build_settings_directory( False )
