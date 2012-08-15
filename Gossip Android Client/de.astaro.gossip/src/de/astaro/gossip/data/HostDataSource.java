package de.astaro.gossip.data;

import java.util.ArrayList;
import java.util.List;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.SQLException;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;

public class HostDataSource {
	private SQLiteDatabase database;
	private GossipSQLiteHelper dbHelper;
	private String[] columns = { GossipSQLiteHelper.HOST_COLUMN_ID, 
									GossipSQLiteHelper.HOST_COLUMN_NAME,
									GossipSQLiteHelper.HOST_COLUMN_ADDRESS};
	
	/*
	 * Initializes a new SQLite database helper.
	 */
	public HostDataSource(Context context){
		dbHelper = new GossipSQLiteHelper(context);
	}
	
	/*
	 * Open connection to a SQLite database.
	 */
	public void open() throws SQLException{
		database = dbHelper.getWritableDatabase();
	}
	
	/*
	 * Close connection to database.
	 */
	public void close(){
		dbHelper.close();
	}
	
	/*
	 * Create host object out of first line of cursor.
	 */
	private Host cursorToHost(Cursor cursor) {
		Host host = new Host();
		host.setId(cursor.getLong(0));
		host.setName(cursor.getString(1));
		host.setAddress(cursor.getString(2));
		return host;
	}
	
	/*
	 * Check if host already in database. If this is not the case, create it and
	 * return a instance of that host.
	 */
	public Host createHost(String name, String address){
		ContentValues values = new ContentValues();
		values.put(GossipSQLiteHelper.HOST_COLUMN_NAME, name);
		values.put(GossipSQLiteHelper.HOST_COLUMN_ADDRESS, address);
		
		Cursor cursor = database.query(GossipSQLiteHelper.TABLE_HOST, columns, 
				GossipSQLiteHelper.HOST_COLUMN_NAME + " = '" + name + "'", 
				null, null, null, null);
		
		if(cursor.moveToFirst() != false){
			return null;
		}
		
		long insertId = database.insert(GossipSQLiteHelper.TABLE_HOST, null, values);
		cursor = database.query(GossipSQLiteHelper.TABLE_HOST, columns, 
										GossipSQLiteHelper.HOST_COLUMN_ID + " = " + insertId, 
										null, null, null, null);
		cursor.moveToFirst();
		
		Host newHost = cursorToHost(cursor);
		cursor.close();
		return newHost;
	}
	
	/*
	 * Create a list of hosts by creating each host individual and returning 
	 * a list of instances. Only newly created hosts will be returned.
	 */
	public List<Host> createHosts(List<Host> addresses){
		List<Host> hosts = new ArrayList<Host>();
		for(Host h : addresses){
			Host a = createHost(h.getName(), h.getAddress());
			if(a != null){
				hosts.add(a);
			}
		}
		
		return hosts;
	}
	
	/*
	 * Remove given instance from database. Host is identified by id.
	 */
	public void deleteHost(Host host){
		long id = host.getId();
		database.delete(GossipSQLiteHelper.TABLE_HOST, 
							GossipSQLiteHelper.HOST_COLUMN_ID + " = " + id, null);
	}
	
	/*
	 * Read currently known hosts and return them as list of host instances.
	 */
	public List<Host> getAllHosts(){
		List<Host> hosts = new ArrayList<Host>();
		
		Cursor cursor = database.query(GossipSQLiteHelper.TABLE_HOST, columns, null, null,
										null, null, null);
		cursor.moveToFirst();
		while(!cursor.isAfterLast()){
			Host host = cursorToHost(cursor);
			hosts.add(host);
			cursor.moveToNext();
		}
		
		cursor.close();
		return hosts;
	}
}
