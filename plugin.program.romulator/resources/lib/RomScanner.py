

import os
import fnmatch
import re
import Config, RomScraper
import time
import threading, logging
import DbConnection


def GetRegularExpString( bracketContents ):

	return '([\[\(]{1}.*' + bracketContents + '{1}.*[\]\)]{1})'


def GetRegularExpStringMatch( bracketContents ):

	return '(.*)' + GetRegularExpString( bracketContents ) + '(.*)'
	
	
perfectRomMatcher = re.compile( GetRegularExpStringMatch( '\!' ) )
removeBracketsExpression = re.compile( GetRegularExpString( '.' ) )

territoryRegularExpressionMap = {
	Config.TERRITORY_USA: re.compile( GetRegularExpStringMatch( 'U' ) ),
	Config.TERRITORY_EUROPE: re.compile( GetRegularExpStringMatch( 'E' ) ),
	Config.TERRITORY_JAPAN: re.compile( GetRegularExpStringMatch( 'J' ) ),
	Config.TERRITORY_AUSTRALIA: re.compile( GetRegularExpStringMatch( 'A' ) ),
	Config.TERRITORY_CANADA: re.compile( GetRegularExpStringMatch( 'C' ) )
}

startingNumberMatcher = re.compile( '^\s*\d+\s*[\-\,-:]\s*' )


# public method
def RefreshRoms( emulatorName, giantBombPlatformId, romsPath, romsFilter, progressCallback, progressData, finishedCallback, finishedData ):

	download_thread = threading.Thread(target=RefreshRomsBackgroundThread, args=( emulatorName, giantBombPlatformId, romsPath, romsFilter, progressCallback, progressData, finishedCallback, finishedData ) )
	download_thread.start()

	
def AddCompaniesToDb( threadDbConnection, companyList ):
	
	for dict in companyList:
		# check if company is already scraped
		gbombId = dict[ 'giantBombId' ]
#		print "Company id " + str( gbombId )
		companyDict = threadDbConnection.GetCompanyByGiantBombId( gbombId )
#		print "FOUND " + str( companyDict is not None )
		if companyDict is not None and companyDict[ 'isScraped' ] is not True:
			# scrape it, add it
			localId = companyDict[ 'id' ]
			apiUrl = dict[ 'apiurl' ]
#			print "ID: " + str( localId ) + " API URL: " + str( apiUrl )
			companyScrapeDict = RomScraper.GetRomScraper().GetCompanyDetailsBlock( apiUrl )
			threadDbConnection.InsertCompanyScrapeRecord( localId, companyScrapeDict )
	
	
def AddGenresToDb( threadDbConnection, genreList ):

	for dict in genreList:
		# check if company is already scraped
		gbombId = dict[ 'giantBombId' ]
#		print "Company id " + str( gbombId )
		companyDict = threadDbConnection.GetGenreByGiantBombId( gbombId )
#		print "FOUND " + str( companyDict is not None )
		if companyDict is not None and companyDict[ 'isScraped' ] is not True:
			# scrape it, add it
			localId = companyDict[ 'id' ]
			apiUrl = dict[ 'apiurl' ]
#			print "ID: " + str( localId ) + " API URL: " + str( apiUrl )
			companyScrapeDict = RomScraper.GetRomScraper().GetGenreDetailsBlock( apiUrl )
			threadDbConnection.InsertGenreScrapeRecord( localId, companyScrapeDict )
	

