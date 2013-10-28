package com.borqs.bugreporter.collector;

import java.util.HashMap;
import java.util.Map;
import com.borqs.bugreporter.util.Util;
import android.content.Context;
import android.text.TextUtils;

/**
 * Collect bug info for kernel panic issue.
 * (It needs kernel to support)
 */
public class KernelPanicCollector implements Collector {

	private static final String TAG = "KernelPanicCollector";
	
	public static final String BUG_TYPE = "KERNEL_PANIC";
	
	/**
	 * Get extras for kernel panic issue.
	 */
	@Override
	public Map<String,String> getBugInfo(Context context, String tag, long time) {
		Util.log(TAG,"Enter KernelPanicCollector...");
		
		// TODO Auto-generated method stub
		
		
		
		
		
		
		Map<String,String> map=new HashMap<String,String>();
		map.put(Util.ExtraKeys.CATEGORY, Collector.CATEGORY_ERROR);
		map.put(Util.ExtraKeys.BUG_TYPE, BUG_TYPE);
		//add more extras...
		
		
		//Check if the map info is valid
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
		String extraKey[] = {Util.ExtraKeys.BUG_TYPE, Util.ExtraKeys.CATEGORY};
		
		//Check if the extra exists and valid
		for (int i = 0; i < extraKey.length; i++) {
			if (map.containsKey(extraKey[i])){
				String extraValue = map.get(extraKey[i]);
				if (TextUtils.isEmpty(extraValue)) {
					Util.log(TAG, "The value of extra: " + extraKey[i] + " is empty! So map is not valid!...");
					return null;
				}
				Util.log(TAG, "Find--" + extraKey[i] + "|" + extraValue);
			}else {
				Util.log(TAG, "No extra: " + extraKey[i] + ". So map is not valid!...");
				return null;
			}
		}
		return map;
	}

}
