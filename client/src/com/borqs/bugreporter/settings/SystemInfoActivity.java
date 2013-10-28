package com.borqs.bugreporter.settings;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import com.borqs.bugreporter.R;
import com.borqs.bugreporter.provider.DBHelper;
import com.borqs.bugreporter.util.Util;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.os.Bundle;
import android.preference.Preference;
import android.preference.PreferenceFragment;
import android.text.TextUtils;

/**
 * View the system information.
 */
public class SystemInfoActivity extends Activity {
	
	private static final String TAG = "SystemInfoActivity";
	
	private static Context context = null;
	private static ContentValues sysInfo = null;
	
	private static Map<String,String> extraInfo = new HashMap<String, String>();
	private DBHelper dbHelper = null;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		context = this;
		dbHelper = new DBHelper(context);
		Intent intent=getIntent();
		String action = intent.getAction();
		if (TextUtils.isEmpty(action)) {
			finish();
			return;
		}
		
		//Get shared preference
		SharedPreferences sp = context.getSharedPreferences("SystemInfoPreference", MODE_PRIVATE);
		//If true, get system info from database
		if (sp.getBoolean(Util.SysInfo.SYSTEM_INFO, false)) {
			Util.log(TAG, "get sysInfo from database...");
			sysInfo = dbHelper.getSysInfo();
		}else {
			//If false, get system info now, and save to database
			Util.log(TAG, "get sysInfo now...");
			sysInfo = Util.SysInfo.getSysInfo(this);
			
			//store shared preference value
			Editor editor = sp.edit();
			editor.putBoolean(Util.SysInfo.SYSTEM_INFO, true);
			editor.commit();
			
			//store to database
			dbHelper.storeSystemInfo(sysInfo);
		}
		
		
//		if (intent.hasExtra(Util.ExtraKeys.SYS_INFO)) {
//			sysInfo = (ContentValues) intent.getParcelableExtra(Util.ExtraKeys.SYS_INFO);
//			Util.log(TAG, "get sysInfo from intent extra.");
//		} else {
//			sysInfo = Util.SysInfo.getSysInfo(this);
//			Util.log(TAG, "get sysInfo now...");
//		}
		
