package de.astaro.gossip.background;

import de.astaro.gossip.ServiceOverviewActivity;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class RefreshServiceListReceiver extends BroadcastReceiver{
	
	/*
	 * Called to update ServiceOverviewActivity. Aborts ordered broadcast to prevent NotifyReceiver
	 * from raising a notification (activity is already in focus).
	 * 
	 * @see android.content.BroadcastReceiver#onReceive(android.content.Context, android.content.Intent)
	 */
	@Override
	public void onReceive(Context context, Intent intent){ 
		if (context instanceof ServiceOverviewActivity){
			ServiceOverviewActivity soa = (ServiceOverviewActivity)context;
			soa.refreshServices();
		}
		abortBroadcast();
	}
}
