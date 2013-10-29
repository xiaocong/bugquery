package com.borqs.bugreporter.manual;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.settings.Settings;
import com.borqs.bugreporter.settings.SettingsActivity;
import com.borqs.bugreporter.util.Util;

import android.os.Bundle;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.app.DialogFragment;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.text.TextUtils;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.Toast;

/**
 * 
 * Provide a UI to receive user's input, and report the issue manually.  
 *
 */
public class ManualReportActivity extends Activity implements OnClickListener {
	
	public static final String TAG = "ManualReportActivity";
	
	public static final String CATEGORY_ERROR = "ERROR";
	public static final String BUG_TYPE = "MANUALLY_REPORT";
	
	private static final int DLG_GIVE_UP_HINT          = 0;
	private static final int DLG_EMPTY_HINT            = 1;
	private static final int DLG_APP_NAME_MISSING      = 2;
	private static final int DLG_APP_PKG_MISSING       = 3;
	private static final int DLG_BUGREPORT_DISABLE     = 4;
	private static final int DLG_MANUAL_REPORT_DISABLE = 5;
	
	private EditText appNameET      = null;
	private EditText descriptionET  = null;
	private Button   submitBtn      = null;
	private static CheckBox apOnlineLogCB  = null;
//	private static CheckBox apOfflineLogCB = null;
	private static CheckBox radioLogCB     = null;
	
	private static final String EXTRA_APP_NAME = "APP_NAME";
	private static final String EXTRA_PACKAGE  = "PACKAGE";
	
	private String appName = null;
	private String appPkg  = null;
	private String appVer  = null;
	
	private Context context = null;
	private Settings settings = null;
	
	/**
	 * Initialize the UI and receive user's input.
	 */
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.manual_report_activity);
		
		context = this;
		settings = new Settings(context);
		
		appNameET      = (EditText)this.findViewById(R.id.app_name_content);
		descriptionET  = (EditText)this.findViewById(R.id.description_content);
		apOnlineLogCB  = (CheckBox)this.findViewById(R.id.ap_online_log);
//		apOfflineLogCB = (CheckBox)this.findViewById(R.id.ap_offline_log);
		radioLogCB     = (CheckBox)this.findViewById(R.id.radio_log);
		submitBtn      = (Button)this.findViewById(R.id.submit_btn);
		
		//Set listener for submit button
		submitBtn.setOnClickListener(this);
		
		
		//The action is: "android.intent.action.MAIN" if touch the apk icon in launcher.
		//If action is "com.borqs.bugreporter.MANUAL_REPORT" from other apps, 
		//we can get app_name/package_name from the intent.
		Intent intent = this.getIntent();
		String action = intent.getAction();
		if(TextUtils.isEmpty(action) || !action.equals(Util.Action.MANAUL_REPORT)) {
			return;
		}
		//Get app name
		if(intent.hasExtra(EXTRA_APP_NAME)){
			appName = intent.getStringExtra(EXTRA_APP_NAME);
			if(TextUtils.isEmpty(appName)){
				myShowDialog(DLG_APP_NAME_MISSING);
				return;
			}
			appNameET.setText(appName);
		}else{
			myShowDialog(DLG_APP_NAME_MISSING);
			return;
		}
		//Get package name
		if(intent.hasExtra(EXTRA_PACKAGE)){
			appPkg = intent.getStringExtra(EXTRA_PACKAGE);
			if(TextUtils.isEmpty(appPkg)){
				myShowDialog(DLG_APP_PKG_MISSING);
				return;
			}
			descriptionET.setText(appPkg);
			try{
				PackageInfo pInfo = getPackageManager().getPackageInfo(appPkg, 0);
				appVer = pInfo.versionName;
			}catch(NameNotFoundException nfe){						
				appVer = "Unknown";
			}
		}else{
			myShowDialog(DLG_APP_PKG_MISSING);
			return;
		}
	}
	
	
	@Override
	public void onBackPressed() {
		if (TextUtils.isEmpty(appNameET.getText().toString())
				&& TextUtils.isEmpty(descriptionET.getText().toString())) {
			super.onBackPressed();
		} else {
			myShowDialog(DLG_GIVE_UP_HINT);
		}
	}



	/**
	 * Submit the bug info to ReportDataWrapper after clicking "Submit" button.
	 */
	@Override
	public void onClick(View v) {
		switch(v.getId()) {
		case R.id.submit_btn:
			if (!settings.isBugReporterEnabled()){
				myShowDialog(DLG_BUGREPORT_DISABLE);
				break;
			}else if (!settings.isTypeEnabled(BUG_TYPE)){
				myShowDialog(DLG_MANUAL_REPORT_DISABLE);
				break;
			}
			
			//The description should not be empty
			if(TextUtils.isEmpty(descriptionET.getText().toString())) {
				Util.log(TAG, "Description is empty!");
				myShowDialog(DLG_EMPTY_HINT);
				return;
			}
			Util.log(TAG, "Description is not empty!");
			
			//Get the app name
			String name = "";
			if(!TextUtils.isEmpty(appPkg)){
				name = appPkg;
				Util.log(TAG, "appPkg: " + name);
			}else if(!TextUtils.isEmpty(appName)){
				name = appName;
				Util.log(TAG, "appName: " + name);
			}else if(!TextUtils.isEmpty(appNameET.getText().toString())){
				name = appNameET.getText().toString();
				Util.log(TAG, "appNameET: " + name);
			}else{
				name = "Unknown";
			}
			Util.log(TAG, "name is: " + name);
			
			
			//Get description
			String description = "";
			String prefix = "";
			if(!TextUtils.isEmpty(appName)) {
				prefix = "App name: " + appName + "   " + "Version: " + appVer 
						+ "\n-------------------------\n";
			}
			description = prefix + descriptionET.getText().toString();
			Util.log(TAG, "description: " + description);
			
			//Submit the bug info to ReportDataWrapper
			Intent target = new Intent(Util.Action.BUG_NOTIFY);
			target.putExtra(Util.ExtraKeys.CATEGORY, CATEGORY_ERROR);
			target.putExtra(Util.ExtraKeys.BUG_TYPE, BUG_TYPE);
			target.putExtra(Util.ExtraKeys.NAME, name);
			target.putExtra(Util.ExtraKeys.DESCRIPTION, description);
//			target.putExtra(Util.ExtraKeys.FILE_PATH, "/data/anr/traces.txt");
			target.putExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT, "" + apOnlineLogCB.isChecked());
			target.putExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT_RADIO, "" + radioLogCB.isChecked());
			startService(target);
			
