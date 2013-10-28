package com.borqs.bugreporter.util;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipArchiveInputStream;
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream;
import org.apache.commons.compress.utils.IOUtils;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.collector.Collector;
import com.borqs.bugreporter.provider.DBHelper;
import com.borqs.bugreporter.settings.Settings;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.telephony.TelephonyManager;
import android.text.TextUtils;
import android.util.Log;


/**
 * This class provides base utilities for implementing some functions.
 */
public class Util {
	
	public static final String TAG = "BugReporter";
	public static final String tag = "Util";
	public static final boolean DBG = android.os.Build.TYPE.equals("user") ? Log.isLoggable(TAG, Log.DEBUG) : true;

	
	public static void log(String msg) {
		if (msg == null) {
			return;
		}
		Log.d(TAG, msg);
	}
	public static void log(String tag, String msg) {
		if (msg == null) {
			return;
		}
		msg = tag + "|" + msg;
		log(msg);
	}
	
	
	/**
	 * 
	 * Define the actions.
	 *
	 */
	public static class Action {
		public static final String ACTION_MSG_DROPBOX   = "com.borqs.bugreporter.ACTION_MSG_DROPBOX";
		public static final String ACTION_MSG_BOOT      = "com.borqs.bugreporter.ACTION_MSG_BOOT";
		public static final String BUG_NOTIFY           = "com.borqs.bugreporter.BUG_NOTIFY";
		public static final String SEND_REPORT          = "com.borqs.bugreporter.SEND_REPORT";
		
		public static final String MONITOR_LIVE_TIME    = "com.borqs.bugreporter.MONITOR_LIVE_TIME";
		public static final String MANAUL_REPORT        = "com.borqs.bugreporter.MANUAL_REPORT";
		
		public static final String VIEW_SYS_INFO        = "com.borqs.bugreporter.VIEW_SYSTEM_INFO";
		public static final String TYPE_CONTROL_LIST    = "com.borqs.bugreporter.TYPE_CONTROL_LIST";
		public static final String VIEW_LOCAL_DATA      = "com.borqs.bugreporter.VIEW_LOCAL_DATA";
		public static final String VIEW_ABOUT           = "com.borqs.bugreporter.VIEW_ABOUT";
		
		public static final String NOTIFY_RESULT        = "com.borqs.bugreporter.NOTIFY_RESULT";
		
	}
	
	
	/**
	 * 
	 * Define the extras info.
	 *
	 */
	public static class ExtraKeys {

		public static final String CATEGORY    = "CATEGORY";
		public static final String BUG_TYPE    = "BUG_TYPE";
		public static final String NAME        = "NAME";
		public static final String DESCRIPTION = "DESCRIPTION";
		/*
		 * The key for providing file path, the file(s) specified by this way will be removed after processing.
		 * The value can be multiple file path, separated by semi-colon.
		 */
		public static final String FILE_PATH   = "FILE_PATH";
		/*
		 * The key for providing file path, but the file(s) specified by this way will be kept after processing.
		 * The value can be multiple file path, separated by semi-colon.  
		 */
		public static final String FILE_KEEP   = "FILE_KEEP";
		public static final String SYS_INFO    = "SYS_INFO";
		
		public static final String ENABLE_ONLINE_LOGCAT       = "ENABLE_ONLINE_LOGCAT";
		public static final String ENABLE_ONLINE_LOGCAT_RADIO = "ENABLE_ONLINE_LOGCAT_RADIO";

	}
	
	
	/**
	 * Define report data structure.
	 */
	public static class ReportData {
		
		public String category = null;
		public String bugType  = null;
		public String name     = null;
		public String info     = null;
		public String filePath = null;
		public String fileKeep = null;
		public String time     = null;
		public String uuid     = null;
		public ContentValues sysInfo = null;

		public boolean hasOnlineLog      = false;
		public boolean hasOnlineRadioLog = false;
		
		public long id = -1;
		public long serverId = -1;
		

		/**
		 * Get data item count in database
		 * @param context
		 * @return
		 */
		public int getCount(Context context) {
			DBHelper dbHelper = new DBHelper(context);
			int count = dbHelper.getCount();
			dbHelper = null;
			return count;
		}
		
		/**
		 * Get all the report data items from database.
		 * @param context
		 * @return
		 */
		public static ReportData[] getReportData(Context context) {
			//if(DBG) Util.log(tag, "getReportData()[]");
			DBHelper dbHelper = new DBHelper(context);
			ReportData[] datas = dbHelper.getReportData();
			dbHelper = null;
			return datas;
		}
		
