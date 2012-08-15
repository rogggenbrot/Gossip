package de.astaro.gossip.background;

import de.astaro.gossip.R;
import de.astaro.gossip.ServiceOverviewActivity;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

public class NotifyReceiver extends BroadcastReceiver{
	
	/*
	 * Create a notification and raise it to the user by displaying a provided message.
	 * 
	 * @see android.content.BroadcastReceiver#onReceive(android.content.Context, android.content.Intent)
	 */
	@Override
	public void onReceive(Context context, Intent intent){
		
		Bundle b = intent.getExtras();
		if(!b.getString("msg").equals("")){
		
			NotificationManager notificationManager = (NotificationManager) 
			          context.getSystemService(context.NOTIFICATION_SERVICE);
		    Notification notification = new Notification(R.drawable.astaro_icon,
		            "Gossip Error Notification", System.currentTimeMillis());
	
		    // Hide the notification after its selected
		    notification.flags |= Notification.FLAG_AUTO_CANCEL;
		    
		    Intent i = new Intent(context, ServiceOverviewActivity.class);
		    PendingIntent activity = PendingIntent.getActivity(context, 0, i, 0);
		    notification.setLatestEventInfo(context, "Faulty services",
		        b.getString("msg"), activity);
		    
		    notification.number += 1;
		    notificationManager.notify(0, notification);
		}
	}
}
