package com.borqs.bugreporter;

import com.borqs.bugreporter.collector.DropBoxCollector;
import com.borqs.bugreporter.settings.Settings;
import com.borqs.bugreporter.util.Util;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.net.ConnectivityManager;
import android.os.DropBoxManager;
import android.text.TextUtils;

/**
 * 
 * This class receives system messages including dropbox, boot complete 
 * and network state change messages.
 */
public class MessageReceiver extends BroadcastReceiver {

	private static final String TAG = "MessageReceiver";
	
	/**
	 * onReceive method mainly receives three kind of system messages:<br>
	 * 1.DropBox entry added message --> DropBoxManager.ACTION_DROPBOX_ENTRY_ADDED.<br>
	 * 2.Boot Complete message --> Intent.ACTION_BOOT_COMPLETED.<br>
	 * 3.Network state change message --> ConnectivityManager.CONNECTIVITY_ACTION.<br>
	 */
	@Override
	public void onReceive(Context context, Intent intent) {
		
		//Get action, and make sure it's not null or 0-length
		String action = intent.getAction();
		if (TextUtils.isEmpty(action)) {
			return;
		}
		
		//Create a new intent
		Intent target = new Intent();
		
		//DropBoxManager.ACTION_DROPBOX_ENTRY_ADDED
		if (action.equals(DropBoxManager.ACTION_DROPBOX_ENTRY_ADDED)) {
			Util.log(TAG, "Received DropBox message...");
			String extraTag = intent.getStringExtra(DropBoxManager.EXTRA_TAG);
			Util.log(TAG, "extraTag: " + extraTag);
			if (!TextUtils.isEmpty(extraTag)
					&& DropBoxCollector.isInterestedTag(extraTag)) {
				target.setAction(Util.Action.ACTION_MSG_DROPBOX);
				target.putExtras(intent);
			} else {
				return;
			}
		}
		//Intent.ACTION_BOOT_COMPLETED
		else if (action.equals(Intent.ACTION_BOOT_COMPLETED)) {
			Util.log(TAG ,"Received system boot completed message...");
			Settings settings=new Settings(context);
			if(settings.isFirstBoot()){
				if(Util.SysInfo.isUserBuild()){
					settings.setBugReporterEnable(false);
				}else{
					settings.setBugReporterEnable(true);
				}
				settings.setFirstBoot(false);
			}
			
			//Set system info shared preference value to false every time
			SharedPreferences sp = context.getSharedPreferences("SystemInfoPreference", context.MODE_PRIVATE);
			Editor editor = sp.edit();
			editor.putBoolean(Util.SysInfo.SYSTEM_INFO, false);
			editor.commit();
			
			//Set BOOT action
			target.setAction(Util.Action.ACTION_MSG_BOOT);
		}
		//ConnectivityManager.CONNECTIVITY_ACTION
		else if (action.equals(ConnectivityManager.CONNECTIVITY_ACTION)) {
			Util.log(TAG, "Received connectivity changed message...");
			target.setAction(Util.Action.SEND_REPORT);
		}else {
			//If there are other system messages...
			return;
		}
		
		//Transfer the message to processor service
		if (target != null){
			context.startService(target);
			target = null;
		}
		
	}

}