		/**
		 * Delete the report data
		 * @param context
		 */
		public void delete(Context context){
			//if(DBG) Util.log(tag,"delete(Context)");
			DBHelper dbHelper = new DBHelper(context);
			dbHelper.delReportData(id);
			dbHelper = null;
			
			/*Reset all data*/
			category = null;
			bugType = null;
			name = null;
			info = null;
			filePath = null;
			time = null;
			uuid = null;
			
			id = -1;
			serverId = -1;
		}
		
		
		//Some set/get methods
		public long getId() {
			return id;
		}
		public void setId(long id) {
			this.id = id;
		}
		
		
		public long getServerId() {
			return serverId;
		}
		public void setServerId(long serverId) {
			this.serverId = serverId;
		}
		
		
		public String getCategory() {
			return category;
		}
		public void setCategory(String category) {
			this.category = category;
		}

		
		public String getBugType() {
			return bugType;
		}
		public void setBugType(String bugType) {
			this.bugType = bugType;
		}
		
		
		public String getName() {
			return name;
		}
		public void setName(String name) {
			this.name = name;
		}

		
		public String getInfo() {
			return info;
		}
		public void setInfo(String info) {
			this.info = info;
		}
		
		
		public String getTime() {
			return time;
		}
		public void setTime(String time) {
			this.time = time;
		}
		
		
		public String getUUID() {
			return uuid;
		}
		public void setUUID(String uuid) {
			this.uuid = uuid;
		}
		
		
		public ContentValues getSysInfo() {
			return sysInfo;
		}
		public void setSysInfo(ContentValues sysInfo) {
			this.sysInfo = sysInfo;
		}

		
		public boolean hasFilePath(){
			return !TextUtils.isEmpty(filePath);
		}
		public String getFilePath(){
			//The filePath here is not the filePath that passed in by intent.
			//It's the zip file path of all the logs. (filePath = zippedFileName)
			return filePath;
		}
		public void setFilePath(String filePath) {
			this.filePath = filePath;
		}
		
		public boolean isError() {
			return category.equals(Collector.CATEGORY_ERROR);
		}
	}
	
	/**
	 * Define the bug map for DropBox bug info.
	 * Map<String extraTag, Map<String bugType, String description> >
	 * 
	 * @author b598
	 *
	 */
	public static class DropBoxInfoMap {

		private Map<String, Map<String,String>> map;

		public DropBoxInfoMap() {
			super();
			map = new HashMap<String,Map<String,String>>();
		}
		
		/**
		 * Add (key, (key, value)) pair to the map.
		 * @param extraTag      extra tag from dropbox intent
		 * @param bugType       bug type
		 * @param description   description info
		 */
		public void add(String extraTag, String bugType, String description) {
			log(tag,"init bug map...");
			//Get the bugInfoMap
			Map<String,String> infoMap = map.get(extraTag);

			//If infoMap doesn't exist, new a HashMap, and add an entry (K extraTag, V bugInfoMap).
			if (infoMap == null) {
				infoMap = new HashMap<String,String>();
				map.put(extraTag, infoMap);
			}

			//Add an entry (K bugType, V description)
			infoMap.put(bugType, description);
		}

		/**
		 * Get bugType according to extraTag
		 * @param extraTag
		 * @return bugType
		 */
		public String getBugType(String extraTag) {

			//Get the bugInfoMap
			Map<String,String> infoMap = map.get(extraTag);
			if (infoMap == null) {
				log(tag, "bug info map is null! Why???????");
				return null;
			}

			//Get bug type
			Set<Map.Entry<String,String>> set = infoMap.entrySet();
			Iterator<Map.Entry<String,String>> list = set.iterator();
			Map.Entry<String,String> entry = (Map.Entry<String,String>)list.next();
			
			return entry.getKey();
		}
		
		/**
		 * Get description info according to extraTag and bugType
		 * @param extraTag
		 * @param bugType
		 * @return description
		 */
		public String getDescription(String extraTag, String bugType) {

			//Get the bugInfoMap
			Map<String,String> infoMap = map.get(extraTag);
			if (infoMap == null) {
				log(tag, "bug info map is also null! Why???????");
				return null;
			}
			
			return infoMap.get(bugType);
		}
	}
	
	
	/**
	 * 
	 * JSON keys definitions 
	 *
	 */
	public static class JSON {
		//report data info keys
		public static final String CATEGORY  = "category";
		public static final String BUG_INFO  = "bug_info";
		public static final String BUG_TYPE  = "bug_type";
		public static final String NAME      = "name";
		public static final String INFO      = "info";
		public static final String TIME      = "time";
		public static final String SYS_INFO  = "sys_info";
		public static final String UUID      = "uuid";	
		public static final String Server_ID = "id";
		
		//bugreporter version keys
		public static final String SELF_VERSION_NAME = "bugreporter.version.name";
		public static final String SELF_VERSION_CODE = "bugreporter.version.code";
		
