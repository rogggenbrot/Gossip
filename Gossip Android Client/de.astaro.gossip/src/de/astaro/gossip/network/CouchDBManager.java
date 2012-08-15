package de.astaro.gossip.network;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.util.Log;


public class CouchDBManager {
	
	private String host;
	private String user;
	private String passwd;
	private int htmlTimeout;
	
	/*
	 * Initialize manager with target host, user settings and a timeout for the 
	 * HTML connection.
	 */
	public CouchDBManager(String host, String user, String passwd, int htmlTimeout){
		this.host = host;
		this.user = user;
		this.passwd = passwd;
		this.htmlTimeout = htmlTimeout;
	}
	
	/*
	 * Read all known peer addresses from the remote couchDB database.
	 * All information must be stored in the 'gossip_crackertable' database.
	 */
	public List<String> readHostNetwork(){
		List<String> hosts = new ArrayList<String>();
		String network = doRead("gossip_crackertable", "_all_docs");
		
		JSONArray list;
		JSONObject single;
		try{
			list = (JSONArray)new JSONObject(network).get("rows");
			
			for(int i = 0; i < list.length(); i++){
				single = (JSONObject)list.get(i);
				
				if(single.getString("id").equals("self")){
					hosts.add(host);
				}else{
					hosts.add(single.getString("id"));
				}
			}
		}catch(JSONException e){
			Log.w("CouchDB", "Unable to parse host list.");
		}
		
		return hosts;
	}
	
	/*
	 * Read all stored results of the service surveillance of the given host.
	 */
	public HashMap<String, Integer> readServiceResults(){
		HashMap<String, Integer> services = new HashMap<String, Integer>();
		
		String results = doRead("gossip_watchresults", "results");
		
		JSONArray list, single;
		try{
			list  = (JSONArray) (new JSONObject(results)).get("results");
			
			for(int i = 0; i < list.length(); i++){
				single = (JSONArray)list.get(i);
				
				
				if(single.getInt(2) == 0){
					services.put(single.getString(0), 10001);
				}else{
					services.put(single.getString(0), 1);
				}
			}
		}catch(JSONException e){
			Log.w("CouchDB", "Unable to parse service list.");
		}
		
		return services;
	}
	
	/*
	 * Read the content of the given document in the given database.
	 */
	private String doRead(String database, String document){
    	BufferedReader reader = null;
    	String content = "";
    	try{
    		
    		URL url = new URL(String.format("http://%s:%s@%s:5984/%s/%s", user, passwd,
    												host, database, document));
    		
    		HttpURLConnection con = (HttpURLConnection) url.openConnection();
    		con.setConnectTimeout(htmlTimeout);
    	
    		reader = new BufferedReader(new InputStreamReader(con.getInputStream()));
    		String line = "";
    		
    		while((line = reader.readLine())!= null){
    			content += line;
    		}
    	}catch(IOException e){
    		Log.w("CouchDB", "Unable to connect to database on " + host + ".");
    	}finally{
    		if(reader != null){
    			try{
    				reader.close();
    			}catch(IOException e){
    				e.printStackTrace();
    			}
    		}
    	}
    	
    	return content;
    }
}