def RefreshRomsBackgroundThread( emulatorName, giantBombPlatformId, romsPath, romsFilter, progressCallback, progressData, finishedCallback, finishedData ):

	threadDbConnection = None
	totalRomsProcessed = 0
	
	try:
		threadDbConnection = DbConnection.DbConnection()	
		threadDbConnection.ClearRoms( emulatorName )
		
		allFiles = GetAllFilesInDirectory( romsPath, romsFilter )
		
		fileCount = len( allFiles )
		print ( 'Discovered ' + str( fileCount ) + ' rom files' )
		
		if ( fileCount > 0 ):
			dbRows = []

			# build original array
			fileIndex = 0
			for file in allFiles:
				if progressCallback( progressData, fileIndex, fileCount, emulatorName, "Discovering", file ) == False:
					return

				fullPath = os.path.join( romsPath, file )
				( romName, romState, territory ) = DetermineRomNameAndState( fullPath )
				rowDict = { "fullPath": fullPath, "emulatorName": emulatorName, "romName": romName, "romState": romState, "territory": territory, "isBestVersion": 0 }
				dbRows.append( rowDict )

				fileIndex = fileIndex + 1
			
			# check for duplicates, find best version of each rom
			CheckForDuplicates( dbRows )
			
			threadDbConnection.InsertRomRecords( emulatorName, dbRows )
			
			# TODO: put in option to do scrape during refresh
			isScraping = 1
			
			# if we are scraping, read the roms back out the db and scrape each one
			if isScraping > 0:
				# for now, only scrape 'best version' roms
				( romDataDictionaryList, totalRomCount ) = threadDbConnection.SelectEmulatorRoms( emulatorName, 0, 1, 0, 'name', 0, 0, 0 )
			
				romIndex = 0
				for rowDict in romDataDictionaryList:
					if progressCallback( progressData, romIndex, totalRomCount, emulatorName, "Scraping", rowDict[ "name" ] ) == False:
						return
					ScrapeRom( rowDict[ "id" ], rowDict[ "name" ], giantBombPlatformId, threadDbConnection )
					
					romIndex += 1
					totalRomsProcessed += 1


	except Exception as e:
		logging.exception(e)

	finally:
		if threadDbConnection != None:
			threadDbConnection.CloseDb()
			del threadDbConnection
		if progressCallback != None:
			del progressCallback
		if finishedCallback != None:
			print "Calling finishedCallback"
			finishedCallback( finishedData )
			del finishedCallback
	
	return totalRomsProcessed
	
	
def ScrapeRomAsync( romId, romName, giantBombPlatformId, completeCallback, completeData ):

	thread = threading.Thread( target=ScrapeRomThread, args=( romId, romName, giantBombPlatformId, completeCallback, completeData ) )
	thread.start()
	
	
def ScrapeRomThread( romId, romName, giantBombPlatformId, completeCallback, completeData ):

	try:
		ScrapeRom( romId, romName, giantBombPlatformId, None )
		completeCallback( True, completeData )
	except Exception as e:
		logging.exception( e )
		completeCallback( False, completeData )
	
	
def ScrapeRom( romId, romName, giantBombPlatformId, threadDbConnection ):

	dbConnection = threadDbConnection
	if dbConnection == None:
		dbConnection = DbConnection.DbConnection()

	romSearchResultsList = RomScraper.GetRomScraper().SearchForRomBlock( romName, giantBombPlatformId )
	if romSearchResultsList != None:
		searchResultCount = len( romSearchResultsList )
#						print "Search result count for rom '" + rowDict[ "name" ] + "' " + str( searchResultCount );
		if searchResultCount > 0:
			# todo: refine search results instead of just using first one
			romSearchResult = romSearchResultsList[0]
#							print rowDict[ "name" ] + " | " + romSearchResult[ 'giantBombApiDetailsUrl' ]
			romDetailsDict = RomScraper.GetRomScraper().GetRomDetailsBlock( romName, romSearchResult[ 'giantBombApiDetailsUrl' ] )
			if romDetailsDict != None:
				romDetailsDict[ 'name' ] = romName
				
				dbConnection.InsertRomScrapeRecords( romId, romDetailsDict )
				AddCompaniesToDb( dbConnection, romDetailsDict[ 'developers' ] )
				AddCompaniesToDb( dbConnection, romDetailsDict[ 'publishers' ] )
				AddGenresToDb( dbConnection, romDetailsDict[ 'genres' ] )
	
	if threadDbConnection == None:
		dbConnection.CloseDb()
	
	
def GetAllFilesInDirectory( rootdir, romFilter ):

	includes = romFilter.split( ',' )
	# transform glob patterns (*.zip) to regular expressions
	includes = r'|'.join([fnmatch.translate(x) for x in includes])

	fileList = []
	for root, subFolders, files in os.walk(rootdir):
		files = [os.path.join(root, f) for f in files]
		files = [f for f in files if re.match(includes, f)]
		for fullName in files:
			relativePath = fullName[ ( len( rootdir ) + 1 ) : len( fullName ) ]
			fileList.append( relativePath )
	return fileList

	
