package com.borqs.bugreporter.collector;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import com.borqs.bugreporter.util.Util;
import android.app.AlarmManager;
import android.app.IntentService;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;

/**
 * 
 * Calculate living time.
 * 
 */
public class LiveTimeCollector extends IntentService {
	
	private final static String TAG = "LiveTimeCollector";	
	
	public static final String LIVE_TIME_RECORD = "live_time_record.txt";
//	public static final String MONITOR_TYPE = "LIVE_TIME";
	public static final String MONITOR_TYPE = "com.borqs.bugreporter";
	public static final String NAME = "LIVE_TIME";
	public static final String CATEGORY = "STATISTIC";
	
	private static long recordInterval = AlarmManager.INTERVAL_HOUR;
	private static long submitInterval = 6 * 60 * 60 * 1000;// 6 hours
	
	
	/**
	 * Calculate living time. 
	 */
	public LiveTimeCollector() {
		super(TAG);
	}

	/**
	 * Monitor the live time every hour and submit live time data every 6 hours.
	 */
	@Override
	protected void onHandleIntent(Intent arg0) {
		Util.log(TAG, "===========Monitor Live Time============");
		Intent target = new Intent();
		
		long[] last = getLastLiveTime(this);
		long time = 0;
		
		if (last[0] == -1 || last[1] == -1) {
			time = 0;
		}else {
			long elapsedSinceBoot = SystemClock.elapsedRealtime();
			if (elapsedSinceBoot < last[0]) {
				time = last[1] + elapsedSinceBoot;
			}else {
				time = last[1] + (elapsedSinceBoot - last[0]);
			}
		}
		Util.log(TAG, "time="+(time/1000));
		
		if ((time + 3000) >= submitInterval) {//To avoid "3 secs less than xxx"
			target.setAction(Util.Action.BUG_NOTIFY);
			target.putExtra(Util.ExtraKeys.CATEGORY, CATEGORY);
			target.putExtra(Util.ExtraKeys.BUG_TYPE, MONITOR_TYPE);
			target.putExtra(Util.ExtraKeys.NAME, NAME);
			target.putExtra(Util.ExtraKeys.DESCRIPTION, "" + (time/1000));
			startService(target);
			
			time = 0;
			Util.log(TAG, "===========Submit a live time data.============");
		}
		setCurrentLiveTime(this, time);
	}
	

	/**
	 * Trigger Alarm Clock.
	 * @param ctx
	 * @param enable
	 */
	public static void set(Context context, boolean enable) {
		Util.log(TAG, "-----set()--AlarmClock : " + enable);
		Intent liveTimeIntent = new Intent(Util.Action.MONITOR_LIVE_TIME);
		PendingIntent liveTimeTriger = PendingIntent.getService(context, 0, liveTimeIntent, 0);
		//launch 5 mins later to avoid too many works on receiving boot completed. 
		long firstTime = System.currentTimeMillis() + 5 * 60 * 1000;
		AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
		
		if (enable) {
			am.setRepeating(AlarmManager.RTC, firstTime, recordInterval, liveTimeTriger);
		}else {
			am.cancel(liveTimeTriger);
			File recordFile = new File(context.getFilesDir().getPath() 
					+ File.separator + LIVE_TIME_RECORD);
			if(recordFile.exists()) {
				recordFile.delete();
			}
		}
	}
	
	
	/*
	 * Set current time.
	 */
	private void setCurrentLiveTime(Context context, long time) {
		DataOutputStream dos = null;
		try {
			dos = new DataOutputStream(this.openFileOutput(LIVE_TIME_RECORD, Context.MODE_PRIVATE));
			dos.writeLong(SystemClock.elapsedRealtime());
			dos.writeLong(time);
		}catch (Exception e) {
			e.printStackTrace();
		}finally {
			if (dos != null){
				try {
					if (dos != null)
						dos.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
	}
	
	/*
	 * Get last live time.
	 */
	private long[] getLastLiveTime(Context context) {
		long lastTime = -1;
		long lastValue = -1;
		DataInputStream dis = null;
		try {
			dis = new DataInputStream(context.openFileInput(LIVE_TIME_RECORD));
			lastTime = dis.readLong();
			lastValue = dis.readLong();
		}catch (Exception e) {
			e.printStackTrace();
		}finally {
			try {
				if (dis != null)
					dis.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
		return new long[] {lastTime, lastValue};
	}
	
	
	/**
	 * Get the value of record interval time.
	 * @return
	 */
	public static long getRecordInterval() {
		return recordInterval;
	}
	/**
	 * Set a new value of recordInterval.
	 * @param interval
	 */
	public static void setRecordInterval(long interval) {
		recordInterval = interval;
	}
	
	/**
	 * Get the value of submit interval time.
	 * @return
	 */
	public static long getSubmitInterval() {
		return submitInterval;
	}
	/**
	 * Set a new value of submitInterval.
	 * @param interval
	 */
	public static void setSubmitInterval(long interval) {
		submitInterval = interval;
	}
}