//			finish();
			//Pop up toast and refresh UI
			Toast.makeText(this, "Submitting this bug to server...",
					Toast.LENGTH_LONG).show();
			appNameET.setText("");
			descriptionET.setText("");
			
			break;
		}
	}
	

	
	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		menu.add("Settings");
		return true;
	}
	
	@Override
	public boolean onMenuItemSelected(int featureId, MenuItem item) {
		String title = (String)item.getTitle();
		if(title.equals("Settings")){
			Intent intent = new Intent(this, SettingsActivity.class);
			startActivity(intent);
			return true;
		}else {
			return false;
		}
	}
	
	
	/**
	 * Show an alert dialog.
	 * @param id
	 */
	private void myShowDialog(int id) {
		DialogFragment newFragment = ManualReportFragment.newInstance(id);
	    newFragment.show(getFragmentManager(), "dialog");
	}
	
	
	/**
	 * 
	 * Create manual report alert dialogs.
	 *
	 */
	public static class ManualReportFragment extends DialogFragment {
		
		public static ManualReportFragment newInstance(int title) {
			ManualReportFragment frag = new ManualReportFragment();
	        Bundle args = new Bundle();
	        args.putInt("title", title);
	        frag.setArguments(args);
	        return frag;
		}

		/**
		 * Create alert dialog.
		 */
		@Override
		public Dialog onCreateDialog(Bundle savedInstanceState) {
			AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
		    
	        int id = getArguments().getInt("title");
	        
	        switch (id) {
	        case DLG_GIVE_UP_HINT:
	        	builder.setMessage("Are you sure you want to give up reporting?")
	        	.setPositiveButton("Yes", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						getActivity().finish();
					}
				})
				.setNegativeButton("No", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.cancel();
					}
				});
	        	break;
	        	
	        case DLG_EMPTY_HINT:
	        	builder.setMessage("Description field can't be empty!")
	        	.setNegativeButton("OK", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.cancel();
					}
				});
	        	break;
	        	
	        case DLG_APP_NAME_MISSING:
	        	builder.setMessage("Application name needed!")
	        	.setNegativeButton("OK", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						getActivity().finish();
					}
				});
	        	break;
	        	
	        case DLG_APP_PKG_MISSING:
	        	builder.setMessage("Application package needed!")
	        	.setNegativeButton("OK", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						getActivity().finish();
					}
				});
	        	break;
	        	
	        case DLG_BUGREPORT_DISABLE:
	        	builder.setMessage("BugReporter is disabled. You need to enable it by: menu -> " +
	        			"Settings -> BugReporter if you want to report bugs.")
	        	.setNegativeButton("OK", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.cancel();
					}
				});
	        	break;
	        	
	        case DLG_MANUAL_REPORT_DISABLE:
	        	builder.setMessage("Manully report function is disabled. You can enable it by: " +
	        			"menu -> Settings -> Type control list -> Manual Report")
	        	.setNegativeButton("OK", new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.cancel();
					}
				});
	        	break;
	        
	        }
			
	        AlertDialog alert = builder.create();
	        return alert;
		}
		
	}
	
}
