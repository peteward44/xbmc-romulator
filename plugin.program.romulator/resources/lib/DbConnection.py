
import os
import sys
import sqlite3
import Config


class DbConnection(object):


	def __init__(self):
	
		dbPath = os.path.join( Config.config.resourcesPath, 'db' )
		self.dbConn = sqlite3.connect( os.path.join( dbPath, 'romulator.db' ) )
		self.dbConn.row_factory = sqlite3.Row
		
		
	def CloseDb(self):
	
		self.dbConn.close()
		
		
	def CreateTables( self ):
	
		dbCursor = self.dbConn.cursor()
		
		dbCursor.execute('create table if not exists roms ( id integer primary key autoincrement, fullPath text, emulatorName text,'
						' name text, romState integer, territory integer, isBestVersion boolean, isFavourite boolean, isScraped boolean, giantBombRomId integer,'
						' releaseDate text, description text )')
						
		dbCursor.execute( 'create table if not exists companies ( id integer primary key autoincrement, name text, giantBombId int, isScraped boolean,'
						' description text, foundedDate text )' )
		dbCursor.execute( 'create table if not exists genres ( id integer primary key autoincrement, name text, giantBombId int, isScraped boolean,'
						' description text )' )
						
		dbCursor.execute( 'create table if not exists platforms ( id integer primary key autoincrement, name text, giantBombId int, isScraped boolean,'
						' description text, companyId integer )' )

		# junction tables to map many-to-many relationship between roms and developers (a rom can have multiple developers, developers can develop multiple roms)
		dbCursor.execute( 'create table if not exists roms_developers_junction ( romId int not null, companyId int not null'
							', CONSTRAINT id PRIMARY KEY ( romId, companyId ) )' )
							
		dbCursor.execute( 'create table if not exists roms_publishers_junction ( romId int not null, companyId int not null'
							', CONSTRAINT id PRIMARY KEY ( romId, companyId ) )' )
							
		dbCursor.execute( 'create table if not exists roms_genres_junction ( romId int not null, genreId int not null'
							', CONSTRAINT id PRIMARY KEY ( romId, genreId ) )' )
		
		dbCursor.execute( 'create table if not exists similar_games ( romId int not null, otherRomGiantBombId int not null, name text'
							', CONSTRAINT id PRIMARY KEY ( romId, otherRomGiantBombId ) )' )
							
		self.dbConn.commit()
		dbCursor.close()

		
	def ClearAllRoms( self ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'delete from roms' )
		dbCursor.execute( 'delete from roms_developers_junction' )
		dbCursor.execute( 'delete from roms_publishers_junction' )
		dbCursor.execute( 'delete from roms_genres_junction' )
		dbCursor.execute( 'delete from similar_games' )
		self.dbConn.commit()
		dbCursor.close()
	
	
	def ClearRoms( self, emulatorName ):
	
		# TODO: remove from other tables too
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'delete from roms where emulatorName = ?', ( emulatorName, ) )
	#	dbCursor.execute( 'delete from roms_developers_junction' )
	#	dbCursor.execute( 'delete from roms_publishers_junction' )
	#	dbCursor.execute( 'delete from roms_genres_junction' )
		self.dbConn.commit()
		dbCursor.close()

		
	def InsertRomRecords( self, emulatorName, dbRowDictionaryList ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'delete from roms where emulatorName=?', ( emulatorName, ) )
		dbCursor.executemany( 'insert into roms ( fullPath, emulatorName, name, romState, territory, isBestVersion )'
				+ 'values ( :fullPath, :emulatorName, :romName, :romState, :territory, :isBestVersion )', dbRowDictionaryList )
		self.dbConn.commit()
		dbCursor.close()
		
		
	def AddEntrysToJunctionTable( self, romId, dataDictList, targetTable, targetJunctionTable, targetIdName ):
	
		if dataDictList != None:
		
			dbCursor = self.dbConn.cursor()
			for dataDict in dataDictList:

				# add developer entry if it does not exist
				dbCursor.execute( 'select * from ' + targetTable + ' where giantBombId = ?', ( dataDict[ 'giantBombId' ], ) )
				data = dbCursor.fetchone()
				if data == None:
					dbCursor.execute( 'insert into ' + targetTable + ' ( name, giantBombId ) values ( ?, ? )', ( dataDict[ 'name' ], dataDict[ 'giantBombId' ] ) )
					dbCursor.execute( 'select id from ' + targetTable + ' where giantBombId = ?', ( dataDict[ 'giantBombId' ], ) )
					data = dbCursor.fetchone()
				
				# then insert into junction table
				targetId = data[ "id" ]
				dbCursor.execute( 'insert into ' + targetJunctionTable + ' ( romId, ' + targetIdName + ' ) values ( ?, ? )', ( romId, targetId ) )
			
			self.dbConn.commit()
			dbCursor.close()
			
			
	def InsertRomScrapeRecords( self, romId, romScrapeDictionary ):
	
		romScrapeDictionary[ 'id' ] = romId
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'update roms set isScraped=1, releaseDate=:releaseDate, giantBombRomId=:giantBombRomId'
						+ ', description=:description'
						+ ' where id = :id', romScrapeDictionary )
		self.dbConn.commit()

		similarGamesList = romScrapeDictionary[ "similarGames" ]
		if similarGamesList != None and len( similarGamesList ) > 0:
			dbCursor.executemany( 'insert into similar_games ( romId, otherRomGiantBombId, name ) values ( ' + str( romId ) + ', :giantBombRomId, :name )', similarGamesList )

		self.AddEntrysToJunctionTable( romId, romScrapeDictionary[ "developers" ], 'companies', 'roms_developers_junction', 'companyId' )
		self.AddEntrysToJunctionTable( romId, romScrapeDictionary[ "publishers" ], 'companies', 'roms_publishers_junction', 'companyId' )
		self.AddEntrysToJunctionTable( romId, romScrapeDictionary[ "genres" ], 'genres', 'roms_genres_junction', 'genreId' )

		self.dbConn.commit()
		
		dbCursor.close()
		
		
	def InsertGenreScrapeRecord( self, genreId, scrapeDictionary ):
	
		scrapeDictionary[ 'id' ] = genreId
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'update genres set isScraped=1, description=:description'
						+ ' where id = :id', scrapeDictionary )
		self.dbConn.commit()
		dbCursor.close()
		
		
	def InsertCompanyScrapeRecord( self, companyId, companyScrapeDictionary ):

		companyScrapeDictionary[ 'id' ] = companyId
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'update companies set isScraped=1, description=:description'
						+ ', foundedDate=:foundedDate'
						+ ' where id = :id', companyScrapeDictionary )
		self.dbConn.commit()
		dbCursor.close()
		
		
	def SetRomFavourite( self, romId, isSelected ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'update roms set isFavourite = ? where id = ?', ( isSelected, romId, ) )
		self.dbConn.commit()
		dbCursor.close()
		
		
	def GetRomById( self, romId ):

		#print "Getting Rom ID " + str( romId )
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from roms where id = ?', ( romId, ) )
		data = dbCursor.fetchone()
		dbCursor.close()
		return data
		
		
	def GetRomSimilarGames( self, romId, limitCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from similar_games where romId = ? limit ?', ( romId, limitCount, ) )
		data = dbCursor.fetchall()
		dbCursor.close()
		return data
		
		
	def GetRomByGiantBombId( self, giantBombRomId ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from roms where giantBombRomId = ?', ( giantBombRomId, ) )
		data = dbCursor.fetchone()
		dbCursor.close()
		return data
		
		
	def GetDevelopersByRomId( self, romId ):
		
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select id, name from companies d INNER JOIN roms_developers_junction j ON d.id = j.companyId where j.romId = ?', ( romId, ) )
		data = dbCursor.fetchall()
		dbCursor.close()
		return data
		
		
	def GetPublishersByRomId( self, romId ):
		
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select id, name from companies p INNER JOIN roms_publishers_junction j ON p.id = j.companyId where j.romId = ?', ( romId, ) )
		data = dbCursor.fetchall()
		dbCursor.close()
		return data
		
		
	def GetGenresByRomId( self, romId ):
		
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select id, name from genres g INNER JOIN roms_genres_junction j ON g.id = j.genreId where j.romId = ?', ( romId, ) )
		data = dbCursor.fetchall()
		dbCursor.close()
		return data
		
	
	def GetCompanyByGiantBombId( self, giantBombId ):
		
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from companies where giantBombId = ?', ( giantBombId, ) )
		data = dbCursor.fetchone()
		dbCursor.close()
		return data
		
		
	def GetRomsByGenre( self, genreId, startIndex, itemCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from roms r INNER JOIN ( select romId from roms_genres_junction where genreId = ? ) j ON r.id = j.romId limit ? offset ?', ( genreId, itemCount, startIndex ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(distinct romId) from roms_genres_junction where genreId = ?', ( genreId, ) )
		(number_of_rows,) = dbCursor.fetchone()
		dbCursor.close()
		
		print "DATA COUNT: " + str( len( data ) ) + " ROW COUNT: " + str( number_of_rows ) + " INDEX: " + str( startIndex ) + " LIMIT: " + str( itemCount )
		
		return ( data, number_of_rows )
		
		
	def GetGenreByGiantBombId( self, giantBombId ):
		
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from genres where giantBombId = ?', ( giantBombId, ) )
		data = dbCursor.fetchone()
		dbCursor.close()
		return data
		
		
	def GetRomsByDeveloperId( self, companyId, startItemIndex, limitCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from roms r INNER JOIN roms_developers_junction j ON r.id = j.romId where j.companyId = ? limit ? offset ?', ( companyId, limitCount, startItemIndex ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(distinct romId) from roms_developers_junction where companyId = ?', ( companyId, ) )
		(number_of_rows,) = dbCursor.fetchone()
		dbCursor.close()
		return ( data, number_of_rows )
		
		
	def GetRomsByPublisherId( self, companyId, startItemIndex, limitCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from roms r INNER JOIN roms_publishers_junction j ON r.id = j.romId where j.companyId = ? limit ? offset ?', ( companyId, limitCount, startItemIndex ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(distinct romId) from roms_publishers_junction where companyId = ?', ( companyId, ) )
		(number_of_rows,) = dbCursor.fetchone()
		dbCursor.close()
		return ( data, number_of_rows )
		
		
	def SelectEmulatorRoms( self, emulatorName, specificRomState, getBestVersion, getFavourites, orderBy, isDescending, startIndex, count ):
		
		dbCursor = self.dbConn.cursor()
		replacementDictionary = { "romState": specificRomState, "emulatorName": emulatorName, "orderBy": orderBy, "limit": count, "offset": startIndex }
		
		descendingString = "DESC" if isDescending > 0 else "ASC"
		whereStatement = ''
		if emulatorName != '*':
			whereStatement += ' emulatorName=:emulatorName'
		if specificRomState > 0:
			if len( whereStatement ) > 0:
				whereStatement += ' and'
			whereStatement += ' romState & :romState == :romState'
		if getBestVersion > 0:
			if len( whereStatement ) > 0:
				whereStatement += ' and'
			whereStatement += ' isBestVersion = 1'
		if getFavourites > 0:
			if len( whereStatement ) > 0:
				whereStatement += ' and'
			whereStatement += ' isFavourite = 1'

		if len( whereStatement ) > 0:
			whereStatement = 'where ' + whereStatement
		
		finalString = ''
		if count <= 0:
			finalString = 'select * from roms ' + whereStatement + ' order by :orderBy ' + descendingString
		else:
			finalString = 'select * from roms ' + whereStatement + ' order by :orderBy ' + descendingString + ' limit :limit offset :offset'
		dbCursor.execute( finalString, replacementDictionary );
		
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(id) from roms ' + whereStatement, replacementDictionary )
		(number_of_rows,) = dbCursor.fetchone()
		
		dbCursor.close()
		return ( data, number_of_rows )

	
	def GetGenreList( self, startItemIndex, itemCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from genres limit ? offset ?', ( itemCount, startItemIndex, ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(id) from genres' )
		(number_of_rows,) = dbCursor.fetchone()
		
		dbCursor.close()
		
	#	print "ITEM COUNT: " + str( len( data ) ) + " ROW COUNT: " + str( number_of_rows )
		
		return ( data, number_of_rows )
		
		
	def GetDeveloperList( self, startItemIndex, limitCount ):
	
		dbCursor = self.dbConn.cursor()
		# method using GROUP BY clause instead of SELECT DISTINCT
	#	dbCursor.execute( 'select * from companies c INNER JOIN roms_developers_junction j ON c.id = j.companyId group by c.id order by c.name limit ? offset ?', ( limitCount, startItemIndex ) )
		dbCursor.execute( 'select * from companies c INNER JOIN ( select distinct companyId from roms_developers_junction ) j ON c.id = j.companyId order by c.name limit ? offset ?', ( limitCount, startItemIndex ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(distinct companyId) from roms_developers_junction' )
		(number_of_rows,) = dbCursor.fetchone()
		dbCursor.close()
		
#		print "TOTAL ROWS: " + str( len( data ) ) + " DETECTED ROWS: " + str( number_of_rows )
		
		return ( data, number_of_rows )
		
		
	def GetPublisherList( self, startItemIndex, limitCount ):
	
		dbCursor = self.dbConn.cursor()
		dbCursor.execute( 'select * from companies c INNER JOIN ( select distinct companyId from roms_publishers_junction ) j ON c.id = j.companyId order by c.name limit ? offset ?', ( limitCount, startItemIndex ) )
		data = dbCursor.fetchall()
		
		dbCursor.execute( 'select COUNT(distinct companyId) from roms_publishers_junction' )
		(number_of_rows,) = dbCursor.fetchone()
		dbCursor.close()
		return ( data, number_of_rows )
		
		