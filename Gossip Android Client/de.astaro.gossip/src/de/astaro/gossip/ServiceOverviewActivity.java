package de.astaro.gossip;

import java.util.Collections;
import java.util.List;

import de.astaro.gossip.background.GossipServiceWatcher;
import de.astaro.gossip.background.RefreshServiceListReceiver;
import de.astaro.gossip.data.*;
import android.os.Bundle;
import android.os.IBinder;
import android.app.ListActivity;
import android.app.NotificationManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.view.Gravity;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewGroup.LayoutParams;
import android.widget.TextView;

public class ServiceOverviewActivity extends ListActivity {

	private GossipServiceWatcher serviceWatcher;
	private ServiceDataSource serviceDatasource;
	private List<Service> serviceList;
	private ServiceAdapter serviceListAdapter;
	
	private RefreshServiceListReceiver slreceiver = new RefreshServiceListReceiver();
	
	/*
	 * Build up an activity which shows watched services' state.
	 * 
	 * @see android.app.Activity#onCreate(android.os.Bundle)
	 */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_service_overview);
        
        serviceDatasource = new ServiceDataSource(this);
        serviceDatasource.open();
        
        serviceList = serviceDatasource.getAllServices();
        Collections.sort(serviceList);
        serviceListAdapter = new ServiceAdapter(this, R.layout.row, serviceList);
        serviceListAdapter.setNotifyOnChange(true);
        setListAdapter(serviceListAdapter);
        setEmptyListView();
        
        doBindService();
    }
    
    /*
     * Close SQLite database helper.
     * 
     * @see android.app.ListActivity#onDestroy()
     */
    @Override
    public void onDestroy(){
    	super.onDestroy();
    	serviceDatasource.close();
    	unbindService(mConnection);
    }
    
    /*
     * Activate background service.
     * 
     * @see android.app.ListActivity#onDestroy()
     */
    @Override
    public void onStart(){
    	super.onStart();
    	((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).cancelAll();
    	
    	Intent i = new Intent();
		i.setAction(getString(R.string.action_string_start));
		sendBroadcast(i, null);		
    }
    
    /*
     * Make sure RefreshServiceListReceiver is registered while this activity is foreground.
     * Set higher priority to get receiver in first position to receive the ordered broadcast.
     * 
     * In addition refresh services.
     * 
     * @see android.app.Activity#onResume()
     */
    @Override
    public void onResume(){
    	super.onResume();
    	((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).cancelAll();
    	
    	IntentFilter ifilter = new IntentFilter(getString(R.string.action_string_notify));
    	ifilter.setPriority(1);
    	registerReceiver(slreceiver, ifilter);
    	
    	serviceList = serviceDatasource.getAllServices(); 
		Collections.sort(serviceList);
		serviceListAdapter.clear();
		serviceListAdapter.addAll(serviceList);
		serviceListAdapter.notifyDataSetChanged();
    }
    
    /*
     * Unregister RefreshServiceListReceiver to enable NotifyReceiver to get the broadcast and
     * raise a notification while application is in the background.
     * 
     * @see android.app.Activity#onPause()
     */
    @Override
    public void onPause(){
    	super.onPause();
    	unregisterReceiver(slreceiver);
    }
    
    /*
     * Show action bar menu.
     * 
     * @see android.app.Activity#onCreateOptionsMenu(android.view.Menu)
     */
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.activity_service_overview, menu);
        return true;
    }
    
    /*
     * Deal with clicks at the action bar. Open up host list view if host button is pressed,
     * start 'PreferenceActivity', if preference icon is pressed. 
     * 
     * @see android.app.Activity#onOptionsItemSelected(android.view.MenuItem)
     */
    @Override
    public boolean onOptionsItemSelected(MenuItem item){
    	Intent i;
    	switch(item.getItemId()){
    	case R.id.hosts:
    		i = new Intent(this, UpdateActivity.class);
    		startActivity(i);
    		break;
    	case R.id.settings:
    		i = new Intent(this, PreferencesActivity.class);
            startActivity(i);
    		break;
    	default:
    		break;
    	}
    	
    	return true;
    }
    
    /*
     * Get the latest from SQLite database.
     */
	public void refreshServices(){
		serviceList = serviceDatasource.getAllServices(); 
		Collections.sort(serviceList);
		serviceListAdapter.clear();
		serviceListAdapter.addAll(serviceList);
		serviceListAdapter.notifyDataSetChanged();
    }
    
	/*
     * Generate a text view to be shown if no host is known.
     */
    public void setEmptyListView(){
    	TextView emptyView = new TextView(getApplicationContext());
    	emptyView.setLayoutParams(new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));
    	emptyView.setText(R.string.no_items);
    	emptyView.setTextSize(20);
    	emptyView.setVisibility(View.GONE);
    	emptyView.setGravity(Gravity.CENTER_VERTICAL | Gravity.CENTER_HORIZONTAL);

    	((ViewGroup)getListView().getParent()).addView(emptyView);
    	getListView().setEmptyView(emptyView);
    }
    
    private ServiceConnection mConnection = new ServiceConnection(){
    	public void onServiceConnected(ComponentName className, IBinder binder){
    		serviceWatcher = ((GossipServiceWatcher.BSBinder) binder).getService();
    	}
    	
    	public void onServiceDisconnected(ComponentName className){
    		serviceWatcher = null;
    	}
    };
    
    void doBindService(){
    	bindService(new Intent(this, GossipServiceWatcher.class), mConnection, Context.BIND_AUTO_CREATE);
    }
}
