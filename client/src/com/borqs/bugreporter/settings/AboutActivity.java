package com.borqs.bugreporter.settings;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;
import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.preference.Preference;
import android.preference.PreferenceFragment;

/**
 * 
 * Display the BugReporter version information.
 * 
 */
public class AboutActivity extends Activity {

	
	private static Context context = null;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		context = this;
		
		// Display the Settings Fragment
		getFragmentManager().beginTransaction().replace(android.R.id.content, new AboutFragment()).commit(); 
	}
	
	
	public static class AboutFragment extends PreferenceFragment {

		//Define the key for each preference
		private final String KEY_VERSION_NAME = "version_name";
		private final String KEY_VERSION_CODE = "version_code";
		
		//Define the preferences
		private Preference prefVesrionName = null;
		private Preference prefVersionCode = null;
		
		/**
		 * Initialize About preference.
		 */
		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			//Load the preference from an XML resource
			addPreferencesFromResource(R.xml.about_activity);
			
			//Find each preference
			prefVesrionName = findPreference(KEY_VERSION_NAME);
			prefVersionCode = findPreference(KEY_VERSION_CODE);
    		
    		//Set the version name and version code
			String versionName = Util.SysInfo.getSelfVersionName(context);
			if (versionName!= null) {
				prefVesrionName.setSummary(versionName);
			}
			
			String versionCode = Util.SysInfo.getSelfVersionCode(context);
			
			if (versionCode != null) {
				prefVersionCode.setSummary(versionCode);
			}
			
		}
	}
	
}