		Set<Map.Entry<String, Object>> valueSet = sysInfo.valueSet();
		Iterator<Map.Entry<String, Object>> list = valueSet.iterator();
		while (list.hasNext()) {
			Map.Entry<String, Object> entry = list.next();
			String key = entry.getKey();
			String value = (String) entry.getValue();
			extraInfo.put(key, value);
		}
		
		
		// Display the Settings Fragment
		getFragmentManager().beginTransaction().replace(android.R.id.content, new SystemInfoFragment()).commit(); 
	}
	
	
	public static class SystemInfoFragment extends PreferenceFragment {

		/**
		 * Initialize System Info preference.
		 */
		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			//Load the preference from an XML resource
			addPreferencesFromResource(R.xml.system_info_activity);
			
			//set each preference
			//device info
			Preference pref1 = findPreference("phone_number");
			pref1.setTitle(Util.JSON.PHONE_NUMBER);
			pref1.setSummary(extraInfo.get(Util.JSON.PHONE_NUMBER));
			
			Preference pref2 = findPreference("imei_number");
			pref2.setTitle(Util.JSON.IMEI_NUMBER);
			pref2.setSummary(extraInfo.get(Util.JSON.IMEI_NUMBER));
			
			Preference pref4 = findPreference("wifi_mac");
			pref4.setTitle(Util.JSON.WIFI_MAC);
			pref4.setSummary(extraInfo.get(Util.JSON.WIFI_MAC));
			
			
			//Build info
			Preference pref5 = findPreference("kernel_version");
			pref5.setTitle(Util.JSON.KERNEL_VERSION);
			pref5.setSummary(extraInfo.get(Util.JSON.KERNEL_VERSION));
			
			Preference pref7 = findPreference("platform_ware");
			pref7.setTitle(Util.JSON.PLATFORM_WARE);
			pref7.setSummary(extraInfo.get(Util.JSON.PLATFORM_WARE));
			
			Preference pref8 = findPreference("custom_build_version");
			pref8.setTitle(Util.JSON.CUSTOM_BUILD_VERSION);
			pref8.setSummary(extraInfo.get(Util.JSON.CUSTOM_BUILD_VERSION));
			
			
			//(standard build info)
			Preference pref9 = findPreference("board");
			pref9.setTitle(Util.JSON.BOARD);
			pref9.setSummary(extraInfo.get(Util.JSON.BOARD));
			
			Preference pref10 = findPreference("bootloader");
			pref10.setTitle(Util.JSON.BOOTLOADER);
			pref10.setSummary(extraInfo.get(Util.JSON.BOOTLOADER));
			
			Preference pref11 = findPreference("brand");
			pref11.setTitle(Util.JSON.BRAND);
			pref11.setSummary(extraInfo.get(Util.JSON.BRAND));
			
			Preference pref12 = findPreference("cpu_abi");
			pref12.setTitle(Util.JSON.CPU_ABI);
			pref12.setSummary(extraInfo.get(Util.JSON.CPU_ABI));
			
			Preference pref13 = findPreference("cpu_abi2");
			pref13.setTitle(Util.JSON.CPU_ABI2);
			pref13.setSummary(extraInfo.get(Util.JSON.CPU_ABI2));
			
			Preference pref14 = findPreference("device");
			pref14.setTitle(Util.JSON.DEVICE);
			pref14.setSummary(extraInfo.get(Util.JSON.DEVICE));
			
			Preference pref15 = findPreference("display");
			pref15.setTitle(Util.JSON.DISPLAY);
			pref15.setSummary(extraInfo.get(Util.JSON.DISPLAY));
			
			Preference pref16 = findPreference("fingerprint");
			pref16.setTitle(Util.JSON.FINGERPRINT);
			pref16.setSummary(extraInfo.get(Util.JSON.FINGERPRINT));
			
			Preference pref17 = findPreference("hardware");
			pref17.setTitle(Util.JSON.HARDWARE);
			pref17.setSummary(extraInfo.get(Util.JSON.HARDWARE));
			
			Preference pref18 = findPreference("host");
			pref18.setTitle(Util.JSON.HOST);
			pref18.setSummary(extraInfo.get(Util.JSON.HOST));
			
			Preference pref19 = findPreference("id");
			pref19.setTitle(Util.JSON.ID);
			pref19.setSummary(extraInfo.get(Util.JSON.ID));
			
			Preference pref20 = findPreference("manufacture");
			pref20.setTitle(Util.JSON.MANUFACTURER);
			pref20.setSummary(extraInfo.get(Util.JSON.MANUFACTURER));
			
			Preference pref21 = findPreference("model");
			pref21.setTitle(Util.JSON.MODEL);
			pref21.setSummary(extraInfo.get(Util.JSON.MODEL));
			
			Preference pref22 = findPreference("product");
			pref22.setTitle(Util.JSON.PRODUCT);
			pref22.setSummary(extraInfo.get(Util.JSON.PRODUCT));
			
			Preference pref23 = findPreference("radio");
			pref23.setTitle(Util.JSON.RADIO);
			pref23.setSummary(extraInfo.get(Util.JSON.RADIO));
			
			Preference pref24 = findPreference("serial");
			pref24.setTitle(Util.JSON.SERIAL);
			pref24.setSummary(extraInfo.get(Util.JSON.SERIAL));
			
			Preference pref25 = findPreference("tags");
			pref25.setTitle(Util.JSON.TAGS);
			pref25.setSummary(extraInfo.get(Util.JSON.TAGS));
			
			Preference pref26 = findPreference("time");
			pref26.setTitle(Util.JSON.BUILD_TIME);
			pref26.setSummary(extraInfo.get(Util.JSON.BUILD_TIME));
			
			Preference pref27 = findPreference("type");
			pref27.setTitle(Util.JSON.TYPE);
			pref27.setSummary(extraInfo.get(Util.JSON.TYPE));
			
			Preference pref28 = findPreference("user");
			pref28.setTitle(Util.JSON.USER);
			pref28.setSummary(extraInfo.get(Util.JSON.USER));
			
			Preference pref29 = findPreference("version_codename");
			pref29.setTitle(Util.JSON.VERSION_CODENAME);
			pref29.setSummary(extraInfo.get(Util.JSON.VERSION_CODENAME));
			
			Preference pref30 = findPreference("version_incremental");
			pref30.setTitle(Util.JSON.VERSION_INCREMENTAL);
			pref30.setSummary(extraInfo.get(Util.JSON.VERSION_INCREMENTAL));
			
			Preference pref31 = findPreference("version_release");
			pref31.setTitle(Util.JSON.VERSION_RELEASE);
			pref31.setSummary(extraInfo.get(Util.JSON.VERSION_RELEASE));
			
			Preference pref32 = findPreference("version_sdk");
			pref32.setTitle(Util.JSON.VERSION_SDK);
			pref32.setSummary(extraInfo.get(Util.JSON.VERSION_SDK));
    		
		}
	}
}
