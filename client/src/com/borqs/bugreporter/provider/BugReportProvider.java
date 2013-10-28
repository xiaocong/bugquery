package com.borqs.bugreporter.provider;

import android.content.ContentProvider;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.UriMatcher;
import android.database.Cursor;
import android.database.SQLException;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteQueryBuilder;
import android.net.Uri;
import android.os.Build;
import android.text.TextUtils;

import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.collector.KernelPanicCollector;
import com.borqs.bugreporter.collector.LiveTimeCollector;
//import com.borqs.bugreporter.collector.LiveTimeCollector;
import com.borqs.bugreporter.settings.Settings;

public class BugReportProvider extends ContentProvider {

	private static final String TAG = "BugReportProvider";	
	private static final boolean DBG = Util.DBG;
	
	private static final String DATABASE_NAME = "bug_report.db";
	private static final int DATABASE_VERSION = 3;//3. update 2013/08/08
	
	private static final int REPORT_DATA    = 1;
	private static final int REPORT_DATA_ID = 2;
	private static final int SYS_INFO       = 3;
	private static final int SETTINGS       = 4;
	private static final int TYPE_CONTROL   = 5;
	private static final int REPEATED_ISSUE = 6;

	private static final UriMatcher sUriMatcher;
	static {
		sUriMatcher = new UriMatcher(UriMatcher.NO_MATCH);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_REPORT_DATA, REPORT_DATA);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_REPORT_DATA+"/#", REPORT_DATA_ID);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_SYS_INFO, SYS_INFO);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_SETTINGS, SETTINGS);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_TYPE_CONTROL, TYPE_CONTROL);
		sUriMatcher.addURI(BugReport.AUTHORITY, BugReport.TABLE_REPEATED_ISSUE, REPEATED_ISSUE);
	}
	
	
	/**
	 * This class helps open, create, and upgrade the database file.
	 */
	private static class DatabaseHelper extends SQLiteOpenHelper {

		DatabaseHelper(Context context) {
			super(context, DATABASE_NAME, null, DATABASE_VERSION);
		}

		@Override
		public void onCreate(SQLiteDatabase db) {
			if(DBG) Util.log(TAG, "Create Database!");
			boolean isUserBuild = Util.SysInfo.isUserBuild();
			
			//Table Report Data
			db.execSQL("CREATE TABLE IF NOT EXISTS " + BugReport.TABLE_REPORT_DATA + " (" 
			+ BugReport.COL_ID + " INTEGER PRIMARY KEY,"
			+ BugReport.COL_CATEGORY + " TEXT," 
			+ BugReport.COL_TYPE + " TEXT,"
			+ BugReport.COL_NAME + " TEXT," 
			+ BugReport.COL_INFO + " TEXT," 
			+ BugReport.COL_FILE_PATH + " TEXT," 
			+ BugReport.COL_TIME + " TEXT," 
			+ BugReport.COL_UUID + " TEXT," 
			+ BugReport.COL_SERVER_ID + " INTEGER DEFAULT -1,"
			+ BugReport.COL_MODIFIED +" TIMESTAMP DEFAULT (time())"
			+ ");");
			
			
			//Table System Info
			db.execSQL("CREATE TABLE IF NOT EXISTS " + BugReport.TABLE_SYS_INFO + " (" 
					+ BugReport.COL_ID + " INTEGER,"
					+ BugReport.COL_KEY + " TEXT," 
					+ BugReport.COL_VALUE + " TEXT"
					+ ");");
			
			
			//Table Settings
			db.execSQL("CREATE TABLE IF NOT EXISTS " + BugReport.TABLE_SETTINGS + " (" 
					+ BugReport.COL_BUG_REPORTER + " INTEGER DEFAULT 1,"
					+ BugReport.COL_SERVER_ADDRESS + " TEXT," 
					+ BugReport.COL_WIFI_ONLY + " INTEGER DEFAULT 1,"
					+ BugReport.COL_UPLOAD_LOG + " INTEGER DEFAULT 1,"
					+ BugReport.COL_USER_NOTIFY + " INTEGER DEFAULT 1,"
					+ BugReport.COL_FIRST_BOOT + " INTEGER DEFAULT 1"
					+ ");");
			
			//Get server address according to the build version (eg. 4.0.3)
			//(versionValue >= 4)?  Settings.ATS_SERVER : Settings.DEFAULT_SERVER
			String serverAddress = null;
			String releaseVersion = Build.VERSION.RELEASE;
			int versionValue = 0;
			try{
				versionValue = Integer.parseInt(releaseVersion.substring(0, releaseVersion.indexOf(".")));
			}catch(Exception e){
				if (DBG) Util.log(TAG, e.toString());
			}
			if (DBG) Util.log(TAG, "Version value:" + versionValue);
			if(versionValue >= 4){
				serverAddress = Settings.ATS_SERVER;
			}else{
				serverAddress = Util.SysInfo.getDefaultBugreporterServer();
				if(serverAddress == null){
					serverAddress = Settings.DEFAULT_SERVER;
				}
			}
			if (DBG) Util.log(TAG, "Init default server:" + serverAddress);
			
			//update some values of Table_Settings
			ContentValues value = new ContentValues();
			value.put(BugReport.COL_BUG_REPORTER, isUserBuild?0:1);
			value.put(BugReport.COL_SERVER_ADDRESS, serverAddress);
			db.insert(BugReport.TABLE_SETTINGS, null, value);
			
			
			
			//Table Type Control
			db.execSQL("CREATE TABLE IF NOT EXISTS " + BugReport.TABLE_TYPE_CONTROL + " (" 
					+ BugReport.COL_TYPE + " TEXT PRIMARY KEY,"
					+ BugReport.COL_STATE + " INTEGER DEFAULT 1"
					+ ");");
			
			value=new ContentValues();
			value.put(BugReport.COL_TYPE, BugReport.TYPE_UNKNOWN);
			value.put(BugReport.COL_STATE, 1);
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "ANR");
			value.put(BugReport.COL_STATE, 1);	
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "FORCE_CLOSE");
			value.put(BugReport.COL_STATE, 1);	
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "CORE_DUMP");
			value.put(BugReport.COL_STATE, 1);	
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "SYSTEM_APP_WTF");
			value.put(BugReport.COL_STATE, 1);	
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "SYSTEM_APP_STRICTMODE");
			value.put(BugReport.COL_STATE, 0);	
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, "SYSTEM_SERVER_CRASH");
			value.put(BugReport.COL_STATE, 1);
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, LiveTimeCollector.MONITOR_TYPE);
			value.put(BugReport.COL_STATE, 1);
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			value.put(BugReport.COL_TYPE, KernelPanicCollector.BUG_TYPE);
			value.put(BugReport.COL_STATE, 1);
			db.insert(BugReport.TABLE_TYPE_CONTROL, null, value);
			
			
			//Table Repeated Issue
			db.execSQL("CREATE TABLE IF NOT EXISTS " + BugReport.TABLE_REPEATED_ISSUE + " (" 
					+ BugReport.COL_ID + " INTEGER PRIMARY KEY,"
					+ BugReport.COL_KEY + " TEXT,"
					+ BugReport.COL_TIME + " INTEGER," 
					+ BugReport.COL_LOG + " INTEGER DEFAULT 0,"
					+ BugReport.COL_SEND + " INTEGER DEFAULT 0"
					+ ");");
		}

		@Override
		public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
			Util.log(TAG, "Update Database!");
			db.execSQL("DROP TABLE IF EXISTS " + BugReport.TABLE_REPORT_DATA );
			db.execSQL("DROP TABLE IF EXISTS " + BugReport.TABLE_SYS_INFO );
			db.execSQL("DROP TABLE IF EXISTS " + BugReport.TABLE_SETTINGS );
			db.execSQL("DROP TABLE IF EXISTS " + BugReport.TABLE_TYPE_CONTROL );
			db.execSQL("DROP TABLE IF EXISTS " + BugReport.TABLE_REPEATED_ISSUE );
			onCreate(db);
		}
	}

	
	
	private DatabaseHelper mOpenHelper;

	@Override
	public boolean onCreate() {
		mOpenHelper = new DatabaseHelper(getContext());
		return true;
	}

	
	/**
	 * Query data.
	 */
	@Override
	public Cursor query(Uri uri, String[] projection, String selection,
			String[] selectionArgs, String sortOrder) {
		SQLiteQueryBuilder qb = new SQLiteQueryBuilder();
		
		//If no sort order is specified use the default
		String orderBy=null;
		
		switch (sUriMatcher.match(uri)) {
		case REPORT_DATA:
			qb.setTables(BugReport.TABLE_REPORT_DATA);
			if (TextUtils.isEmpty(sortOrder)) {
				orderBy = BugReport.DEFAULT_SORT_ORDER;
			} else {
				orderBy = sortOrder;
			}
			break;
		case SYS_INFO:
			qb.setTables(BugReport.TABLE_SYS_INFO);
			break;
		case SETTINGS:
			qb.setTables(BugReport.TABLE_SETTINGS);
			break;
		case TYPE_CONTROL:
			qb.setTables(BugReport.TABLE_TYPE_CONTROL);
			break;
		case REPEATED_ISSUE:
			qb.setTables(BugReport.TABLE_REPEATED_ISSUE);
			orderBy = sortOrder;
			break;
		default:
			throw new IllegalArgumentException("Unknown URI " + uri);
		}		

		// Get the database and run the query
		SQLiteDatabase db = mOpenHelper.getReadableDatabase();
		Cursor c = qb.query(db, projection, selection, selectionArgs, null, null, orderBy);

		//Tell the cursor which uri to watch, so it knows when its source data changes
		c.setNotificationUri(getContext().getContentResolver(), uri);
		return c;
	}	

	/**
	 * Insert data.
	 */
	@Override
	public Uri insert(Uri uri, ContentValues initialValues) {
		String table=null;
		switch (sUriMatcher.match(uri)) {
		case REPORT_DATA:
			table=BugReport.TABLE_REPORT_DATA;
			break;		
		case SYS_INFO:
			table=BugReport.TABLE_SYS_INFO;
			break;
		/*case SETTINGS: settings table no insert operation
			table=BugReport.TABLE_SETTINGS;
			break;*/
		case TYPE_CONTROL:
			table=BugReport.TABLE_TYPE_CONTROL;
			break;
		case REPEATED_ISSUE:
			table=BugReport.TABLE_REPEATED_ISSUE;
			break;
		default:
			throw new IllegalArgumentException("Unknown URI " + uri);
		}
		
		if (initialValues == null) {
			throw new IllegalArgumentException("No data to insert!");
		}		

		SQLiteDatabase db = mOpenHelper.getWritableDatabase();
		long rowId = db.insert(table, null, initialValues);
		if (rowId > 0) {
			Uri dataUri = ContentUris.withAppendedId(uri,rowId);
			getContext().getContentResolver().notifyChange(dataUri, null);
			return dataUri;
		}

		throw new SQLException("Failed to insert row into " + uri);
	}

	
	/**
	 * Delete data.
	 */
	@Override
	public int delete(Uri uri, String where, String[] whereArgs) {
		SQLiteDatabase db = mOpenHelper.getWritableDatabase();
		int count;
		
		String table=null;		
		switch (sUriMatcher.match(uri)) {
		case REPORT_DATA:
			table=BugReport.TABLE_REPORT_DATA;			
			break;		
		case SYS_INFO:
			table=BugReport.TABLE_SYS_INFO;			
			break;
		case TYPE_CONTROL:
			table=BugReport.TABLE_TYPE_CONTROL;
			break;
		case REPEATED_ISSUE:
			table=BugReport.TABLE_REPEATED_ISSUE;
			break;
		default:
			throw new IllegalArgumentException("Unknown URI " + uri);
		}
		count=db.delete(table, where, whereArgs);

		getContext().getContentResolver().notifyChange(uri, null);
		return count;
	}

	
	/**
	 * Update data.
	 */
	@Override
	public int update(Uri uri, ContentValues values, String where,String[] whereArgs) {
		SQLiteDatabase db = mOpenHelper.getWritableDatabase();
		int count;
		String table=null;		
		switch (sUriMatcher.match(uri)) {
		case REPORT_DATA:
			table=BugReport.TABLE_REPORT_DATA;			
			break;		
		case SYS_INFO:
			table=BugReport.TABLE_SYS_INFO;			
			break;
		case SETTINGS: 
			Util.log(TAG, "===lihui===update SETTINGS table");
			table=BugReport.TABLE_SETTINGS;
			break;
		case TYPE_CONTROL:
			table=BugReport.TABLE_TYPE_CONTROL;
			break;
		case REPEATED_ISSUE:
			table=BugReport.TABLE_REPEATED_ISSUE;
			break;
		default:
			throw new IllegalArgumentException("Unknown URI " + uri);
		}
		
		count = db.update(table, values, where, whereArgs);

		getContext().getContentResolver().notifyChange(uri, null);
		return count;
	}


	/**
	 * Get the URI type
	 */
	@Override
	public String getType(Uri uri) {
		switch (sUriMatcher.match(uri)) {
		case REPORT_DATA:
		case SYS_INFO:
		case SETTINGS:
		case TYPE_CONTROL:
		case REPEATED_ISSUE:
			return BugReport.CONTENT_TYPE;
		default:
			throw new IllegalArgumentException("Unknown URI " + uri);
		}
	}
	
}
