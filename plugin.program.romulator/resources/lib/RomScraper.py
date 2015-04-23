
from threading import Thread
from threading import Lock
import urllib2
import urllib
import time
import os
import Config
import logging
import re
import time
import XmlHelper

import xml
from xml.dom import minidom


#API_KEYS = {'%VGDBAPIKey%' : 'Zx5m2Y9Ndj6B4XwTf83JyKz7r8WHt3i4',
#			'%GIANTBOMBAPIKey%' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
#			'%ARCHIVEAPIKEY%' : 'VT7RJ960FWD4CC71L0Z0K4KQYR4PJNW8'}

			
romScraper = None


def GetRomScraper():
	global romScraper
	if romScraper == None:
		romScraper = RomScraper()
	return romScraper
	

def FormatPlatformsData( dom ):
	
	ret = []
	
	if dom != None:
		platformList = dom.getElementsByTagName( 'platform' )
		for platform in platformList:
			
			platformData = {}
			
			platformData[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( platform, 'name' )
			platformData[ 'abbreviation' ] = XmlHelper.FindFirstDataInXmlTagList( platform, 'abbreviation' )
			platformData[ 'giantBombPlatformId' ] = XmlHelper.FindFirstDataInXmlTagList( platform, 'id' )
			
			ret.append( platformData )
			
	return ret


class RomScraper(object):

	def __init__( self ):
		pass
			

	def SearchForRomBlock( self, romName, giantBombPlatformId ):

		try:
			return self.DoSearchForRom( romName, giantBombPlatformId )
		except Exception as e:
			logging.exception(e)
		return None
	
	
	def GetRomDetailsBlock( self, romName, giantBombApiDetailsUrl ):

		try:
			return self.DoGetRomDetails( romName, giantBombApiDetailsUrl )
		except Exception as e:
			logging.exception(e)
		return None
		
		
	def SearchForPlatformBlock( self, platformName ):
		
		try:
			return self.DoSearchForPlatformBlock( platformName )
		except Exception as e:
			logging.exception(e)
		return None

		
	def GetCompanyDetailsBlock( self, giantBombCompanyUrl ):
		
		try:
			return self.DoGetCompanyDetailsBlock( giantBombCompanyUrl )
		except Exception as e:
			logging.exception(e)
		return None
		

	def GetGenreDetailsBlock( self, giantBombCompanyUrl ):
		
		try:
			return self.DoGetGenreDetailsBlock( giantBombCompanyUrl )
		except Exception as e:
			logging.exception(e)
		return None
		
		
	def ParseSimilarGamesData( self, xmlTag ):
		
		ret = []
		if xmlTag != None:
			gameTags = XmlHelper.FindChildNodesByTagName( xmlTag, 'game' )
			for gameTag in gameTags:
				dict = {}
				dict[ 'giantBombRomId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
				dict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
				ret.append( dict )
			
		return ret
		
		
	def TestXmlDocumentErrorStatus( self, xmlDoc ):
			
		errorTagResultsList = xmlDoc.getElementsByTagName( "error" )
		if len( errorTagResultsList ) == 1:
			for childTag in errorTagResultsList[0].childNodes:
				if childTag.nodeType == childTag.TEXT_NODE or childTag.nodeType == childTag.CDATA_SECTION_NODE:
					if childTag.data == "OK":
						return True
		return False
		
		
	def ParseSearchXml( self, text, giantBombPlatformId ):
	
		xmlDocument = minidom.parseString( text )
		if self.TestXmlDocumentErrorStatus( xmlDocument ) == False:
			raise Exception( "Invalid response for search XML" )

		gameTagResultList = xmlDocument.getElementsByTagName( "game" )
		
#		print "ROM SEARCH TEXT: " + text
		
		resultDictList = []
		for gameTag in gameTagResultList:
			romDict = {}
			
			romDict[ 'giantBombRomId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
			romDict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
			romDict[ 'aliases' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'aliases' )
			platformList = XmlHelper.FindFirstChildNodeByTagName( gameTag, 'platforms' )
			if platformList != None:
				romDict[ 'platforms' ] = FormatPlatformsData( platformList )
			romDict[ 'giantBombApiDetailsUrl' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'api_detail_url' )
			
			# filter by giantBombPlatformId (can't do this directly in the url search string)
			foundPlatformId = False
			if len( giantBombPlatformId ) > 0:
				for platform in romDict[ 'platforms' ]:
#					print "Platform: " + platform[ 'name' ]
					if int( platform[ 'giantBombPlatformId' ] ) == int( giantBombPlatformId ):
						foundPlatformId = True
						break
			else:
				foundPlatformId = True
				
			if foundPlatformId == True:
				resultDictList.append( romDict )
		
		return resultDictList
		
		
	def ParsePlatformSearchXml( self, text ):
	
		xmlDocument = minidom.parseString( text )
		if self.TestXmlDocumentErrorStatus( xmlDocument ) == False:
			raise Exception( "Invalid response for search platform XML" )

		gameTagResultList = xmlDocument.getElementsByTagName( "platform" )
		
		#print "PLATFORM SEARCH TEXT: " + text
		
		resultDictList = []
		for gameTag in gameTagResultList:
			romDict = {}
			
			romDict[ 'giantBombPlatformId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
			romDict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
			romDict[ 'abbreviation' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'abbreviation' )
			romDict[ 'description' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'deck' )

			resultDictList.append( romDict )
		
		return resultDictList
		
		
	def ParseDeveloperData( self, developersNode, xmlNodeName ):
		
		devList = []
		if developersNode is not None:
			for developerNode in XmlHelper.FindChildNodesByTagName( developersNode, xmlNodeName ):
				
				dev = {}
				dev[ 'giantBombId' ] = XmlHelper.FindFirstDataInXmlTagList( developerNode, 'id' )
				dev[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( developerNode, 'name' )
				dev[ 'apiurl' ] = XmlHelper.FindFirstDataInXmlTagList( developerNode, 'api_detail_url' )
				
				devList.append( dev )
				
		return devList
		
		
	def SaveImageToRomCache( self, cacheDirectory, romName, imageXmlNode ):
		# pick an image priority
		for imageSizeName in Config.config.imagePriorityOrder:
			try:	
				apiUrl = XmlHelper.FindFirstDataInXmlTagList( imageXmlNode, imageSizeName + '_url' )
				if apiUrl is not None and len( apiUrl ) > 0:
					imageUrl = apiUrl
					imageFilenameNoExtension = imageSizeName
					
#					print "[" + romName + "] TRYING " + imageUrl + " FILE: " + imageFilenameNoExtension

					if imageUrl is not None and imageFilenameNoExtension is not None and len( imageUrl ) > 0 and len( imageFilenameNoExtension ) > 0:
						if not os.path.exists( cacheDirectory ):
							os.makedirs( cacheDirectory )

						# get image file extension from imageUrl
						( dummy, imageExtension ) = os.path.splitext( imageUrl )
						imageFilename = imageFilenameNoExtension + imageExtension
						romImageFilename = os.path.join( cacheDirectory, imageFilename )
						
						if os.path.isfile( romImageFilename ):
							return # file already exists
						
						if imageUrl != None and len( imageUrl ) > 0:
							imageResp = urllib2.urlopen( imageUrl )
							imageData = imageResp.read()
							if len( imageData ) > 0:
								imageFile = open( romImageFilename, 'wb' )
								imageFile.write( imageData )
								imageFile.close()
								return

			except Exception as e:
				logging.exception(e)
			#	print ( "Error retrieving rom image: ", e )

		
	def ParseRomDetailsXml( self, romName, text ):
	
		xmlDocument = minidom.parseString( text )
		if self.TestXmlDocumentErrorStatus( xmlDocument ) == False:
			raise Exception( "Invalid response for get rom details XML" )

		#print "XML: " + text
			
		gameTagResultList = xmlDocument.getElementsByTagName( "results" )
		
		if len( gameTagResultList ) == 0:
			raise Exception( "Could not find result for rom" )
		if len( gameTagResultList ) > 1:
			raise Exception( "Unexpected number of results for rom" )
			
		gameTag = gameTagResultList[0]
		
		romDict = {}

		#romDict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
		romDict[ 'description' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'deck' )
		romDict[ 'giantBombRomId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
		
		 # string is provided in ISO standard format anyway so can be stored in DB like that
		romDict[ 'releaseDate' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'original_release_date' )
		
		# similar games are map of { 'giantBombRomId', 'name' }
		romDict[ 'similarGames' ] = self.ParseSimilarGamesData( XmlHelper.FindFirstChildNodeByTagName( gameTag, 'similar_games' ) )

		romDict[ 'developers' ] = self.ParseDeveloperData( XmlHelper.FindFirstChildNodeByTagName( gameTag, 'developers' ), 'company' )
		romDict[ 'publishers' ] = self.ParseDeveloperData( XmlHelper.FindFirstChildNodeByTagName( gameTag, 'publishers' ), 'publisher' )
		romDict[ 'genres' ] = self.ParseDeveloperData( XmlHelper.FindFirstChildNodeByTagName( gameTag, 'genres' ), 'genre' )
		
		imageNode = XmlHelper.FindFirstChildNodeByTagName( gameTag, 'image' )		
		if imageNode is not None:
			self.SaveImageToRomCache( Config.config.GetRomsImageCachePath( romName ), romName, imageNode )
			
		return romDict
		
		
	def ParseCompanyDetailsXml( self, text ):
	
		xmlDocument = minidom.parseString( text )
		if self.TestXmlDocumentErrorStatus( xmlDocument ) == False:
			raise Exception( "Invalid response for get company details XML" )

#		print "XML: " + text
			
		gameTagResultList = xmlDocument.getElementsByTagName( "results" )
		
		if len( gameTagResultList ) == 0:
			raise Exception( "Could not find result for company" )
		if len( gameTagResultList ) > 1:
			raise Exception( "Unexpected number of results for company" )
			
		gameTag = gameTagResultList[0]
		
		romDict = {}

		romDict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
		romDict[ 'description' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'deck' )
		romDict[ 'giantBombId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
		romDict[ 'foundedDate' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'date_founded' )
		
		imageNode = XmlHelper.FindFirstChildNodeByTagName( gameTag, 'image' )		
		if imageNode is not None:
			self.SaveImageToRomCache( Config.config.GetCompaniesImageCachePath( romDict[ 'name' ] ), romDict[ 'name' ], imageNode )

		return romDict
		
		
	def ParseGenreDetailsXml( self, text ):
	
		xmlDocument = minidom.parseString( text )
		if self.TestXmlDocumentErrorStatus( xmlDocument ) == False:
			raise Exception( "Invalid response for get genre details XML" )

#		print "XML: " + text
			
		gameTagResultList = xmlDocument.getElementsByTagName( "results" )
		
		if len( gameTagResultList ) == 0:
			raise Exception( "Could not find result for genre" )
		if len( gameTagResultList ) > 1:
			raise Exception( "Unexpected number of results for genre" )
			
		gameTag = gameTagResultList[0]
		
		romDict = {}

		romDict[ 'name' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'name' )
		romDict[ 'description' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'deck' )
		romDict[ 'giantBombId' ] = XmlHelper.FindFirstDataInXmlTagList( gameTag, 'id' )
	
		imageNode = XmlHelper.FindFirstChildNodeByTagName( gameTag, 'image' )
		if imageNode is not None:
			self.SaveImageToRomCache( Config.config.GetGenresImageCachePath( romDict[ 'name' ] ), romDict[ 'name' ], imageNode )

		return romDict
		
		
	def DoSearchForRom( self, romName, giantBombPlatformId ):
	
		romDictList = []
		theurl = self.BuildSearchUrl( romName )
		resp = urllib2.urlopen( theurl )
		text = resp.read()
		if len( text ) > 0:
			romDictList = self.ParseSearchXml( text, giantBombPlatformId )
		else:
			raise Exception( "Search for '" + romName + "' received empty response" )
		
		return romDictList
		
		
	def DoSearchForPlatformBlock( self, platformName ):
	
		romDictList = []
		# search by name first, then by abbreviation
		theurl = self.BuildPlatformSearchUrl( platformName, 1 )
		resp = urllib2.urlopen( theurl )
		text = resp.read()
		if len( text ) > 0:
			romDictList = self.ParsePlatformSearchXml( text )
			
			if len( romDictList ) == 0:
				# Attempt search by abbreviation
				theurl = self.BuildPlatformSearchUrl( platformName, 2 )
				resp = urllib2.urlopen( theurl )
				text = resp.read()
				if len( text ) > 0:
					romDictList = self.ParsePlatformSearchXml( text )
				else:
					raise Exception( "Search for '" + platformName + "' received empty response" )
		else:
			raise Exception( "Search for '" + platformName + "' received empty response" )
		
		return romDictList
		
			
	def DoGetRomDetails( self, romName, giantBombApiDetailsUrl ):
	
		romDict = {}
		theurl = self.BuildGetRomDetailsUrl( giantBombApiDetailsUrl )
		resp = urllib2.urlopen( theurl )
		text = resp.read()
		if len( text ) > 0:
			romDict = self.ParseRomDetailsXml( romName, text )
		else:
			raise Exception( "Get Rom Details for URL '" + giantBombApiDetailsUrl + "' received empty response" )
		
		return romDict
		
		
	def DoGetCompanyDetailsBlock( self, giantBombCompanyUrl ):
		
		romDict = {}
		theurl = self.BuildGetCompanyDetailsUrl( giantBombCompanyUrl )
		resp = urllib2.urlopen( theurl )
		text = resp.read()
		if len( text ) > 0:
			romDict = self.ParseCompanyDetailsXml( text )
		else:
			raise Exception( "Get Company Details for URL '" + giantBombCompanyUrl + "' received empty response" )
		
		return romDict
		
		
	def DoGetGenreDetailsBlock( self, giantBombCompanyUrl ):
		
		romDict = {}
		theurl = self.BuildGetGenreDetailsUrl( giantBombCompanyUrl )
		resp = urllib2.urlopen( theurl )
		text = resp.read()
		if len( text ) > 0:
			romDict = self.ParseGenreDetailsXml( text )
		else:
			raise Exception( "Get Genre Details for URL '" + giantBombCompanyUrl + "' received empty response" )
		
		return romDict
		
		
	def BuildSearchUrl( self, romName ):
	
	# http://www.giantbomb.com/api/documentation#toc-0-15
	
		url = 'http://www.giantbomb.com/api/search/'
		values = {
			'api_key' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
			'format' : 'xml',
			'query' : romName,
			'limit' : '100',
			'resources' : 'game',
			'field_list' : 'platforms,id,name,aliases,api_detail_url' }
		
		valueData = urllib.urlencode( values )
		finalUrl = url + '?' + valueData
#		print ( "Search rom URL: " + finalUrl )
		return finalUrl
		
		
	def BuildPlatformSearchUrl( self, platformName, searchType ):
	
	# http://www.giantbomb.com/api/documentation#toc-0-15
	
		filterName = ''
		if searchType == 1:
			filterName = 'name:'
		elif searchType == 2:
			filterName = 'abbreviation:'
		# filter by aliases doesn't work
#		elif searchType == 3:
#			filterName = 'aliases:'
		else:
			raise Exception( "Invalid search type specified for BuildPlatformSearchUrl" )
			
		url = 'http://www.giantbomb.com/api/platforms/'
		values = {
			'api_key' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
			'format' : 'xml',
			'filter' : filterName + platformName,
			'limit' : '10',
			'field_list' : 'abbreviation,id,name,deck,aliases' }
		
		valueData = urllib.urlencode( values )
		finalUrl = url + '?' + valueData
#		print ( "Search platform URL: " + finalUrl )
		return finalUrl
		
		
	def BuildGetRomDetailsUrl( self, giantBombApiDetailsUrl ):
	
	# http://www.giantbomb.com/api/documentation#toc-0-15
	
#		url = 'http://www.giantbomb.com/api/games/'
		url = giantBombApiDetailsUrl
		values = {
			'api_key' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
			'format' : 'xml',
			'field_list' : 'name,deck,original_release_date,similar_games,image,images,publishers,developers,genres,platforms,id' }
		
		valueData = urllib.urlencode( values )
		finalUrl = url + '?' + valueData
#		print ( "Rom details URL: " + finalUrl )
		return finalUrl
		
		
	def BuildGetCompanyDetailsUrl( self, giantBombCompanyUrl ):

		# bug in giant bomb database: need to replace /developer/ portion of URL with /company/
		url = giantBombCompanyUrl
		url = url.replace( '/developer/', '/company/' )
		url = url.replace( '/publisher/', '/company/' )
		values = {
			'api_key' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
			'format' : 'xml',
			'field_list' : 'name,deck,date_founded,aliases,image' }
		
		valueData = urllib.urlencode( values )
		finalUrl = url + '?' + valueData
#		print ( "Company details URL: " + finalUrl )
		return finalUrl
		

	def BuildGetGenreDetailsUrl( self, giantBombCompanyUrl ):

		url = giantBombCompanyUrl
		values = {
			'api_key' : '279442d60999f92c5e5f693b4d23bd3b6fd8e868',
			'format' : 'xml',
			'field_list' : 'name,deck,aliases,image' }
		
		valueData = urllib.urlencode( values )
		finalUrl = url + '?' + valueData
#		print ( "Genre details URL: " + finalUrl )
		return finalUrl
		
		