package de.astaro.gossip;

import de.astaro.gossip.background.RefreshServiceListReceiver;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.preference.PreferenceActivity;
import android.view.MenuItem;


 
public class PreferencesActivity extends PreferenceActivity {

	private RefreshServiceListReceiver slreceiver = new RefreshServiceListReceiver();
	
	/*
	 * Open the preference view which is stored in xml/preferences.xml.
	 * 
	 * @see android.preference.PreferenceActivity#onCreate(android.os.Bundle)
	 */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        addPreferencesFromResource(R.xml.preferences);
        getActionBar().setDisplayHomeAsUpEnabled(true);
        getActionBar().setHomeButtonEnabled(true);
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
     * Deal with clicks at the action bar. Finish activity if home button is pressed.
     * 
     * @see android.app.Activity#onOptionsItemSelected(android.view.MenuItem)
     */
    @Override
    public boolean onOptionsItemSelected(MenuItem item){
    	switch(item.getItemId()){
    	case android.R.id.home:
    		Intent i = new Intent();
    		i.setAction(getString(R.string.action_string_start));
    		sendBroadcast(i, null);
    		finish();
        	break;
    	default:
    		break;
    	}
    	
    	return true;
    }
}