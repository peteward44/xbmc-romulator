
import xbmc, xbmcgui
import sys
import DbConnection, EntryPoint, Config
import RomScanner


ACTION_CANCEL_DIALOG = (9,10,51,92,110)

CONTROL_BUTTON_PLAYGAME = 3000
CONTROL_WRAPLIST_SIMILARGAMES = 59
CONTROL_BUTTON_ADDFAVOURITE = 25

ITEMTYPE_SIMILAR = 1
ITEMTYPE_DEVELOPER = 2
ITEMTYPE_PUBLISHER = 3


def CreateWindow( addonInstallPath, skin, romId ):
	try:
		gid = GuiGameInfoWindow("GuiGameInfoWindow.xml", addonInstallPath, romId=romId )
	except:
		gid = GuiGameInfoWindow("GuiGameInfoWindow.xml", addonInstallPath, romId=romId )
	
	del gid


class GuiGameInfoWindow(xbmcgui.WindowXMLDialog):

	romId = None
	WINDOW = None

	
	def getControlById(self, controlId):
		try:
			control = self.getControl(controlId)
		except: 
#			Logutil.log("Control with id: %s could not be found. Check WindowXML file." %str(controlId), util.LOG_LEVEL_ERROR)
#			self.writeMsg(util.localize(35025) %str(controlId))
			return None
		
		return control


	def __init__( self, XMLname, fallbackPath, romId ):
	
		self.romId = romId
#		xbmcgui.WindowXMLDialog.__init__( self, XMLname, fallbackPath )
#		super( GuiGameInfoWindow, self ).__init__( *args, **kwargs )

		self.doModal()
		

	def onInit(self):
	
		self.WINDOW = xbmcgui.Window( 10000 )
	
		# Put your List Populating code/ and GUI startup stuff here
		control = self.getControlById(CONTROL_BUTTON_PLAYGAME)
		if(control != None):
			self.setFocus(control)
			
		#if(selectedGame == None):
		#	Logutil.log("selectedGame == None in showGameInfo", util.LOG_LEVEL_WARNING)
		#	return

		self.PopulateFields( self.romId, False, True )
		
		
	def SetProperty( self, name, value ):
	
		if value != None:
			self.WINDOW.setProperty( name, value )
		else:
			self.WINDOW.setProperty( name, "" )
		
		
	def MergeNamesAsString( self, dataDictList ):
	
		string = ""
		if dataDictList != None:
			for dataDict in dataDictList:
				if len( string ) > 0:
					string = string + ", "
				string = string + dataDict[ 'name' ]
		return string


	def AddItem( self, romId, name, image, itemType ):
	
		item = xbmcgui.ListItem( label=name, label2="",
			iconImage=image, thumbnailImage=image )
		item.setProperty( 'romId', str( romId ) )
		item.setProperty( 'itemType', str( itemType ) )
		self.addItem(item)
	
	
	def UpdateSimilarGamesText( self ):
		
		string = ""
		listPos = self.getCurrentListPosition()
		if ( listPos >= 0 ):
			listItem = self.getListItem( listPos )
#			print "List item: " + str( listPos )
			typeProp = listItem.getProperty( 'itemType' )
			if typeProp != None and len( typeProp ) > 0:
				typePropInt = int( typeProp )
				if ( typePropInt == ITEMTYPE_SIMILAR ):
					string = "Similar games:"
				elif ( typePropInt == ITEMTYPE_DEVELOPER ):
					string = "From the same developers:"
				elif ( typePropInt == ITEMTYPE_PUBLISHER ):
					string = "From the same publishers:"
		self.SetProperty( 'listDescription', string )
	
	
	def AddIfDoesNotExist( self, primaryRomId, gameList, romDict, itemType ):
	
		if romDict[ 'id' ] == primaryRomId:
			return False
			
		for gameObj in gameList:
			( gameRomDict, gameItemType ) = gameObj
			if gameRomDict[ 'id' ] == romDict[ 'id' ]:
				return False
	
		gameList.append( ( romDict, itemType, ) )
		return True
	
	
	def PopulateFields( self, romId, doClearList, doScrape ):

		dbConnection = DbConnection.DbConnection()
		romDict = dbConnection.GetRomById( romId )

		# then add similar games as list items
		if doClearList == True:
			if self.getListSize() > 0:
				self.clearList()
				
		# remove item already in there if first used
		if self.getListSize() > 0:
			self.removeItem(0)
		
		self.SetProperty( 'label', romDict[ "name" ] )
		self.SetProperty( 'gameinfobig', Config.config.GetRomsImageCacheFile( romDict[ "name" ] ) )
		self.SetProperty( 'plot', romDict["description"] )
		self.SetProperty( 'releasedate', Config.config.FormatDateString( romDict["releaseDate"] ) )

		developerDictList = dbConnection.GetDevelopersByRomId( romId )
		self.SetProperty( 'developer', self.MergeNamesAsString( developerDictList ) )
		
		publisherDictList = dbConnection.GetPublishersByRomId( romId )
		self.SetProperty( 'publisher', self.MergeNamesAsString( publisherDictList ) )
		
		genreDictList = dbConnection.GetGenresByRomId( romId )
		self.SetProperty( 'genre', self.MergeNamesAsString( genreDictList ) )
		
		addFavButton = self.getControlById( CONTROL_BUTTON_ADDFAVOURITE )
		
		if romDict[ 'isFavourite' ] == 1:
			addFavButton.setSelected( True )
		else:
			addFavButton.setSelected( False )

		# set up similar games list
		similarGamesDict = dbConnection.GetRomSimilarGames( romId, Config.config.guiGameWindowSimilarGamesLimit )

		otherGamesList = []

		for sgDict in similarGamesDict:
			# for each similar game, see if it exists in the main db.
			otherRomDataDict = dbConnection.GetRomByGiantBombId( sgDict[ "otherRomGiantBombId" ] )
			
			if otherRomDataDict != None: # this similar game exists in DB
				self.AddIfDoesNotExist( romId, otherGamesList, otherRomDataDict, ITEMTYPE_SIMILAR )
	
