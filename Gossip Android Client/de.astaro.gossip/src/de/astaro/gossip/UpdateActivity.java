package de.astaro.gossip;

import java.util.List;

import de.astaro.gossip.background.RefreshServiceListReceiver;
import de.astaro.gossip.data.*;
import de.astaro.gossip.network.*;
import android.os.Bundle;
import android.os.StrictMode;
import android.preference.PreferenceManager;
import android.app.ListActivity;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.view.ContextMenu;
import android.view.ContextMenu.ContextMenuInfo;
import android.view.ViewGroup.LayoutParams;
import android.view.Gravity;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.TextView;

public class UpdateActivity extends ListActivity {

	SharedPreferences preferences;
	private HostDataSource hostDataSource;
	private CouchDBManager couchDB;
	private List<Host> allHosts;
	private ArrayAdapter<Host> hostListAdapter;
	private RefreshServiceListReceiver slreceiver = new RefreshServiceListReceiver();
	
	/*
	 * Build up an activity which shows current known hosts.
	 * 
	 * @see android.app.Activity#onCreate(android.os.Bundle)
	 */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_update);
        
        StrictMode.ThreadPolicy policy = new StrictMode.
        		ThreadPolicy.Builder().permitAll().build();
        StrictMode.setThreadPolicy(policy); 
        
        hostDataSource = new HostDataSource(this);
        hostDataSource.open();
        allHosts = hostDataSource.getAllHosts();
        hostListAdapter = new ArrayAdapter<Host>(this,
        								android.R.layout.simple_list_item_1, allHosts);
        setListAdapter(hostListAdapter);
        setEmptyListView();
        
        registerForContextMenu((ListView)findViewById(android.R.id.list));
        
        // Preferences are maintained via PreferencesActivity
        preferences = PreferenceManager.getDefaultSharedPreferences(this);
        getActionBar().setDisplayHomeAsUpEnabled(true);
        getActionBar().setHomeButtonEnabled(true);
    }
    
    /*
     * Close SQLite database helper.
     * 
     * @see android.app.ListActivity#onDestroy()
     */
    @Override
    public void onDestroy(){
    	super.onDestroy();
    	hostDataSource.close();
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
     * @see android.app.Activity#onResume()
     */
    @Override
    public void onResume(){
    	super.onResume();
    	
    	IntentFilter ifilter = new IntentFilter(getString(R.string.action_string_notify));
    	ifilter.setPriority(1);
    	registerReceiver(slreceiver, ifilter);
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
        getMenuInflater().inflate(R.menu.activity_update, menu);
        return true;
    }
    
    /*
     * Deal with clicks at the action bar. Finish activity if home button is pressed,
     * start 'PreferenceActivity', if preference icon is pressed.
     * 
     * @see android.app.Activity#onOptionsItemSelected(android.view.MenuItem)
     */
    @Override
    public boolean onOptionsItemSelected(MenuItem item){
    	switch(item.getItemId()){
    	case android.R.id.home:
    		finish();
        	break;
    	case R.id.settings:
    		Intent i = new Intent(UpdateActivity.this, PreferencesActivity.class);
            startActivity(i);
    		break;
    	default:
    		break;
    	}
    	
    	return true;
    }
    
    /*
     * Create context menu for host list. Menu items are stored in strings.xml.
     * 
     * @see android.app.Activity#onCreateContextMenu(android.view.ContextMenu, android.view.View, android.view.ContextMenu.ContextMenuInfo)
     */
    @Override
    public void onCreateContextMenu(ContextMenu menu, View v,
        ContextMenuInfo menuInfo) {
	    if (v.getId()==android.R.id.list) {
	    	AdapterView.AdapterContextMenuInfo info = (AdapterView.AdapterContextMenuInfo)menuInfo;
		    menu.setHeaderTitle(allHosts.get(info.position).getName());
		    String[] menuItems = getResources().getStringArray(R.array.item_menu);
		      
		    for (int i = 0; i<menuItems.length; i++) {
		    	menu.add(Menu.NONE, i, i, menuItems[i]);
		    }
	    }
    }
    
    /*
     * Deal with clicks on menu items. Menu items are stored in strings.xml.
     * 
     * @see android.app.Activity#onContextItemSelected(android.view.MenuItem)
     */
    @Override
    public boolean onContextItemSelected(MenuItem item) {
	    AdapterView.AdapterContextMenuInfo info = (AdapterView.AdapterContextMenuInfo)item.getMenuInfo();
	    int menuItemIndex = item.getItemId();
	    String[] menuItems = getResources().getStringArray(R.array.item_menu);
	    String menuItemName = menuItems[menuItemIndex];
	    Host selected = allHosts.get(info.position);
	
	    if(menuItemName.equals("Delete")){
	    	allHosts.remove(info.position);
	    	hostDataSource.deleteHost(selected);
	    	hostListAdapter.notifyDataSetChanged();
	    }
	     
	    return true;
	}
    
    /*
     * Reread and store host list from remote couchDB server using up-to-date user
     * settings for seed host, username and password. 
     * 
     * Will not delete any old peers, only add new.
     */
    public void refreshHostList(View view){
    	String hostname = preferences.getString("hostname", "n/a");
    	String username = preferences.getString("username", "n/a");
    	String password = preferences.getString("password", "n/a");
    	int timeout = Integer.parseInt(preferences.getString("timeout", "1")) * 1000;
    	couchDB = new CouchDBManager(hostname, username, password, timeout);
    	List<Host> network = couchDB.readHostNetwork();
    	
    	allHosts.addAll(hostDataSource.createHosts(network)); 
    	hostListAdapter.notifyDataSetChanged();
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

}