		//lihui new system info keys
		//device info
		public static final String PHONE_NUMBER         = "phoneNumber";
		public static final String IMEI_NUMBER          = "imei_number";//IMEI_NUMBER
		public static final String WIFI_MAC             = "wifi_mac_address";
		
		//build info
		public static final String KERNEL_VERSION       = "sys.kernel.version";
		public static final String PLATFORM_WARE        = "ro.build.revision";
		public static final String CUSTOM_BUILD_VERSION = "ro.custom.build.version";//lihui new added
		//build info - standard definition in sdk doc
		public static final String BOARD                = "android.os.Build.BOARD";
		public static final String BOOTLOADER           = "android.os.Build.BOOTLOADER";
		public static final String BRAND                = "android.os.Build.BRAND";
		public static final String CPU_ABI              = "android.os.Build.CPU_ABI";
		public static final String CPU_ABI2             = "android.os.Build.CPU_ABI2";
		public static final String DEVICE               = "android.os.Build.DEVICE";
		public static final String DISPLAY              = "android.os.Build.DISPLAY";//releaseStr
		public static final String FINGERPRINT          = "android.os.Build.FINGERPRINT";
		public static final String HARDWARE             = "android.os.Build.HARDWARE";
		public static final String HOST                 = "android.os.Build.HOST";
		public static final String ID                   = "android.os.Build.ID";
		public static final String MANUFACTURER         = "android.os.Build.MANUFACTURER";
		public static final String MODEL                = "android.os.Build.MODEL";
		public static final String PRODUCT              = "android.os.Build.PRODUCT";
		public static final String RADIO                = "android.os.Build.RADIO";//Build.getRadioVersion()
		public static final String SERIAL               = "android.os.Build.SERIAL";
		public static final String TAGS                 = "android.os.Build.TAGS";
		public static final String BUILD_TIME           = "android.os.Build.TIME";
		public static final String TYPE                 = "android.os.Build.TYPE";
		public static final String USER                 = "android.os.Build.USER";
		public static final String VERSION_CODENAME     = "android.os.Build.VERSION.CODENAME";
		public static final String VERSION_INCREMENTAL  = "android.os.Build.VERSION.INCREMENTAL";
		public static final String VERSION_RELEASE      = "android.os.Build.VERSION.RELEASE";
		public static final String VERSION_SDK          = "android.os.Build.VERSION.SDK";
	}
	

	/**
	 * Collect system info.
	 */
	public static class SysInfo {
		
		public static final String SYSTEM_INFO = "SYSTEM_INFO";
		
