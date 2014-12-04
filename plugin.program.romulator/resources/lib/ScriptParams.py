

class ScriptParams(object):

	mParams = {}
	
	def __init__(self, argumentString):
		if len( argumentString )>=2:
			cleanedparams = argumentString.replace('?','')
			if ( argumentString[ len( argumentString ) - 1 ] == '/' ):
				argumentString = argumentString[ 0 : len( argumentString ) - 2 ]
			pairsofparams = cleanedparams.split( '&' )
			for i in range( len( pairsofparams ) ):
				splitparams = {}
				splitparams = pairsofparams[ i ].split( '=' )
				if ( len( splitparams ) ) == 2:
					self.mParams[ splitparams[ 0 ] ] = splitparams[ 1 ]

	def GetParamDefault( self, keyName, defValue ):
		try:
			return self.mParams[ keyName ]
		except:
			return defValue
			