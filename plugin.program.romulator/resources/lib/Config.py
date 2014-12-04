
from xml.dom.minidom import parse
from xml.dom.minidom import getDOMImplementation
import XmlHelper
import re
import glob

from ast import literal_eval as make_tuple
import os, time

TERRITORY_USA = 1
TERRITORY_EUROPE = 2
TERRITORY_AUSTRALIA = 4
TERRITORY_CANADA = 8
TERRITORY_JAPAN = 16

ROMSTATE_PERFECT = 1
ROMSTATE_PIRATE = 2
ROMSTATE_HACK = 4


class Config(object):

	configFilePath = ''
	scraperCacheDirectory = ''
	scaperType = ''
	scaperImageQuality = ''
	RomItemCount = 10
	resourcesPath = ''
	dateFormatString = '%Y-%m-%d'
	zipToolPath = ''
	zipToolArgs = ''
	
	guiGameWindowSimilarGamesLimit = 75
	guiGameWindowDeveloperGamesLimit = 75
	guiGameWindowPublisherGamesLimit = 75
		
	territoryPriorityOrder = [ TERRITORY_USA, TERRITORY_EUROPE, TERRITORY_AUSTRALIA, TERRITORY_CANADA, TERRITORY_JAPAN ]
	imagePriorityOrder = [ 'super', 'screen', 'medium', 'small', 'thumb', 'icon', 'tiny' ]

	
	emulatorTypeMap = []

	
	def FormatDateString( self, isoDateString ):
	
		if isoDateString != None and len( isoDateString ) > 0:
			dateTimeObject = time.strptime( isoDateString, "%Y-%m-%d %H:%M:%S" )
			return time.strftime( self.dateFormatString, dateTimeObject )
		else:
			return ""

			
	def GetEmulatorByName( self, emuName ):
	
		for emulatorType in self.emulatorTypeMap:
			if emulatorType[ 'name' ] == emuName:
				return emulatorType
		return None
			
			
	def RemoveBadCharactersForFolderName( self, folderName ):
		
		return re.sub( '[\*\?\\\/\:\<\>\|]', '', folderName )
		
	
	def GetRomsImageCachePath( self, suffix ):
	
		return self.GetCachePath( 'roms', suffix )
		
		
	def GetCompaniesImageCachePath( self, suffix ):
	
		return self.GetCachePath( 'companies', suffix )
		
		
	def GetGenresImageCachePath( self, suffix ):
	
		return self.GetCachePath( 'genres', suffix )
		
	
	def GetCachePath( self, parentDir, suffix ):
	
		cacheDir = os.path.join( self.scraperCacheDirectory, self.RemoveBadCharactersForFolderName( parentDir ) )
		return os.path.join( cacheDir, self.RemoveBadCharactersForFolderName( suffix ) )
	

	def GetRomsImageCacheFile( self, suffix ):
	
		return self.GetCacheFile( 'roms', suffix )
		
		
	def GetCompaniesImageCacheFile( self, suffix ):
	
		return self.GetCacheFile( 'companies', suffix )
	

	def GetGenresImageCacheFile( self, suffix ):
	
		return self.GetCacheFile( 'genres', suffix )
	
		
	def GetCacheFile( self, parentDir, suffix ):
	
		for imageQualityName in self.imagePriorityOrder:
			searchPath = os.path.join( self.GetCachePath( parentDir, suffix ), imageQualityName + ".*" )
			fileList = glob.glob( searchPath )
			if len( fileList ) > 0:
				return fileList[0]
		return ''
	

	def GetImagePath( self, fileName ):
		
		return os.path.join( os.path.join( self.resourcesPath, "images" ), fileName )
		

	def Init( self, resourcesPath ):
	
		self.resourcesPath = resourcesPath
		self.configFilePath = os.path.join( resourcesPath, 'config.xml' )
		
		try:
			if ( os.path.isfile( self.configFilePath ) ):
				dom = parse( self.configFilePath )
				
				rootNode = XmlHelper.FindFirstChildNodeByTagName( dom, 'config' )

				displayNodeList = XmlHelper.FindChildNodesByTagName( rootNode, 'display' )
				if len( displayNodeList ) > 0:
					displayNode = displayNodeList[0]
					try:
						self.RomItemCount = int( displayNode.getAttribute( 'romItemCount' ) )
					except:
						pass
				
				dateTimeNodeList = XmlHelper.FindChildNodesByTagName( rootNode, 'datetime' )
				if len( dateTimeNodeList ) > 0:
					dateTimeNode = dateTimeNodeList[0]
					self.dateFormatString = dateTimeNode.getAttribute( 'format' )
				
				scraperNodeList = XmlHelper.FindChildNodesByTagName( rootNode, 'scraper' )
				if len( scraperNodeList ) > 0:
					scraperNode = scraperNodeList[0]
					self.scaperType = scraperNode.getAttribute( 'type' )
					self.scaperImageQuality = scraperNode.getAttribute( 'imageQuality' )
					self.scraperCacheDirectory = scraperNode.getAttribute( 'cacheDirectory' )
				
				launcherNodeList = XmlHelper.FindChildNodesByTagName( rootNode, 'ziptool' )
				if len( launcherNodeList ) > 0:
					launcherNode = launcherNodeList[0]
					self.zipToolPath = launcherNode.getAttribute( 'path' )
					self.zipToolArgs = launcherNode.getAttribute( 'args' )
				
				# read in supported platforms
				emulatorNodeList = XmlHelper.FindChildNodesByTagName( rootNode, 'emulator' )

				for emulatorNode in emulatorNodeList:
					name = emulatorNode.getAttribute('name')
					romsPath = emulatorNode.getAttribute('romsPath')
					romFilter = emulatorNode.getAttribute('romFilter')
					exe_file = emulatorNode.getAttribute('exe_file')
					exe_args = emulatorNode.getAttribute('exe_args')
					giantBombPlatformId = emulatorNode.getAttribute('giantBombPlatformId')
					
					emuMap = { "name": name, "romsPath":romsPath, "romFilter":romFilter, "exe_file":exe_file, "exe_args":exe_args,
						"giantBombPlatformId":giantBombPlatformId }
					self.emulatorTypeMap.append( emuMap )
		except:
			pass
			
		if len( self.scraperCacheDirectory ) == 0:
			self.scraperCacheDirectory = os.path.join( resourcesPath, 'cache' )
				
				
	def AddEmulator( self, platform, roms_dir, romFilter, exe_file, exe_args ):
	
		emuMap = { "name": platform, "romsPath":roms_dir, "romFilter":romFilter, "exe_file":exe_file, "exe_args":exe_args }
		self.emulatorTypeMap.append( emuMap )
		
		self.SaveConfig()
		
		
	def SaveConfig( self ):
	
		impl = getDOMImplementation()
		newdoc = impl.createDocument(None, "config", None)
		top_element = newdoc.documentElement
		
		displayElement = newdoc.createElement( 'display' )
		displayElement.setAttribute( 'romItemCount', str( self.RomItemCount ) )
		top_element.appendChild(displayElement)
		
		scraperElement = newdoc.createElement( 'scraper' )
		scraperElement.setAttribute( 'type', self.scaperType )
		scraperElement.setAttribute( 'imageQuality', self.scaperImageQuality )
		scraperElement.setAttribute( 'cacheDirectory', self.scraperCacheDirectory )
		top_element.appendChild(scraperElement)
		
		dateTimeElement = newdoc.createElement( 'datetime' )
		dateTimeElement.setAttribute( 'format', self.dateFormatString )
		top_element.appendChild(dateTimeElement)

		launcherNode = newdoc.createElement( 'ziptool' )
		launcherNode.setAttribute( 'path', self.zipToolPath )
		launcherNode.setAttribute( 'args', self.zipToolArgs )
		top_element.appendChild(launcherNode)	
		
		newdoc.appendChild( top_element )
		
		for emulatorType in self.emulatorTypeMap:
			emulatorElement = newdoc.createElement( 'emulator' )
			for emuKey in emulatorType:
				emulatorElement.setAttribute( emuKey, emulatorType[ emuKey ] )
			top_element.appendChild(emulatorElement)

		f = open( self.configFilePath, 'w' )
		f.write( newdoc.toprettyxml() )
		f.close()
		

config = Config()

