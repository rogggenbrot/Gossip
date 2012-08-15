package de.astaro.gossip.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class GossipSQLiteHelper extends SQLiteOpenHelper{
	
	private static final String DATABASE_NAME = "gossip.db";
	private static final int DATABASE_VERSION = 4;
	
	public static final String TABLE_HOST = "host";
	public static final String HOST_COLUMN_ID = "_id";
	public static final String HOST_COLUMN_NAME = "name";
	public static final String HOST_COLUMN_ADDRESS = "address";
	
	public static final String TABLE_SERVICE = "service";
	public static final String SERVICE_COLUMN_ID = "_id";
	public static final String SERVICE_COLUMN_NAME = "name";
	public static final String SERVICE_COLUMN_WATCHERS = "watchers";
	public static final String SERVICE_COLUMN_FAILURES = "failures";
			
	private static final String DATABASE_CREATE_HOST = "create table "
			+ TABLE_HOST + "(" + HOST_COLUMN_ID + " integer primary key, "
			+ HOST_COLUMN_NAME + " text not null,"
			+ HOST_COLUMN_ADDRESS + " text not null);";
	
	private static final String DATABASE_CREATE_SERVICE = "create table "
			+ TABLE_SERVICE + "(" + SERVICE_COLUMN_ID + " integer primary key, "
			+ SERVICE_COLUMN_NAME + " text unique not null, "
			+ SERVICE_COLUMN_WATCHERS + " integer not null, "
			+ SERVICE_COLUMN_FAILURES + " integer not null);";
	
	public GossipSQLiteHelper(Context context){
		super(context, DATABASE_NAME, null, DATABASE_VERSION);
	}
	
	/*
	 * Create both host and service table when database is initially created.
	 * 
	 * @see android.database.sqlite.SQLiteOpenHelper#onCreate(android.database.sqlite.SQLiteDatabase)
	 */
	@Override
	public void onCreate(SQLiteDatabase database){
		database.execSQL(DATABASE_CREATE_HOST);
		database.execSQL(DATABASE_CREATE_SERVICE);
	}
	
	/*
	 * Drop old tables and recreate them when database is upgraded (old data will be lost).
	 * 
	 * @see android.database.sqlite.SQLiteOpenHelper#onUpgrade(android.database.sqlite.SQLiteDatabase, int, int)
	 */
	@Override
	public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion){
		db.execSQL("DROP TABLE IF EXISTS " + TABLE_HOST);
		db.execSQL("DROP TABLE IF EXISTS " + TABLE_SERVICE);
		onCreate(db);
	}
}
