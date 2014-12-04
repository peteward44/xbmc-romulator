import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import urllib, urllib2, logging
import sys
import Config


class XbmcDirectoryListing( object ):

	directoryItemList = []
	

	def FormatArgumentList( self, argumentDictionary ):
		u = sys.argv[0];
		if len( argumentDictionary ) > 0:
			u += "?" + urllib.urlencode( argumentDictionary )
		return u

		
	# adds an item with a context menu - you have to format the commands yourself.
	# example: AddContextMenuItem( 'View Favourites', '', 'icon.png', { 'mode':'browse', 'view':'favourites' },
	#					[( 'Refresh', 'XBMC.RunPlugin(' + FormatArgumentList( { 'mode': 'refresh', 'view':'all' } ) + ')',)], True, False )
	def AddContextMenuItemRaw( self, displayLabel, line2, imageName, argumentDictionary, contextMenuCommands, isFolder, addFolderToHierarchy ):
	
		listitem = xbmcgui.ListItem(label = displayLabel, label2 = line2, iconImage = imageName, thumbnailImage = imageName)
		if addFolderToHierarchy == True:
			argumentDictionary[ 'addFolderToHierarchy' ] = '1'
		else:
			argumentDictionary[ 'addFolderToHierarchy' ] = '0'
		argumentDictionary[ 'previousPageHandle' ] = str( sys.argv[1] )
		u = self.FormatArgumentList( argumentDictionary )
		if contextMenuCommands != None:
			listitem.addContextMenuItems(contextMenuCommands)
		self.directoryItemList.append( ( u, listitem, isFolder ) )
		return listitem
		
	
	# simpler version of the context menu, all commands assume they are XBMC.RunPlugin() commands
	# example: AddContextMenuItem( 'View Favourites', '', 'icon.png', { 'mode':'browse', 'view':'favourites' },
	#					[( 'Refresh', { 'mode': 'refresh', 'view':'all' },)], True, False )
	def AddContextMenuItem( self, displayLabel, line2, imageName, argumentDictionary, contextMenuCommandList, isFolder, addFolderToHierarchy ):
		
		if contextMenuCommandList != None:
			rawContextMenuCommands = []
			for ( cookedName, cookedCommandDictionary ) in contextMenuCommandList:
				tuple = ( cookedName, 'XBMC.RunPlugin(' + self.FormatArgumentList( cookedCommandDictionary ) + ')',)
				rawContextMenuCommands.append( tuple )
			return self.AddContextMenuItemRaw( displayLabel, line2, imageName, argumentDictionary, rawContextMenuCommands, isFolder, addFolderToHierarchy )
		else:
			return self.AddContextMenuItemRaw( displayLabel, line2, imageName, argumentDictionary, None, isFolder, addFolderToHierarchy )

		
	# adds an item with no context menu
	# example: AddItem( "Settings", '', 'settings.png', { 'mode':'settings' }, True, True )
	def AddItem( self, displayLabel, line2, imageName, argumentDictionary, isFolder, addFolderToHierarchy ):
	
		return self.AddContextMenuItemRaw( displayLabel, line2, imageName, argumentDictionary, None, isFolder, addFolderToHierarchy )

		
	def AddPreviousPageItem( self, startItemIndex, itemCount, itemDictionary ):

		if startItemIndex > 0:
			prevIndex = startItemIndex - itemCount
			if prevIndex < 0:
				prevIndex = 0
			itemDictionary[ 'startItemIndex' ] = str(prevIndex)
			itemDictionary[ 'itemCount' ] = str(itemCount)
			listitem = self.AddItem( "Previous Page...", '', Config.config.GetImagePath( 'previous.png' ), itemDictionary, True, False )
#			listitem.select( True )
			return listitem
		return None


	def AddNextPageItem( self, startItemIndex, itemCount, totalItemCount, itemDictionary ):

		if ( startItemIndex + itemCount ) < totalItemCount:
			itemDictionary[ 'startItemIndex' ] = str( startItemIndex + itemCount )
			itemDictionary[ 'itemCount' ] = str( itemCount )
			listitem = self.AddItem( "Next Page...", '', Config.config.GetImagePath( 'next.png' ), itemDictionary, True, False )
#			listitem.select( True )
			return listitem
		return None


	# call this when all items are added
	def Commit( self, addFolderToHierarchy ):
		itemCount = len( self.directoryItemList )
		if itemCount > 0:
			try:
				xbmcplugin.addDirectoryItems( handle = int(sys.argv[1]), items = self.directoryItemList, totalItems = itemCount )
				xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
			except Exception as e:
				logging.exception(e)
		try:
#			print "ADD FOLDER: " + str( addFolderToHierarchy )
			updateListingTrue = not addFolderToHierarchy
			xbmcplugin.endOfDirectory( handle = int(sys.argv[1]), updateListing = updateListingTrue, cacheToDisc = False )
		except Exception as e:
			logging.exception(e)
		try:
			for ( u, listitem, isFolder ) in self.directoryItemList:
				del listitem
			del self.directoryItemList[:]
		except Exception as e:
			logging.exception(e)
			
			
	#def end_xbmc_action():
	#	xbmcplugin.setResolvedUrl( int(sys.argv[1]), True, xbmcgui.ListItem() )
	#	pass
			