def RemoveExtension( fileName ):

	# default remove extension function removes multiple dotted extensions, which we don't want.
	keepSearching = 1
	while keepSearching > 0:
		findIndex = fileName.rfind( '.', 0, len( fileName )-1 )
		extLength = len( fileName ) - findIndex
		if findIndex >= 0 and extLength <= 4:
			fileName = fileName[0:findIndex]
		else:
			keepSearching = 0
	return fileName

	
def PrepareRomName( fileNameNoExt ):

	# remove anything in brackets
	global removeBracketsExpression
	romName = removeBracketsExpression.sub( '', fileNameNoExt )
	
	# some roms start with a number in the filename, remove it
	global startingNumberMatcher
	romName = startingNumberMatcher.sub( '', romName )
	romName = romName.strip()
	return romName
	

def DetermineRomNameAndState( fullPath ):

	fileNameNoExt = RemoveExtension( os.path.basename( fullPath ) )
	romState = 0
	territory = 0
	
	global perfectRomMatcher
	if perfectRomMatcher.match( fileNameNoExt ):
		romState |= Config.ROMSTATE_PERFECT
	
	global territoryRegularExpressionMap
	for territoryId in territoryRegularExpressionMap.keys():
		regularExp = territoryRegularExpressionMap[ territoryId ]
		if regularExp.match( fileNameNoExt ):
			territory |= territoryId
	
	romName = PrepareRomName( fileNameNoExt )

	#print ( "Rom added : '" + romName + "' state " + str( romState ) + " territory " + str( territory ) )
	
	return ( romName, romState, territory )
	

	
def CheckForDuplicates( dbRows ):

	indicesAlreadyProcessed = set()

	for examineIndex in range( len( dbRows ) ):

		if examineIndex not in indicesAlreadyProcessed:
			romName = dbRows[ examineIndex ][ "romName" ]
	
			duplicateIndexList = set()
			duplicateIndexList.add( examineIndex )
			
			for findDuplicateIndex in range( examineIndex+1, len( dbRows ) ):
				duplicateRomName = dbRows[ findDuplicateIndex ][ "romName" ]
				if romName.lower() == duplicateRomName.lower():
					duplicateIndexList.add( findDuplicateIndex )
					
			indicesAlreadyProcessed.update( duplicateIndexList )
		
			bestVersionIndex = FindBestDuplicate( dbRows, duplicateIndexList )
			dbRows[ bestVersionIndex ][ "isBestVersion" ] = 1
			

def FindBestDuplicate( dbRows, duplicateIndexList ):

	if len( duplicateIndexList ) == 1:
		return list( duplicateIndexList )[0]
	else:
		# look for 'perfect image' first
		useThisIndexList = None
		
		perfectImageList = BuildPerfectImageList( dbRows, duplicateIndexList )
		if len( perfectImageList ) == 1:
			return perfectImageList[0]
		elif len( perfectImageList ) > 1:
			useThisIndexList = perfectImageList
		else:
			useThisIndexList = duplicateIndexList
			
		# look in territory priority order
		firstPreferredTerritoryIndex = -1
		selectedIndex = -1
		while selectedIndex < 0 and len( useThisIndexList ) > 0:
			selectedIndex = FindPreferredTerritory( dbRows, useThisIndexList )

			if selectedIndex >= 0:
				if firstPreferredTerritoryIndex < 0:
					firstPreferredTerritoryIndex = selectedIndex
				
				row = dbRows[ selectedIndex ]
				# dont use if is hacked / pirate
				if row[ "romState" ] & ( Config.ROMSTATE_PIRATE | Config.ROMSTATE_HACK ) > 0:
					useThisIndexList.remove( selectedIndex )
					selectedIndex = -1
	
		if selectedIndex < 0:
			return useThisIndexList[0]
		else:
			return selectedIndex
		
		
def BuildPerfectImageList( dbRows, duplicateIndexList ):

	perfectRomIndices = []
	for index in duplicateIndexList:
		row = dbRows[ index ]
		if row[ "romState" ] & Config.ROMSTATE_PERFECT > 0:
			perfectRomIndices.append( index )
		
	return perfectRomIndices
	
	
def FindPreferredTerritory( dbRows, duplicateIndexList ):

	for rowIndex in duplicateIndexList:
		row = dbRows[ rowIndex ]
		for territoryId in Config.config.territoryPriorityOrder:
			if row[ "territory" ] & territoryId > 0:
				return rowIndex
	return -1
	
	
	