		public static ContentValues getSysInfo(Context context) {
			if(DBG) Util.log(tag,"getSysInfo(Context)");
			
			//Get phone number and device ID
			String phoneNumber = null;
			String deviceId = null;
			TelephonyManager tm = (TelephonyManager) context
					.getSystemService(Context.TELEPHONY_SERVICE);
			if (tm != null) {
				phoneNumber = tm.getLine1Number();
				if (phoneNumber == null || phoneNumber.equals("")) {
					phoneNumber = tm.getSubscriberId();
					if (phoneNumber != null && !phoneNumber.equals("")) {
						phoneNumber = "IMSI:" + phoneNumber;
					} else {
						phoneNumber = "Unknown";
					}
				}
				deviceId = tm.getDeviceId();
				if (deviceId == null || deviceId.equals("")) {
					deviceId = "Unknown";
				}
			} else {
				phoneNumber = "Unknown";
				deviceId = "Unknown";
			}
			
			//Get wifi mac address
			String wifiMacAddress = getWiFiMac(context);
			
			//Get other basic system info from getprop() 			
			String kernelVersionStr = getProp(JSON.KERNEL_VERSION, getFormattedKernelVersion());
			if (kernelVersionStr == null || "".equals(kernelVersionStr)) {
				kernelVersionStr = "Unknown";
			}
			String platFormwareStr = getProp(JSON.PLATFORM_WARE, "Unknown");
			String customBuildVersion = getProp(JSON.CUSTOM_BUILD_VERSION,"Unknown");
						
			//Get all the build info
			String board = (TextUtils.isEmpty(Build.BOARD)) ? "Unknown" : Build.BOARD;
			String bootLoader = (TextUtils.isEmpty(Build.BOOTLOADER)) ? "Unknown" : Build.BOOTLOADER;
			String brand = (TextUtils.isEmpty(Build.BRAND)) ? "Unknown" : Build.BRAND;
			String cpuAbi = (TextUtils.isEmpty(Build.CPU_ABI)) ? "Unknown" : Build.CPU_ABI;
			String cpuAbi2 = (TextUtils.isEmpty(Build.CPU_ABI2)) ? "Unknown" : Build.CPU_ABI2;
			String device = (TextUtils.isEmpty(Build.DEVICE)) ? "Unknown" : Build.DEVICE;
			String displayStr = (TextUtils.isEmpty(Build.DISPLAY)) ? "Unknown" : Build.DISPLAY;
			String fingerprint = (TextUtils.isEmpty(Build.FINGERPRINT)) ? "Unknown" : Build.FINGERPRINT;
			String hardware = (TextUtils.isEmpty(Build.HARDWARE)) ? "Unknown" : Build.HARDWARE;
			String host = (TextUtils.isEmpty(Build.HOST)) ? "Unknown" : Build.HOST;
			String id = (TextUtils.isEmpty(Build.ID)) ? "Unknown" : Build.ID;
			String manufacture = (TextUtils.isEmpty(Build.MANUFACTURER)) ? "Unknown" : Build.MANUFACTURER;
			String modelStr = (TextUtils.isEmpty(Build.MODEL)) ? "Unknown" : Build.MODEL;
			String product = (TextUtils.isEmpty(Build.PRODUCT)) ? "Unknown" : Build.PRODUCT;
			String radio = (TextUtils.isEmpty(Build.getRadioVersion())) ? "Unknown" : Build.getRadioVersion();
			String serial = (TextUtils.isEmpty(Build.SERIAL)) ? "Unknown" : Build.SERIAL;
			String tags = (TextUtils.isEmpty(Build.TAGS)) ? "Unknown" : Build.TAGS;
			String time = (TextUtils.isEmpty("" + Build.TIME)) ? "Unknown" : ("" + Build.TIME);
			String mtype = (TextUtils.isEmpty(Build.TYPE)) ? "Unknown" : Build.TYPE;
			String user = (TextUtils.isEmpty(Build.USER)) ? "Unknown" : Build.USER;
			String versionCodeName = (TextUtils.isEmpty(Build.VERSION.CODENAME)) ? "Unknown" : Build.VERSION.CODENAME;
			String incremental = (TextUtils.isEmpty(Build.VERSION.INCREMENTAL)) ? "Unknown" : Build.VERSION.INCREMENTAL;
			String versionRelease = (TextUtils.isEmpty(Build.VERSION.RELEASE)) ? "Unknown" : Build.VERSION.RELEASE;
			String versionSdk = (TextUtils.isEmpty("" + Build.VERSION.SDK_INT)) ? "Unknown" : ("" + Build.VERSION.SDK_INT);
			
			
			//put these system info to a ContentValues object
			ContentValues sysInfo = new ContentValues();
			
			sysInfo.put(Util.JSON.PHONE_NUMBER, phoneNumber);
			sysInfo.put(Util.JSON.IMEI_NUMBER, deviceId);
			sysInfo.put(Util.JSON.WIFI_MAC, wifiMacAddress);
			sysInfo.put(Util.JSON.KERNEL_VERSION, kernelVersionStr);
			sysInfo.put(Util.JSON.PLATFORM_WARE, platFormwareStr);
			sysInfo.put(Util.JSON.CUSTOM_BUILD_VERSION, customBuildVersion);
			
			sysInfo.put(Util.JSON.BOARD, board);
			sysInfo.put(Util.JSON.BOOTLOADER, bootLoader);
			sysInfo.put(Util.JSON.BRAND, brand);
			sysInfo.put(Util.JSON.CPU_ABI, cpuAbi);
			sysInfo.put(Util.JSON.CPU_ABI2, cpuAbi2);
			sysInfo.put(Util.JSON.DEVICE, device);
			sysInfo.put(Util.JSON.DISPLAY, displayStr);
			sysInfo.put(Util.JSON.FINGERPRINT, fingerprint);
			sysInfo.put(Util.JSON.HARDWARE, hardware);
			sysInfo.put(Util.JSON.HOST, host);
			sysInfo.put(Util.JSON.ID, id);
			sysInfo.put(Util.JSON.MANUFACTURER, manufacture);
			sysInfo.put(Util.JSON.MODEL, modelStr);
			sysInfo.put(Util.JSON.PRODUCT, product);
			sysInfo.put(Util.JSON.RADIO, radio);
			sysInfo.put(Util.JSON.SERIAL, serial);
			sysInfo.put(Util.JSON.TAGS, tags);
			sysInfo.put(Util.JSON.BUILD_TIME, time);
			sysInfo.put(Util.JSON.TYPE, mtype);
			sysInfo.put(Util.JSON.USER, user);
			sysInfo.put(Util.JSON.VERSION_CODENAME, versionCodeName);
			sysInfo.put(Util.JSON.VERSION_INCREMENTAL, incremental);
			sysInfo.put(Util.JSON.VERSION_RELEASE, versionRelease);
			sysInfo.put(Util.JSON.VERSION_SDK, versionSdk);
			
			sysInfo.put(Util.JSON.SELF_VERSION_NAME, getSelfVersionName(context));
			sysInfo.put(Util.JSON.SELF_VERSION_CODE, getSelfVersionCode(context));

			return sysInfo;
		}
		
