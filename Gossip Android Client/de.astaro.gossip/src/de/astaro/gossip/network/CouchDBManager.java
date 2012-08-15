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

import de.astaro.gossip.data.Host;

import android.util.Log;


public class CouchDBManager {
	
	private String host;
	private String user;
	private String passwd;
	private int htmlTimeout;
	private boolean useAuthentification = false;
	
	/*
	 * Initialize manager with target host, user settings and a timeout for the 
	 * HTML connection.
	 */
	public CouchDBManager(String host, String user, String passwd, int htmlTimeout){
		this.host = host;
		this.htmlTimeout = htmlTimeout;
		if(!user.equals("") && !passwd.equals("")){
			this.user = user;
			this.passwd = passwd;
			this.useAuthentification = true;
		}
	}
	
	/*
	 * Read all known peer addresses from the remote couchDB database.
	 * All information must be stored in the 'gossip_crackertable' database.
	 */
	public List<Host> readHostNetwork(){
		List<Host> hosts = new ArrayList<Host>();
		String network = doRead("gossip_crackertable", "_all_docs");
		
		JSONArray list;
		JSONObject docName;
		try{
			list = (JSONArray)new JSONObject(network).get("rows");
			
			for(int i = 0; i < list.length(); i++){
				docName = (JSONObject)list.get(i);
				
				String single_doc = doRead("gossip_crackertable", docName.getString("id"));
				JSONArray addresses = new JSONObject(single_doc).getJSONArray("host");
				Host newHost = new Host();
				newHost.setAddress(addresses.getString(0));
				
				if(docName.getString("id").equals("self")){
					newHost.setName(host);
				}else{
					newHost.setName(docName.getString("id"));
				}
				hosts.add(newHost);
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
			Log.w("CouchDB", "Unable to parse service list of " + host + ".");
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
    		URL url;
    		if(useAuthentification){
    			url = new URL(String.format("http://%s:%s@%s:5984/%s/%s", user, passwd,
    												host, database, document));
    		}else{
    			url = new URL(String.format("http://%s:5984/%s/%s", host, database, document));
    		}
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
