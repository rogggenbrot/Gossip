package de.astaro.gossip.background;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class StartServiceReceiver extends BroadcastReceiver{
	/*
	 * Start service when receiving a broadcast.
	 * 
	 * @see android.content.BroadcastReceiver#onReceive(android.content.Context, android.content.Intent)
	 */
	@Override
	public void onReceive(Context context, Intent intent){
		Intent service = new Intent(context, GossipServiceWatcher.class);
		context.startService(service);
	}
}
