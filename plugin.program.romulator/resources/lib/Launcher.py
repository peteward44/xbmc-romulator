
import xbmc, os, sys

	
def UnFullScreenXBMC():
	#this minimizes xbmc some apps seems to need it
	try:
		xbmc.executehttpapi("Action(199)")
	except:
		xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')


def FullScreenXBMC():
	#Logutil.log("Toggle to Full Screen mode", util.LOG_LEVEL_INFO)
	#this brings xbmc back
	try:
		xbmc.executehttpapi("Action(199)")
	except:
		xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"togglefullscreen"},"id":"1"}')
		

def UnZipRom( zippedFilePath ):

	if os.path.isfile( Config.config.zipToolPath ):
		
		formattedArgs = Config.config.zipToolArgs
		formattedArgs = formattedArgs.replace( "%IN%", '"' + zippedFilePath + '"' )
		formattedArgs = formattedArgs.replace( "%OUT%", '"' + tempOutPath + '"' )

		cmd = Config.config.zipToolPath + " " + formattedArgs
		os.system( cmd.encode(sys.getfilesystemencoding()) )
		
	return zippedFilePath
		
		
def BuildCmd( emuDict, romDataDictionary, unzippedRomFilePath ):

	romArgs = emuDict[ 'exe_args' ]
	romArgs = romArgs.replace( "%ROM%", '"' + unzippedRomFilePath + '"' )
	cmd = emuDict[ 'exe_file' ] + " " + romArgs
	return cmd


def LaunchRom( emuDict, romDataDictionary ):

	#stop Player (if playing)
	if(xbmc.Player().isPlayingVideo()):
		xbmc.Player().stop()

	screenMode = xbmc.getInfoLabel("System.Screenmode")
	isFullScreen = screenMode.endswith("Full Screen")
	
	if isFullScreen == True:
		UnFullScreenXBMC()
	
	unzippedRomFilePath = UnZipRom( romDataDictionary[ 'fullPath' ] )
	cmd = BuildCmd( emuDict, romDataDictionary, unzippedRomFilePath )
	print "Launching rom with command line: " + cmd
	os.system( cmd.encode(sys.getfilesystemencoding()) )
	
	if isFullScreen == True:
		FullScreenXBMC()
	
	
	