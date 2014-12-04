import xbmc, xbmcgui
import Config

#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h


def FormatMenuString( title, option ):
	if len( option ) > 0:
		return title + " [" + option + "]"
	else:
		return title


def DoAddDialog():
	platform = ""
	roms_dir = ""
	roms_filter = ""
	exe_file = ""
	exe_args = "%ROM%"
	
	dialog = xbmcgui.Dialog()
	indialog = 1
	while indialog > 0:
		selection = dialog.select( "Add Emulator",
			[ FormatMenuString( "Platform", platform ), FormatMenuString( "Roms dir", roms_dir ), FormatMenuString( "Roms filter", roms_filter ), FormatMenuString( "Exe file", exe_file ),
				FormatMenuString( "Exe arguments", exe_args ), "Add", "Cancel" ])
		
		if selection == 0:
			keyboard = xbmc.Keyboard("", "Enter Platform")
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				platform = keyboard.getText()
		elif selection == 1:
			roms_dir = dialog.browse(0,"Locate emulator roms","files","", False, False, "")
		elif selection == 2:
			keyboard = xbmc.Keyboard("*.zip|*.7z|*.bin", "Rom filter" )
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				roms_filter = keyboard.getText()
		elif selection == 3:
		#0 = showandgetdirectory
		#1 = showandgetfile
		#2 = showandgetimage
			exe_file = dialog.browse(1,"Locate emulator executable","files","", False, False, "")
		elif selection == 4:
			keyboard = xbmc.Keyboard( "%ROM%", "Enter exe arguments")
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				exe_args = keyboard.getText()
		elif selection == 5:
			validPlatform = len( platform ) > 0
			validExe = len( exe_file ) > 0
			validRomsDir = len( roms_dir ) > 0
			isValid = validPlatform and validExe and validRomsDir
			if isValid:
				Config.config.AddEmulator( platform, roms_dir, roms_filter, exe_file, exe_args )
				indialog = 0
			else:
				invalidFields = ""
				if not validPlatform:
					invalidFields = invalidFields + "Platform, "
				if not validExe:
					invalidFields = invalidFields + "Exe Path, "
				if not validRomsDir:
					invalidFields = invalidFields + "Roms Dir, "
				if len( invalidFields ) > 0:
					invalidFields = invalidFields[: len( invalidFields )-2 ]
				dialog.ok( "Error", "The following fields have invalid values", invalidFields )
		elif selection == 6 or selection < 0:
			indialog = 0
			
	del dialog
	