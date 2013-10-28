package com.borqs.bugreporter.collector;

import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.util.Util.DropBoxInfoMap;
import android.content.Context;
import android.os.DropBoxManager;
import android.text.TextUtils;


/**
 * 
 * Collect bug info for supported&interested issues from DropBox.
 *
 */
public class DropBoxCollector implements Collector {
	
	private static final String TAG = "DropBoxCollector";
	
	//Define the interested DropBox tags
	public static final String[] INTERESTED_TAGS = {"system_app_anr",
		                                            "system_app_crash",
		                                            "SYSTEM_TOMBSTONE",
		                                            "system_app_wtf",
		                                            "system_app_strictmode",
		                                            "SYSTEM_RESTART"
//		                                            "SYSTEM_LAST_KMSG"
		                                            };
	
	//Define a map for DropBox (includes the bugType and description)
	public static DropBoxInfoMap BM;
	static {
		BM = new DropBoxInfoMap();
		//Add (extraTag, bugType, description) value pair to the DropBoxInfoMap
		BM.add("system_app_anr",        "ANR",                   "Application is Not Responding!");
		BM.add("system_app_crash",      "FORCE_CLOSE",           "Application has stopped unexpectedly!");
		BM.add("SYSTEM_TOMBSTONE",      "CORE_DUMP",             "Core Dumped!");
		BM.add("system_app_wtf",        "SYSTEM_APP_WTF",        "What a Terrible Failure!");
		BM.add("system_app_strictmode", "SYSTEM_APP_STRICTMODE", "StrictMode Violation!");
		BM.add("SYSTEM_RESTART",        "SYSTEM_SERVER_CRASH",   "System server crashed!");
//		BM.add("SYSTEM_LAST_KMSG",      "KERNEL_PANIC",          "Kernel panic happened!");
	}
	
	/**
	 * Get extras for dropbox issues.
	 */
	@Override
	public Map<String,String> getBugInfo(Context context, String tag, long time) {
		Util.log(TAG,"Enter DropBoxCollector...");
		Map<String,String> map = new HashMap<String,String>();
		
		//Get the process name in dropbox entry
		DropBoxManager dbm = (DropBoxManager) context.getSystemService(Context.DROPBOX_SERVICE);
		DropBoxManager.Entry entry = dbm.getNextEntry(tag, time-1);
		if(entry == null){
			if(Util.DBG) Util.log(TAG, "Entry is Null!");
			map = null;
			return map;
		}
		
		//public String getText (int maxBytes)
		//Parameters maxBytes 	of string to return (will truncate at this length).
		//Returns the uncompressed text contents of the entry, null if the entry is not text.
		String fileContent = entry.getText(100*1024); //100K
		String name = null;
//		Util.log(TAG, "Entry entry.getText:\n" + fileContent);
		int start = fileContent.indexOf("Process:");
		if (start == -1) {
			name  = "Unknown";
		}else {
			start += 9;
			int end = fileContent.indexOf("\n", start);
			name = fileContent.substring(start, end);
			Util.log(TAG, "process name: " + name);
		}
		
		//Get the dropbox file
		String destFileName = tag + "@" + time + ".txt";
		DataOutputStream dos = null;
		try {
			dos = new DataOutputStream(context.openFileOutput(destFileName, Context.MODE_PRIVATE));
			dos.writeBytes(fileContent);
		} catch (Exception e) {
			e.printStackTrace();
		} finally {
			if (dos != null) {
				try {
					dos.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				dos = null;
			}
		}
		
		String filePath = context.getFilesDir().getPath() + "/" + destFileName;
		Util.log(TAG, "filePath:" + filePath);
		File destFile = new File(filePath);
		Util.log(TAG, "f.length():" + destFile.length());
		
		//get bug type according to tag
		String bugType = BM.getBugType(tag);
		String description = BM.getDescription(tag, bugType);
		
		
		//put all the (key, value) pair to the map
		map.put(Util.ExtraKeys.CATEGORY, Collector.CATEGORY_ERROR);
		map.put(Util.ExtraKeys.BUG_TYPE, bugType);
		map.put(Util.ExtraKeys.NAME, name);
		map.put(Util.ExtraKeys.DESCRIPTION, description);
		map.put(Util.ExtraKeys.FILE_PATH, filePath);
		map.put(Util.ExtraKeys.FILE_KEEP, "/data/anr/traces.txt;");
		map.put(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT, "true");
		
		//Check whether the map info is valid
		map = parser(map);
		return map;
	}
	
	/**
	 * Check if map contains the mandatory extras. We should make sure 
	 * this set of data is right and valid to be returned to ProcessorService.
	 * @param map
	 * @return map or null if the map info is not valid
	 */
	@Override
	public Map<String, String> parser(Map<String, String> map) {
		//Define mandatory extras
		String extraKey[] = {Util.ExtraKeys.BUG_TYPE, Util.ExtraKeys.NAME, 
				Util.ExtraKeys.DESCRIPTION, Util.ExtraKeys.CATEGORY};
		
		//Check if the extra exists and valid
		for (int i = 0; i < extraKey.length; i++) {
			if (map.containsKey(extraKey[i])){
				String extraValue = map.get(extraKey[i]);
				if (TextUtils.isEmpty(extraValue)) {
					if(Util.DBG) Util.log(TAG, "The value of extra: " + extraKey[i] + " is empty! So map is not valid!...");
					return null;
				}
				if(Util.DBG) Util.log(TAG, "Find--" + extraKey[i] + "|" + extraValue);
			}else {
				if(Util.DBG) Util.log(TAG, "No extra: " + extraKey[i] + ". So map is not valid!...");
				return null;
			}
		}
		return map;
	}
	
	/**
	 * Check whether the tag is interested by BugReporter.
	 * @param tag string that containing DropBox tags
	 * @return True/False
	 */
	public static boolean isInterestedTag(String tag){
		int length = DropBoxCollector.INTERESTED_TAGS.length;
		for(int i = 0; i < length; i ++){
			if(tag.equals(DropBoxCollector.INTERESTED_TAGS[i])){
				return true;
			}
		}
		return false;
	}

}
