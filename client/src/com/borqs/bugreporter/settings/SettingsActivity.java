package com.borqs.bugreporter.settings;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.preference.CheckBoxPreference;
import android.preference.EditTextPreference;
import android.preference.Preference;
import android.preference.PreferenceFragment;
import android.preference.Preference.OnPreferenceChangeListener;
import android.preference.Preference.OnPreferenceClickListener;
import android.text.TextUtils;

/**
 * Provide switch for BurgReporter turn on/off, data connection, types to report, log on/off, data not sent, system info, etc.
 */
public class SettingsActivity extends Activity {
	
	private static final String TAG = "SettingsActivity";
	
	private static Context context = null;
	private static Settings settings = null;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		
		context = this;
		settings = new Settings(context);
		
		// Display the Settings Fragment
		getFragmentManager().beginTransaction().replace(android.R.id.content, new SettingsFragment()).commit(); 
	}
	
	public static class SettingsFragment extends PreferenceFragment implements OnPreferenceChangeListener, OnPreferenceClickListener {

		//Define the key for each preference
		private final String KEY_BUG_REPORT     = "bug_report";
		private final String KEY_SERVER_ADDRESS = "server_address";
		private final String KEY_WIFI_ONLY      = "wifi_only";
		private final String KEY_TYPE_CONTROL   = "type_control";
		private final String KEY_LOCAL_DATA     = "local_data";
		private final String KEY_SYSTEM_INFO    = "system_info";
		private final String KEY_UPLOAD_LOG     = "upload_log";
		private final String KEY_NOTIFICATION   = "notification";
		private final String KEY_ABOUT          = "about";
		
		//Define the preferences
		private CheckBoxPreference prefBugReport     = null;
		private EditTextPreference prefServerAddress = null;
		private CheckBoxPreference prefWifiOnly      = null;
		private CheckBoxPreference prefUploadLog     = null;
		private CheckBoxPreference prefUserNotify    = null;
		private Preference prefTypeControl = null;
		private Preference prefLocalData   = null;
		private Preference prefSystemInfo  = null;
		private Preference prefAbout       = null;
		
		/**
		 * Initialize settings preference.
		 */
		@Override
		public void onCreate(Bundle savedInstanceState) {
			Util.log(TAG, "onCreate()");
			super.onCreate(savedInstanceState);
			//Load the preference from an XML resource
			addPreferencesFromResource(R.xml.settings_activity);
			
			
			//Find each preference
			prefBugReport = (CheckBoxPreference) findPreference(KEY_BUG_REPORT);
			prefServerAddress = (EditTextPreference) findPreference(KEY_SERVER_ADDRESS);
			prefWifiOnly = (CheckBoxPreference) findPreference(KEY_WIFI_ONLY);
			prefUploadLog = (CheckBoxPreference) findPreference(KEY_UPLOAD_LOG);
			prefUserNotify = (CheckBoxPreference) findPreference(KEY_NOTIFICATION);
    		prefTypeControl = findPreference(KEY_TYPE_CONTROL);
    		prefLocalData = findPreference(KEY_LOCAL_DATA);
    		prefSystemInfo = findPreference(KEY_SYSTEM_INFO);
    		prefAbout = findPreference(KEY_ABOUT);
    		
    		//Set default server address
    		prefServerAddress.setText(settings.getServerAddress());
    		prefServerAddress.setSummary(prefServerAddress.getText());
    		
    		//Get the value of BugReporter's state
    		boolean isBREnabled = settings.isBugReporterEnabled();
    		prefBugReport.setChecked(isBREnabled);//Set BugReport default state
    		prefWifiOnly.setChecked(settings.isViaWifiOnly());
    		prefUploadLog.setChecked(settings.isUploadLog());
    		Util.log(TAG, "settings.isShowUserNotificaion(): " + settings.isShowUserNotificaion());
    		prefUserNotify.setChecked(settings.isShowUserNotificaion());
    		Util.log(TAG, "prefUserNotify.isChecked(): " + prefUserNotify.isChecked());
    		
    		//The state of the following preferences depend on the state of BugReporter
    		prefServerAddress.setEnabled(isBREnabled);
    		prefWifiOnly.setEnabled(isBREnabled);
    		prefUploadLog.setEnabled(isBREnabled);
    		prefUserNotify.setEnabled(isBREnabled);
    		prefTypeControl.setEnabled(isBREnabled);
    		prefLocalData.setEnabled(isBREnabled);
    		prefSystemInfo.setEnabled(isBREnabled);
    		prefAbout.setEnabled(isBREnabled);
    		
    		//Set listener for each preference
    		prefBugReport.setOnPreferenceChangeListener(this);
    		prefServerAddress.setOnPreferenceChangeListener(this);
    		prefWifiOnly.setOnPreferenceChangeListener(this);
    		prefUploadLog.setOnPreferenceChangeListener(this);
    		prefUserNotify.setOnPreferenceChangeListener(this);
    		prefTypeControl.setOnPreferenceClickListener(this);
    		prefLocalData.setOnPreferenceClickListener(this);
    		prefSystemInfo.setOnPreferenceClickListener(this);
    		prefAbout.setOnPreferenceClickListener(this);
		}
		
		/**
		 * Listen and handle the preference change event.
		 */
		@Override
		public boolean onPreferenceChange(Preference preference, Object newValue) {
			Util.log(TAG, "onPreferenceChange()");
			
			String key = preference.getKey();
			Util.log(key, "key=" + key);
			if(TextUtils.isEmpty(key)){
				return false;
			}
			
			if(key.equals(KEY_BUG_REPORT)){
				Boolean value = (Boolean)newValue;
				settings.setBugReporterEnable(value);
	    		prefServerAddress.setEnabled(value);
	    		prefWifiOnly.setEnabled(value);
	    		prefUploadLog.setEnabled(value);
	    		prefUserNotify.setEnabled(value);
	    		prefTypeControl.setEnabled(value);
	    		prefLocalData.setEnabled(value);
	    		prefSystemInfo.setEnabled(value);
	    		prefAbout.setEnabled(value);
	    		
			}else if(key.equals(KEY_SERVER_ADDRESS)){
				settings.setServerAddress((String)newValue);
				prefServerAddress.setSummary((String)newValue);
			}else if(key.equals(KEY_WIFI_ONLY)){
				settings.setViaWifiOnly((Boolean)newValue);
			}else if(key.equals(KEY_UPLOAD_LOG)){
				settings.setUploadLog((Boolean)newValue);
			}else if(key.equals(KEY_NOTIFICATION)){
				settings.setShowUserNotification((Boolean)newValue);
			}else{
				//other value
			}
			return true;
		}
		
		/**
		 * Listen and handle the preference click event.
		 */
		@Override
		public boolean onPreferenceClick(Preference preference) {
			Util.log(TAG, "onPreferenceClick()");
			
			String key = preference.getKey();
			Util.log(key, "key=" + key);
			if(TextUtils.isEmpty(key)){
				return false;
			}
			
			if(key.equals(KEY_TYPE_CONTROL)){
				Intent intent = new Intent(Util.Action.TYPE_CONTROL_LIST);
				intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
				context.startActivity(intent);
			}else if(key.equals(KEY_LOCAL_DATA)){
				Intent intent = new Intent(Util.Action.VIEW_LOCAL_DATA);
				intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
				context.startActivity(intent);			
			}else if(key.equals(KEY_SYSTEM_INFO)){
				Intent intent = new Intent(Util.Action.VIEW_SYS_INFO);
				intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);	
				context.startActivity(intent);
			}else if (key.equals(KEY_ABOUT)) {
				Intent intent = new Intent(Util.Action.VIEW_ABOUT);
				intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);	
				context.startActivity(intent);
			}else{
				//other value
			}
			
			return true;
		}
		
	}
	
}
