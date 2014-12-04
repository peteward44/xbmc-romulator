import xbmcplugin, string, sys, os, traceback, xbmcaddon, logging

__plugin__ =  'RomLauncher'
__author__ = 'PW <peteward44@gmail.com>'
__date__ = '13-05-2013'
__version__ = '1.0.0'

ADDON = xbmcaddon.Addon()
REMOTE_DBG = False

sys.path.append( os.path.join( os.path.join( ADDON.getAddonInfo('path'), "resources" ), "lib" ) )

# append pydev remote debugger
if REMOTE_DBG:
	# Make pydev debugger works for auto reload.
	# Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
	try:
		import pysrc.pydevd as pydevd
		# stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
		pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
	except ImportError:
		sys.stderr.write("Error: You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
		sys.exit(1)

import EntryPoint

try:
	EntryPoint.StartApp( ADDON )
except Exception as e:
	logging.exception(e)

