package com.borqs.bugreporter.provider;

import android.net.Uri;


/**
 * 
 * This class defines the database of BugReporter.
 *
 */
public class BugReport {
	 
	//This class cannot be instantiated
	private BugReport() {}
	public static final String AUTHORITY = "com.borqs.bugreporter.provider.BugReport";
	
	
	//Define the tables
	/*Table for report data*/
	public static final String TABLE_REPORT_DATA = "report_data";
	/*Table for system info*/
	public static final String TABLE_SYS_INFO = "sys_info";
	/*Table for settings*/
	public static final String TABLE_SETTINGS = "settings";
	/*Table for type control list*/
	public static final String TABLE_TYPE_CONTROL = "type_control";
	/*Table for repeated issue*/
	public static final String TABLE_REPEATED_ISSUE = "repeated_issue";
	
	
	//column_keys of TABLE_REPORT_DATA
	public static final String COL_ID = "_id";
	public static final String COL_CATEGORY = "category";
	public static final String COL_TYPE = "type";
	public static final String COL_NAME = "name";
	public static final String COL_INFO = "info";
	public static final String COL_FILE_PATH = "file_path";
	public static final String COL_TIME = "time";
	public static final String COL_UUID = "uuid";
	public static final String COL_SERVER_ID = "server_id";
	public static final String COL_MODIFIED = "modified";
	
	
	//TABLE_SETTINGS column_keys
	public static final String COL_BUG_REPORTER = "bug_reporter";
	public static final String COL_SERVER_ADDRESS = "server_address";
	public static final String COL_WIFI_ONLY = "wifi_only";
	public static final String COL_UPLOAD_LOG = "upload_log";
	public static final String COL_USER_NOTIFY = "user_notify";
	public static final String COL_FIRST_BOOT = "first_boot";
//	public static final String COL_LEGAL_AGREE = "legal_agree";
//	public static final String COL_ROAMING_NOTIFY = "roaming_notify";

	//TABLE_SYS_INFO
	public static final String COL_KEY = "key";
	public static final String COL_VALUE = "value";
	
	//TABLE_TYPE_CONTROL
	public static final String COL_STATE = "state";
	
	//TABLE_REPEATED_ISSUE
	public static final String COL_LOG = "log";
	public static final String COL_SEND = "send";
	
	//Define an TYPE_UNKNOWN for type control
	public static final String TYPE_UNKNOWN = "UNKNOWN_TYPE";
	
	
	//Define the projection
	public static final String[] reportDataProjection = {COL_ID,COL_CATEGORY,COL_TYPE,COL_NAME,COL_INFO,COL_FILE_PATH,COL_TIME,COL_UUID,COL_SERVER_ID};
	public static final String[] sysInfoProjection = {COL_ID,COL_KEY,COL_VALUE};
	
	
	/**
     * The content:// style URL for this database.
     */
    public static final Uri CONTENT_URI_REPORT_DATA = Uri.parse("content://" + AUTHORITY + "/"+TABLE_REPORT_DATA);
    
    public static final Uri CONTENT_URI_SYS_INFO = Uri.parse("content://" + AUTHORITY + "/"+TABLE_SYS_INFO);
    
    public static final Uri CONTENT_URI_SETTINGS = Uri.parse("content://" + AUTHORITY + "/"+TABLE_SETTINGS);
    
    public static final Uri CONTENT_URI_TYPE_CONTROL = Uri.parse("content://" + AUTHORITY + "/"+TABLE_TYPE_CONTROL);
    
    public static final Uri CONTENT_URI_REPEATED_ISSUE = Uri.parse("content://" + AUTHORITY + "/"+TABLE_REPEATED_ISSUE);

    public static final String CONTENT_TYPE = "vnd.android.cursor.dir/vnd.borqs.bug";
	
    
    /**
     * The default sort order for this table
     */
    public static final String DEFAULT_SORT_ORDER = "modified DESC";    
    
}
