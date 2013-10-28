package com.borqs.bugreporter;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.TextView;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;

/*
 * Sending result notify.
 */
public class UserNotifyActivity  extends Activity{
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		
		Intent intent = this.getIntent();
		String action = intent.getAction();
		
		if((!TextUtils.isEmpty(action)) && (action == Util.Action.NOTIFY_RESULT)) {
			setContentView(R.layout.user_notify_activity);
			
			TextView textView = (TextView)this.findViewById(R.id.displayText);
			if(textView != null){
				String message = intent.getStringExtra(Util.NOTIFY_MESSAGE);
				textView.setText(message);
				textView.append(" Press back to exit.");
			}
			
		}else {
			return;
		}
	}
	

}