		/**
		 * Get trace file path.
		 * @return
		 */
		public static String getTraceFilePath(){
			String propKey = "dalvik.vm.stack-trace-file";
			return getProp(propKey, null).trim();
		}
		
		/**
		 * Get line separator.
		 * @return
		 */
		public static String getLineSeparator(){
			String separator = System.getProperty("line.separator");
			if(TextUtils.isEmpty(separator)){
				separator = "\r\n";
			}
			return separator;
		}
		
		/**
		 * Get the state of network.
		 * @param context
		 * @return
		 */
		public static boolean isNetworkAvailable(Context context) {
			if(DBG) log(tag, "isNetworkAvailable()");
			ConnectivityManager connManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
			if(connManager == null){
				return false;
			}
			NetworkInfo netInfo = connManager.getActiveNetworkInfo();
			Settings settings = new Settings(context);

			if (netInfo == null) {
				return false;
			}		
			
			if(netInfo.isConnected()){
				int type = netInfo.getType();
				if(DBG) log("Type:" + type);
				switch (type) {
				case ConnectivityManager.TYPE_WIFI: {
					if(DBG) log("Type:WiFi");
					return true;
				}
				case ConnectivityManager.TYPE_MOBILE: {
					/*
					 * Check settings, whether GPRS can be used check local
					 * database,send data if necessary.
					 */
					if(DBG) log("Type:MOBILE");
					if (settings.isViaWifiOnly()) {
						if(DBG) log("WiFiOnly:true");
						return false;
					}else{
						if(DBG) log("WiFiOnly:false");
						return true;
					}
				}
				default: {
					return false;
				}
				}
			}else{
				if (DBG) Util.log(tag, "Network is not connected!");
			}
			return false;
		}
		
		/**
		 * Get the state of data roaming.
		 * @param context
		 * @return
		 */
		public static boolean isRoaming(Context context){
			ConnectivityManager connManager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
			NetworkInfo netInfo = connManager.getActiveNetworkInfo();			

			if (netInfo == null) {
				return false;
			}		
			return netInfo.isRoaming();
		}

		/**
		 * Get the default bugReporter server address.
		 * @return
		 */
		public static String getDefaultBugreporterServer(){
			String propKey = Settings.PROP_BUGREPORTER_SERVER;
			String server = getProp(propKey,null);
			if(TextUtils.isEmpty(server)){
				return null;
			}else{
				return server.trim();
			}
		}
		
		/**
		 * Get system property
		 * @param key
		 * @param defaultValue
		 * @return
		 */
		private static String getProp(String key, String defaultValue) {
			Process process = null;
			BufferedReader br = null;

			if (null == key || "".equals(key)) {
				return defaultValue;
			}

			try {
				process = Runtime.getRuntime().exec("getprop " + key.trim());
				br = new BufferedReader(new InputStreamReader(
						process.getInputStream()));

				String value = br.readLine();
				if(value != null){
					if(value.trim() != null){
						if ("".equals(value)) {
							value = null;
						}
					}else{
						value = null;
					}
				}
				return (value == null ? defaultValue : value);
			} catch (IOException e) {
				// if(DBG) log("Execute getprop failed: " + e);
				return null;
			} finally {
				try {
					br.close();
				} catch (IOException ioe) {
				}
				br = null;
				try {
					if (process != null)
						process.destroy();
				} catch (Exception e) {
				}
				process = null;
			}

		}

		/**
		 * Get the version name of BugReporter.
		 * @param context
		 * @return
		 */
		public static String getSelfVersionName(Context context) {
			try {
				return context.getPackageManager()
						.getPackageInfo(context.getPackageName(),
								PackageManager.GET_ACTIVITIES).versionName;
			} catch (Exception e) {
				return "Unknown";
			}
		}

		/**
		 * Get the version code of BugReporter.
		 * @param context
		 * @return
		 */
		public static String getSelfVersionCode(Context context) {
			try {
				return context.getPackageManager()
						.getPackageInfo(context.getPackageName(),
								PackageManager.GET_ACTIVITIES).versionCode
						+ "";
			} catch (Exception e) {
				return "Unknown";
			}
		}

