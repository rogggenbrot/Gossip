package de.astaro.gossip.background;

import java.util.Calendar;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.preference.PreferenceManager;

public class ScheduleReceiver extends BroadcastReceiver{
	
	
	@Override
	public void onReceive(Context context, Intent intent){
		AlarmManager service = (AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
		Intent i = new Intent(context, StartServiceReceiver.class);
		PendingIntent pending = PendingIntent.getBroadcast(context, 0, i, PendingIntent.FLAG_CANCEL_CURRENT);
		
		int interval = Integer.parseInt(PreferenceManager.getDefaultSharedPreferences(context)
													.getString("interval", "5")) * 60000;
		// Start 5 seconds after boot completed
		Calendar cal = Calendar.getInstance();
		cal.add(Calendar.SECOND, 5);
		// InexactRepeating allows Android to optimize the energy consumption
		service.setInexactRepeating(AlarmManager.RTC_WAKEUP, cal.getTimeInMillis(), 
					interval, pending);
	}
}
