package com.borqs.bugreporter.settings;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.collector.LiveTimeCollector;
import com.borqs.bugreporter.provider.DBHelper;
import com.borqs.bugreporter.settings.Settings.TypeControl;
import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.preference.CheckBoxPreference;
import android.preference.Preference;
import android.preference.PreferenceScreen;
import android.preference.Preference.OnPreferenceChangeListener;
import android.preference.PreferenceFragment;
import android.text.TextUtils;

/**
 * Provide a list of bug types for users to control which type to track.
 */
public class TypeControlListActivity extends Activity {
	
	private static final String TAG = "TypeControlListActivity";
	
	private static Context context = null;
	private static Settings settings = null;
	private static DBHelper dbHelper = null;
	

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		Util.log(TAG, "Enter TypeControlListActivity...");
		
		context = this;
		settings = new Settings(context);
		dbHelper = new DBHelper(context);

		
		// Display the TypeControlList Fragment
		getFragmentManager().beginTransaction().replace(android.R.id.content, new TypeControlListFragment()).commit(); 
	}
	
	
	public static class TypeControlListFragment extends PreferenceFragment implements OnPreferenceChangeListener {

		/**
		 * Initialize the TypeControlList Preference screen
		 */
		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			
			//Load the preference from an XML resource
			addPreferencesFromResource(R.xml.type_control_list_activity);
			
			PreferenceScreen prefScreen = getPreferenceScreen();
			try{
				//Read the type control list from database
				TypeControl[] list = dbHelper.getTypeControlList();
				if(list == null){
					getActivity().finish();
					return;
				}
				//Set listener for each preference item
				for(int i = 0; i < list.length; i++) {
					final String type = list[i].type;
					CheckBoxPreference item = new CheckBoxPreference(context);
					item.setTitle(type);
					item.setChecked(list[i].allowed);
					item.setSummaryOn("Allow sending");
					item.setSummaryOff("Block sending");
					item.setOnPreferenceChangeListener(this);
					prefScreen.addPreference(item);
				}
			}catch(Exception e){
				e.printStackTrace();
				getActivity().finish();
				return;
			}
		}

		/**
		 * Listen and handle the preference change event.
		 */
		@Override
		public boolean onPreferenceChange(Preference preference, Object newValue) {
			Util.log(TAG, "onPreferenceChange()");
			
			//Get the preference title
			CharSequence type = preference.getTitle();
			if(TextUtils.isEmpty(type)){
				return false;
			}
			Util.log(TAG, "onPreferenceChange,type: " + type);
			
			//Set a new value of the type
			Boolean state = (Boolean)newValue;
			settings.setTypeEnabled(type.toString(), state);
			
			//setRepeat/cancel AlarmManager if live_time state changes.
			if (type == LiveTimeCollector.MONITOR_TYPE) {
				LiveTimeCollector.set(context, state);
			}
			
			return true;
		}

	}
	
}
