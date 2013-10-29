package com.borqs.bugreporter;

import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import com.borqs.bugreporter.collector.DropBoxCollector;
import com.borqs.bugreporter.collector.LiveTimeCollector;
import com.borqs.bugreporter.util.Util;
import android.app.IntentService;
import android.content.Intent;
import android.os.DropBoxManager;
import android.text.TextUtils;

/**
 * 
 * This class handles the requests received from MessageReciever.
 * Get bug info from specified collector and send these info to ReportDataWrapper.
 *
 */
public class ProcessorService extends IntentService {
	
	private static final String TAG = "ProcessorService";

	public ProcessorService() {
		super(TAG);
	}

	/**
	 * Handle the requests received from MessageReciever:<br>
	 * 1.Request of collecting dropbox info.<br>
	 * 2.Request of collecting boot complete related info.<br>
	 */
	@Override
	protected void onHandleIntent(Intent intent) {
		Util.log(TAG, "Received intent.");
		
		//Get action, and make sure it's not null or 0-length
		String action = intent.getAction();
		if (TextUtils.isEmpty(action)) {
			return;
		}
		
		Map<String,String> extraInfo = null;
		String tag = null;
		long time = -1;
		
		
		//handle info from different request action
		//Util.Action.ACTION_MSG_DROPBOX
		if (action.equals(Util.Action.ACTION_MSG_DROPBOX)) {
			tag = intent.getStringExtra(DropBoxManager.EXTRA_TAG);
			time = intent.getLongExtra(DropBoxManager.EXTRA_TIME, -1);
			Util.log(TAG, "extraTag|" + tag);
			Util.log(TAG, "extraTime|" + time);
			
			//Get extras
			try {
				extraInfo = DropBoxCollector.class.newInstance().getBugInfo(this, tag, time);
			} catch (InstantiationException e) {
				e.printStackTrace();
			} catch (IllegalAccessException e) {
				e.printStackTrace();
			}
		}
		//action.equals(Util.Action.ACTION_MSG_BOOT
		else if (action.equals(Util.Action.ACTION_MSG_BOOT)) {
			//1. Calculate live time: Trigger AlarmClock for calculating live time
			LiveTimeCollector.set(this, true);
			
			//2. Check kernel panic info
//			try {
//				extraInfo = KernelPanicCollector.class.newInstance().getBugInfo(this, tag, time);
//			} catch (InstantiationException e) {
//				e.printStackTrace();
//			} catch (IllegalAccessException e) {
//				e.printStackTrace();
//			}
//			
//			//3. Check CP panic
			
		}
		
		
		//Send to ReportDataWrapper
		if (extraInfo == null) {
			return;
		}
		Intent target = new Intent(Util.Action.BUG_NOTIFY);
		Set<Map.Entry<String,String>> set = extraInfo.entrySet();
		Iterator<Map.Entry<String,String>> list = set.iterator();
		while(list.hasNext()){
			Map.Entry<String,String> entry = list.next();
			target.putExtra(entry.getKey(), entry.getValue());
		}
		Util.log(TAG, "...send to ReportDataWrapper...");
		startService(target);
		Util.log(TAG, "...send to ReportDataWrapper finished");
	}
	
}
