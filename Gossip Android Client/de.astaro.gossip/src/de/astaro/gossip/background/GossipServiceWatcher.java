package de.astaro.gossip.background;


import java.util.HashMap;
import java.util.List;
import java.util.Map.Entry;

import de.astaro.gossip.R;
import de.astaro.gossip.data.Host;
import de.astaro.gossip.data.HostDataSource;
import de.astaro.gossip.data.ServiceDataSource;
import de.astaro.gossip.network.CouchDBManager;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Binder;
import android.os.IBinder;
import android.os.StrictMode;
import android.preference.PreferenceManager;
import android.util.Log;

public class GossipServiceWatcher extends Service {
	private final IBinder mBinder = new BSBinder();
	
	/*
	 * Read service results from all known hosts, gather the information and 
	 * update the service list.
	 * 
	 * @see android.app.Service#onStartCommand(android.content.Intent, int, int)
	 */
	@Override
	public int onStartCommand(Intent intent, int flags, int startId){        
		StrictMode.ThreadPolicy policy = new StrictMode.
	        		ThreadPolicy.Builder().permitAll().build();
	    StrictMode.setThreadPolicy(policy); 
		
		SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
		HostDataSource hds = new HostDataSource(this);
		ServiceDataSource sds = new ServiceDataSource(this);
		hds.open();
		sds.open();
		
		List<Host> hostList = hds.getAllHosts();
		List<de.astaro.gossip.data.Service> oldServiceList = sds.getAllServices();
		HashMap<String, Integer> serviceMap = new HashMap<String, Integer>();
		
		// Collect services from every known host and gather them in one HashMap.
		for(Host h : hostList){
			CouchDBManager couchdb = new CouchDBManager(h.getAddress(), 
										preferences.getString("username", "n/a"), 
										preferences.getString("password", "n/a"), 
										Integer.parseInt(preferences.getString("timeout", "1"))*1000);
			HashMap<String, Integer> temp = couchdb.readServiceResults();
			
			for(Entry<String, Integer> e : temp.entrySet()){
				if(serviceMap.containsKey(e.getKey())){
					serviceMap.put(e.getKey(), serviceMap.get(e.getKey()) + e.getValue());
				}else{
					serviceMap.put(e.getKey(), e.getValue());
				}
			}
		}
		
		// Delete no longer present services
		for(de.astaro.gossip.data.Service s : oldServiceList){
			if(!serviceMap.containsKey(s.getName())){
				sds.deleteService(s);
			}
		}
		
		// Figure out faulty services (more than 50% of the watchers report an error)
		String errorMsg = "";
		for(Entry<String, Integer> e : serviceMap.entrySet()){
			int amountOfErrors = (int)e.getValue()/10000;
			int amountOfWatchers = e.getValue() % 10000;
			
			if(amountOfErrors/amountOfWatchers <= 0.5){
				continue;
			}
			
			errorMsg += e.getKey() + " | ";
		}
		
		sds.createServices(serviceMap);
		
		// Notify either RefreshServiceListReceiver or NotifyReceiver, depending if activity is in focus
		Intent i = new Intent();
		//i.setAction("de.astaro.gossip.NOTIFY");
		i.setAction(getString(R.string.action_string_notify));
		i.putExtra("msg", errorMsg);
		sendOrderedBroadcast(i, null);		
	    
		sds.close();
		hds.close();
		
		return Service.START_NOT_STICKY;
	}
	
	@Override
	public IBinder onBind(Intent arg0){
		return mBinder;
	}
	
	public class BSBinder extends Binder{
		public GossipServiceWatcher getService(){
			return GossipServiceWatcher.this;
		}
	}
	
}