		/**
		 * Get kernel version.
		 * @return
		 */
		private static String getFormattedKernelVersion() {
			String procVersionStr;

			try {
				BufferedReader reader = new BufferedReader(new FileReader(
						"/proc/version"), 256);
				try {
					procVersionStr = reader.readLine();
				} finally {
					reader.close();
				}

				final String PROC_VERSION_REGEX = "\\w+\\s+" + /* ignore: Linux */
				"\\w+\\s+" + /* ignore: version */
				"([^\\s]+)\\s+" + /* group 1: 2.6.22-omap1 */
				"\\(([^\\s@]+(?:@[^\\s.]+)?)[^)]*\\)\\s+" + /*
															 * group 2:
															 * (xxxxxx@xxxxx
															 * .constant)
															 */
				"\\((?:[^(]*\\([^)]*\\))?[^)]*\\)\\s+" + /* ignore: (gcc ..) */
				"([^\\s]+)\\s+" + /* group 3: #26 */
				"(?:PREEMPT\\s+)?" + /* ignore: PREEMPT (optional) */
				"(.+)"; /* group 4: date */

				Pattern p = Pattern.compile(PROC_VERSION_REGEX);
				Matcher m = p.matcher(procVersionStr);

				if (!m.matches()) {
					// Log.e(TAG, "Regex did not match on /proc/version: " +
					// procVersionStr);
					return "Unavailable";
				} else if (m.groupCount() < 4) {
					// Log.e(TAG,"Regex match on /proc/version only returned "+
					// m.groupCount() + " groups");
					return "Unavailable";
				} else {
					// we change 2"\n" into " "
					return (new StringBuilder(m.group(1)).append(" ")
							.append(m.group(2)).append(" ").append(m.group(3))
							.append(" ").append(m.group(4))).toString();
				}
			} catch (IOException e) {
				// Log.e(TAG,"IO Exception when getting kernel version for Device Info screen",e);
				return "Unavailable";
			}
		}
		
		/**
		 * Get the wifi mac address.
		 * @param context
		 * @return
		 */
		public static String getWiFiMac(Context context) { 

	        WifiManager wifi = (WifiManager)context.getSystemService(Context.WIFI_SERVICE);
	        if(wifi == null){
	        	return null;
	        }

	        WifiInfo info = wifi.getConnectionInfo();
	        if(info == null){
	        	return null;
	        }
	        
	        String mac = info.getMacAddress();
	        
	        if (TextUtils.isEmpty(mac)){
	        	return "Unknown";
	        }else{
	        	return mac;
	        }
	   }
		
		
		//This value and it's set method only useful for testing.
		private static boolean _userBuild = true;
		public static void setUserBuildForTest(boolean userBuild){
			_userBuild = userBuild;
		}
		/**
		 * Check if it's user build.(buildVariant.equals("user") || buildVariant.equals("userdebug"))
		 * @return
		 */
		public static boolean isUserBuild() {
			String buildVariant = android.os.Build.TYPE;
			if (buildVariant.equals("user")) {
				return true;
			} else {
				return false;
			}
		}
		
	}
	
	
	
	public static final String NOTIFY_MESSAGE = "notify_message";
	/**
	 * Notify user.
	 * @param context
	 * @param msg
	 * @param action
	 * @param sound
	 * @param vibrate
	 */
	public static void notify(Context context, String message, String action,
			boolean sound, boolean vibrate) {
		//New a notification manager
		NotificationManager notifyManager = (NotificationManager) context
				.getSystemService(Context.NOTIFICATION_SERVICE);
		
		//New a PendingIntent
		Intent intent = new Intent(action);
		intent.putExtra(NOTIFY_MESSAGE, message);
		PendingIntent contentIntent = PendingIntent.getActivity(context, 1,
				intent, Intent.FLAG_ACTIVITY_NEW_TASK);
		
		//Set which notification properties will be inherited from system defaults.
		int defaults = 0x0;
		if(sound){
			defaults|=Notification.DEFAULT_SOUND;
		}
		if(vibrate){
			defaults|=Notification.DEFAULT_VIBRATE;
		}
		
		//New a notification
		Notification notification = new Notification.Builder(context)
		.setAutoCancel(true) //Auto dismiss the notification if the user touches the clear button.
		.setDefaults(defaults)
		.setSmallIcon(R.drawable.ic_launcher)//represent the notification in the status bar.
		.setContentTitle("BugReporter")
		.setContentText(message)
		.setTicker(message) //text displayed in the status bar when the notification first arrives.
		.setWhen(System.currentTimeMillis())
		.setContentIntent(contentIntent) //a PendingIntent to be sent when the notification is clicked.
		.build();
		
		//Set notify
		notifyManager.notify(R.string.app_name, notification);
	}
	
	
	/**
	 * Manage the logs.
	 */
	public static class DataFile {
		
		/**
		 * Get online logcat log.
		 * @param savePath
		 */
		public static void getOnlineLogcatLog(String savePath) {
			Util.log(TAG, "==getOnlineLogcatLog");
			getOnlineLog(null, savePath);
		}
		
