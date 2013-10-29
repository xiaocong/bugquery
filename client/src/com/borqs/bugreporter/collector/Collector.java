package com.borqs.bugreporter.collector;

import java.util.Map;
import android.content.Context;

/**
 * A standard interface for the collectors.
 */
public interface Collector {
	
	//Define category
	public static final String CATEGORY_ERROR = "ERROR";
	
	//Define method to get bug info
	public Map<String,String> getBugInfo(Context context, String tag, long time);
	
	//Define method to check if the map info is valid
	public Map<String,String> parser(Map<String,String> map);

}
