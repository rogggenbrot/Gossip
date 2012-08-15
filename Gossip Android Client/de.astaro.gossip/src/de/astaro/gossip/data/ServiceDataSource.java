package de.astaro.gossip.data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map.Entry;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.SQLException;
import android.database.sqlite.SQLiteDatabase;

public class ServiceDataSource {
	private SQLiteDatabase database;
	private GossipSQLiteHelper dbHelper;
	private String[] columns = { GossipSQLiteHelper.SERVICE_COLUMN_ID, 
									GossipSQLiteHelper.SERVICE_COLUMN_NAME,
									GossipSQLiteHelper.SERVICE_COLUMN_WATCHERS,
									GossipSQLiteHelper.SERVICE_COLUMN_FAILURES};
	
	/*
	 * Initialize a new database helper.
	 */
	public ServiceDataSource(Context context){
		dbHelper = new GossipSQLiteHelper(context);
	}
	
	/*
	 * Open a connection to the SQLite database.
	 */
	public void open() throws SQLException{
		database = dbHelper.getWritableDatabase();
	}
	
	/*
	 * Close current database connection.
	 */
	public void close(){
		dbHelper.close();
	}
	
	/*
	 * Create service object out of first line of cursor.
	 */
	private Service cursorToService(Cursor cursor) {
		Service service = new Service();
		service.setId(cursor.getLong(0));
		service.setName(cursor.getString(1));
		service.setAmountOfWatchers(cursor.getInt(2));
		service.setAmountOfErrors(cursor.getInt(3));
		return service;
	}
	
	/*
	 * Check if service already in database. If this is the case, simply update
	 * it in the database, otherwise create a new service in the database.
	 * In either way return a instance of that host.
	 */
	public Service createService(String name, int watchers, int failures){
		ContentValues values = new ContentValues();
		values.put(GossipSQLiteHelper.SERVICE_COLUMN_NAME, name);
		values.put(GossipSQLiteHelper.SERVICE_COLUMN_WATCHERS, watchers);
		values.put(GossipSQLiteHelper.SERVICE_COLUMN_FAILURES, failures);
		
		Cursor cursor = database.query(GossipSQLiteHelper.TABLE_SERVICE, columns, 
				GossipSQLiteHelper.SERVICE_COLUMN_NAME + " = '" + name + "'", 
				null, null, null, null);
		
		if(cursor.moveToFirst() != false){
			database.update(GossipSQLiteHelper.TABLE_SERVICE, values, 
					GossipSQLiteHelper.SERVICE_COLUMN_NAME + " = ?", new String[]{name});
		}else{
			database.insert(GossipSQLiteHelper.TABLE_SERVICE, null, values);
		}
		cursor = database.query(GossipSQLiteHelper.TABLE_SERVICE, columns, 
										GossipSQLiteHelper.SERVICE_COLUMN_NAME + " = '" + name + "'", 
										null, null, null, null);
		cursor.moveToFirst();
		
		Service newService = cursorToService(cursor);
		cursor.close();
		return newService;
	}
	
	/*
	 * Create a list of services by creating each service individual and returning 
	 * a list of instances.
	 * 
	 * The amount of errors is represented by all digits starting at the 5th position,
	 * the number of watchers is related to the lower 4 digits.
	 */
	public List<Service> createServices(HashMap<String, Integer> services){
		List<Service> servList = new ArrayList<Service>();
		for(Entry<String, Integer> e : services.entrySet()){
			Service s = createService(e.getKey(), e.getValue() % 10000, (int)(e.getValue()/10000));
			if(s != null){
				servList.add(s);
			}
		}
		
		return servList;
	}
	
	/*
	 * Delete a service in database identified by its database id.
	 */
	public void deleteService(Service service){
		long id = service.getId();
		database.delete(GossipSQLiteHelper.TABLE_SERVICE, 
							GossipSQLiteHelper.SERVICE_COLUMN_ID + " = " + id, null);
	}
	
	/*
	 * Read currently known services and return them as list of service instances.
	 */
	public List<Service> getAllServices(){
		List<Service> services = new ArrayList<Service>();
		
		Cursor cursor = database.query(GossipSQLiteHelper.TABLE_SERVICE, columns, null, null,
										null, null, null);
		cursor.moveToFirst();
		while(!cursor.isAfterLast()){
			Service service = cursorToService(cursor);
			services.add(service);
			cursor.moveToNext();
		}
		
		cursor.close();
		return services;
	}
}
