package com.borqs.bugreporter.dev;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import com.borqs.bugreporter.util.Util;


public class DevLauncherReceiver extends BroadcastReceiver {

	private static final boolean DBG = Util.DBG;
	private static final String tag = "DevLauncherReceiver";
	private static final String SECRET_CODE = "338";
	
	@Override
	public void onReceive(Context context, Intent intent) {
		if (DBG) Util.log(tag,"DevLauncherReceiver!");		
		if(context == null){
			if (DBG) Util.log(tag, "Context null!");
			return;
		}
		if(intent == null){
			if (DBG) Util.log(tag, "Intent null!");
			return;
		}
		
		String action = intent.getAction();		
		if(null == action || "".equals(action)){
			if (DBG) Util.log(tag, "Action null!");
			return;
		}
		String code = intent.getData() != null ? intent.getData().getHost() : null;

		//Start CATEGORY_TEST launcher activity by "*#*#338#*#*".
		if ("android.provider.Telephony.SECRET_CODE".equals(action) && SECRET_CODE.equals(code)) {
			Intent launcherIntent = new Intent(Intent.ACTION_MAIN);
			launcherIntent.setClass(context, DevLauncherActivity.class);
			launcherIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
			context.startActivity(launcherIntent);
		}
	}
}