		/**
		 * Get online radio log.
		 * @param savePath
		 */
		public static void getRadioLog(String savePath) {
			Util.log(TAG, "==getRadioLog");
			ArrayList<String> args = new ArrayList<String>();
			args.add("-b");
			args.add("radio");
			getOnlineLog(args, savePath);
		}
		
		/*
		 * Get online log.
		 */
		private static void getOnlineLog(ArrayList<String> args, String savePath) {
			Process process = null;
			BufferedReader br = null;
			BufferedWriter bw = null;
			
			//Get all args
			ArrayList<String> cmdline = new ArrayList<String>();
			cmdline.add("logcat");
			cmdline.add("-d");
			cmdline.add("-v");
			cmdline.add("time");
			if ((args != null) && (args.size() > 0)) {
				cmdline.addAll(args);
			}
			
			//execute the command in a process
			try {
				process = Runtime.getRuntime().exec(cmdline.toArray(new String[0]));
				br = new BufferedReader(new InputStreamReader(process.getInputStream()));
				bw = new BufferedWriter(new FileWriter(savePath));
				
				String line = null;
				String separator = SysInfo.getLineSeparator();
				
				while ((line = br.readLine()) != null) {
					bw.write(line);
					bw.write(separator);
				}
				
			}catch (Exception e) {
				e.printStackTrace();
			}finally {
				if (bw != null) {
					try {
						bw.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
					bw = null;
				}
				
				if (br != null) {
					try {
						br.close();
					} catch (Exception e) {
					}
					br = null;
				}
				
				if (process != null) {
					try {
						process.destroy();
					} catch (Exception e) {
					}
					process = null;
				}
			}
		}
		
		
		/**
		 * Copy data from source file to destination file.
		 * @param source
		 * @param destDir
		 * @return
		 * @throws Exception
		 */
		public static String copy(String source, String destDir) throws Exception{
			//Create the source file, and make sure it exists
			File srcFile = new File(source);
			if (!srcFile.exists()) {
				throw new Exception("Source file doesn't exist!");
			}
			
			//Create destination file
			File destFolder = new File(destDir);
			if (!destFolder.isDirectory()){
				throw new Exception("Destination is not a folder!");
			}
			if(!destDir.endsWith(File.separator)) {
				destDir += File.separator;
			}
			File destFile = new File(destDir + srcFile.getName());
			
			//copy data from source file to destination file
			BufferedInputStream bis = null;
			BufferedOutputStream bos = null;
			try{
				bis = new BufferedInputStream(new FileInputStream(srcFile));
				bos = new BufferedOutputStream(new FileOutputStream(destFile));
				//copy
				IOUtils.copy(bis, bos);
				
				return destFile.getPath();
				
			}catch (Exception e) {
				e.printStackTrace();
			}finally {
				if (bis != null) {
					try{
						bis.close();
					}catch (Exception e){
						e.printStackTrace();
					}
					bis = null;
				}
				
				if (bos != null) {
					try{
						bos.close();
					}catch (Exception e) {
						e.printStackTrace();
					}
					bos = null;
				}
				
				srcFile = null;
				destFile = null;
			}
			
			return null;
		}
		
		
		/**
		 * Move data from source file to destination file.
		 * @param source
		 * @param destDir
		 * @return
		 * @throws Exception
		 */
		public static String move(String source, String destDir) throws Exception{
			Util.log(TAG, "==move1 ");
			//Create the source file, and make sure it exists
			File srcFile = new File(source);
			if (!srcFile.exists()) {
				throw new Exception("Source file doesn't exist!");
			}
			
			//Create destination file
			File destFolder = new File(destDir);
			if (!destFolder.isDirectory()){
				throw new Exception("Destination is not a folder!");
			}
			if(!destDir.endsWith(File.separator)) {
				destDir += File.separator;
			}
			File destFile = new File(destDir + srcFile.getName());
			
			//move data from source file to destination file
			BufferedInputStream bis = null;
			BufferedOutputStream bos = null;
			try{
				bis = new BufferedInputStream(new FileInputStream(srcFile));
				bos = new BufferedOutputStream(new FileOutputStream(destFile));
				//copy
				Util.log(TAG, "==move2 ");
				IOUtils.copy(bis, bos);
				//delete
				Util.log(TAG, "==delete source file|" + srcFile.getAbsolutePath());
				boolean flag = srcFile.delete();
				Util.log(TAG, "==delete source file|" + flag);
				
				
				Util.log(TAG, "destFile|" + destFile.getAbsolutePath());
				return destFile.getPath();
				
			}catch (Exception e) {
				e.printStackTrace();
			}finally {
				if (bis != null) {
					try{
						bis.close();
					}catch (Exception e){
						e.printStackTrace();
					}
					bis = null;
				}
				
				if (bos != null) {
					try{
						bos.close();
					}catch (Exception e) {
						e.printStackTrace();
					}
					bos = null;
				}
				
				srcFile = null;
				destFile = null;
			}
			
			return null;
		}
		
		/**
		 * Zip a file or folder. If the src is folder, zip the files in the
		 * folder, not including sub-folder and the content in the sub-folder.
		 * 
		 * @param src can be a single file, a single directory, or multiple files separated by ":".  
		 * @param destFileName
		 * @return true/false
		 */
		public static boolean zip(String src, String destFileName) {
			BufferedInputStream bis = null;
			ZipArchiveOutputStream zos = null;
			
			//Get source list
			String[] sourceList = null;			
			if(src.contains(";")){				
				sourceList = src.split(";");
			}else {
				sourceList = new String[1];
				sourceList[0] = src;
			}
			
			//get zip output stream
			try{
				zos = new ZipArchiveOutputStream(new BufferedOutputStream(new FileOutputStream(destFileName)));
			}catch(IOException ioe){
				ioe.printStackTrace();
			}
			
			//zip
			for (int i = 0; i < sourceList.length; i++) {
				File srcFile = new File(sourceList[i]);
				if (srcFile.exists()) {
					if (srcFile.isDirectory()) {
						File[] list = srcFile.listFiles();
						for (int j = 0 ; j < list.length; j++) {
							if (list[j].isFile()) {
								try {
									bis = new BufferedInputStream(new FileInputStream(list[j]));
									ZipArchiveEntry entry = new ZipArchiveEntry(list[j].getName());
									entry.setSize(list[j].length());
									zos.putArchiveEntry(entry);
									IOUtils.copy(bis, zos);
									zos.closeArchiveEntry();
								}catch (Exception e) {
									e.printStackTrace();
								}finally {
									if (bis != null) {
										try {
											bis.close();
										} catch (IOException e) {
											e.printStackTrace();
										}
										bis = null;
									}
								}
							}
						}
						
					}else { //srcFile is not a directory.
						try {
							bis = new BufferedInputStream(new FileInputStream(
									srcFile));							
							ZipArchiveEntry entry = new ZipArchiveEntry(srcFile.getName());
							entry.setSize(srcFile.length());
							zos.putArchiveEntry(entry);
							IOUtils.copy(bis, zos);
							zos.closeArchiveEntry();
						} catch (IOException ioe) {
							ioe.printStackTrace();
						} finally {
							if (bis != null) {
								try {
									bis.close();
								} catch (IOException e) {
									e.printStackTrace();
								}
								bis = null;
							}
						}
						
					}
					
				}else {//src file doesn't exist
					if (DBG) Util.log(tag,"File not exist!");
				}
			}
			
			
			//set zos to null
			if (zos != null) {
				try {
					zos.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				zos = null;
			}
			
			//Check if zip successfully
			File destFile = new File(destFileName);			
			if(destFile.exists()){
				if(DBG) log(tag, "target file size:" + destFile.length() + " Bytes.");
				return true;
			}else{
				return false;
			}
		}
		
		/**
		 * Unzip a file
		 * @param srcFile
		 * @param destDir
		 * @throws IOException
		 */
		public static void unzip(File srcFile, File destDir) throws IOException {
			ZipArchiveInputStream is = null;
			try {
				is = new ZipArchiveInputStream(new BufferedInputStream(
						new FileInputStream(srcFile)));
				ZipArchiveEntry entry = null;
				while ((entry = is.getNextZipEntry()) != null) {
					if (entry.isDirectory()) {
						File directory = new File(destDir, entry.getName());
						directory.mkdirs();
					} else {
						OutputStream os = null;
						try {
							os = new BufferedOutputStream(new FileOutputStream(
									new File(destDir, entry.getName())));
							IOUtils.copy(is, os);
						} finally {
							try {
								os.close();
							} catch (Exception e) {
							}
							os = null;
						}
					}
				}
			} finally {
				try {
					is.close();
				} catch (Exception e) {
				}
				is = null;
			}
		}
		
		
		/**
		 * Delete file or folder.
		 * @param target target to delete.
		 * @return true if the target isn't exist now. 
		 */
		public static boolean delete(String target) {
			File srcFile = new File(target);
			if(srcFile.exists()){
				if(srcFile.isDirectory()){
					File[] list = srcFile.listFiles();
					for(int i = 0; i < list.length; i++){
						list[i].delete();
					}
					return srcFile.delete();					
				}else{
					return srcFile.delete();					
				}
			}else{
				return true;
			}
		}
		
		
	}

}