#		self.AddItem( -1, "", "", 0 )

		# add roms from same developers to similar games list
		if developerDictList != None:
			for dataDict in developerDictList:
				( otherRomDataDictList, developerCount ) = dbConnection.GetRomsByDeveloperId( dataDict[ 'id' ], 0, Config.config.guiGameWindowDeveloperGamesLimit )
				if otherRomDataDictList != None:
					for otherRomDataDict in otherRomDataDictList:
						self.AddIfDoesNotExist( romId, otherGamesList, otherRomDataDict, ITEMTYPE_DEVELOPER )
						
#		self.AddItem( -1, "", "", 0 )

		# same for publisher
		if publisherDictList != None:
			for dataDict in publisherDictList:
				( otherRomDataDictList, publisherCount ) = dbConnection.GetRomsByPublisherId( dataDict[ 'id' ], 0, Config.config.guiGameWindowPublisherGamesLimit )
				if otherRomDataDictList != None:
					for otherRomDataDict in otherRomDataDictList:
						self.AddIfDoesNotExist( romId, otherGamesList, otherRomDataDict, ITEMTYPE_PUBLISHER )

		for game in otherGamesList:
			( otherRomDataDict, itemType ) = game
			self.AddItem( otherRomDataDict[ "id" ], otherRomDataDict[ "name" ], Config.config.GetRomsImageCacheFile( otherRomDataDict[ "name" ] ), itemType )

		dbConnection.CloseDb()
		
		self.UpdateSimilarGamesText()
		
		if doScrape == True:
			if romDict[ 'isScraped' ] != 1:
				self.doClearList = doClearList
				self.DoScrape( romId, romDict )
				
				
	def OnScrapeComplete( self, success, progressBar ):
		if success == True:
			self.PopulateFields( self.romId, self.doClearList, False )
		del progressBar
		

	def DoScrape( self, romId, romDict ):
	
		self.romId = romId
		progressBar = xbmcgui.DialogProgress()
		progressBar.create('Scraping information...')
		#				print "DOING SCRAPE..."
		romEmulatorType = Config.config.GetEmulatorByName( romDict[ 'emulatorName' ] )
		RomScanner.ScrapeRomAsync( romId, romDict[ "name" ], romEmulatorType[ 'giantBombPlatformId' ], self.OnScrapeComplete, progressBar )


	def onAction(self, action):
	
	#	print "ACTION: " + str( action.getId() )
	
		#if ( action.getId() == 1 or action.getId() == 2  ):
		self.UpdateSimilarGamesText()
	
		if(action.getId() in ACTION_CANCEL_DIALOG):
			self.close()

			
	def onClick(self, controlID):
	
		if (controlID == CONTROL_BUTTON_PLAYGAME):			
			xbmc.executebuiltin( 'XBMC.RunPlugin(' + sys.argv[0] + '?mode=launch&romid=' + str( self.romId ) + ' )' )
			self.close()
			
		elif ( controlID == CONTROL_WRAPLIST_SIMILARGAMES ):
			# call PopulateFields with the new rom ID
			pos = self.getCurrentListPosition()
			if pos >= 0:
				selectedItem = self.getListItem(pos)
				if selectedItem != None:
					romId = selectedItem.getProperty( 'romId' )
					if romId != None:
						romIdInt = int( romId )
						if romIdInt >= 0:
							self.PopulateFields( romIdInt, True, True )
							
		elif ( controlID == CONTROL_BUTTON_ADDFAVOURITE ):
			addFavButton = self.getControlById( CONTROL_BUTTON_ADDFAVOURITE )
			if addFavButton != None:
				isSelected = addFavButton.isSelected()
	#			print "IS FAVOURITE: " + str( isSelected )
				dbConnection = DbConnection.DbConnection()
				dbConnection.SetRomFavourite( self.romId, isSelected )
				dbConnection.CloseDb()
			

	def onFocus(self, controlID):
		pass


		