package com.borqs.bugreporter.provider;

import java.io.File;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.text.TextUtils;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.util.Util.ReportData;
import com.borqs.bugreporter.settings.Settings.SettingsData;
import com.borqs.bugreporter.settings.Settings.TypeControl;


public class DBHelper {
	private final String TAG = "DBHelper";
	private static final boolean DBG = Util.DBG;

	public static final int RECORD_COUNT_LIMIT = 50;

	private ContentResolver mResolver;	
	
	public DBHelper(Context context) {
		//if(DBG) Util.log(tag,"DBHelper(Context)");
		this.mResolver = context.getContentResolver();
	}

	/**
	 * Save report data to database.
	 */
	public long addReportData(String category, String type, String name,
			String info, String filePath, String time, String uuid,
			ContentValues sysInfo) {
		//if (DBG) Util.log(tag, "addReportData()");
		long id = -1;
		if (getCount() > RECORD_COUNT_LIMIT) {
			delOldestData();
		}

		/* What will happen if some parameter is null? */
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_CATEGORY, category);
		values.put(BugReport.COL_TYPE, type);
		values.put(BugReport.COL_NAME, name);
		values.put(BugReport.COL_INFO, info);
		values.put(BugReport.COL_FILE_PATH, filePath);
		values.put(BugReport.COL_TIME, time);
		values.put(BugReport.COL_UUID, uuid);
		Uri uri = mResolver.insert(BugReport.CONTENT_URI_REPORT_DATA, values);
		id = ContentUris.parseId(uri);
		//if (DBG) Util.log(tag, "id=" + id);

//		Set<Map.Entry<String, Object>> entrySet = null;
//		if (sysInfo != null && sysInfo.size() > 0) {
//			//if(DBG) Util.log(tag,"sysInfo.size() = " + sysInfo.size());
//			entrySet = sysInfo.valueSet();
//			Iterator<Map.Entry<String, Object>> entriesIter = entrySet
//					.iterator();
//			while (entriesIter.hasNext()) {
//				Map.Entry<String, Object> entry = entriesIter.next();
//				String key = entry.getKey();
//				String value = (String) entry.getValue();
//				ContentValues sysInfoValue = new ContentValues();
//				sysInfoValue.put(BugReport.COL_ID, Long.valueOf(id));
//				sysInfoValue.put(BugReport.COL_KEY, key);
//				sysInfoValue.put(BugReport.COL_VALUE, value);
//				mResolver.insert(BugReport.CONTENT_URI_SYS_INFO, sysInfoValue);
//			}
//		}else{
//			if(DBG) Util.log(TAG,"sysInfo is null or size 0!");
//		}

		return id;
	}
	
	
	/**
	 * Get all the report data items in database.
	 * @return
	 */
	public ReportData[] getReportData() {
		//if(DBG) Util.log(tag,"getReportData()[]");
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_REPORT_DATA,
				null, null, null, null);
		if(cursor == null){
			if(DBG) Util.log(TAG,"cursor==null!");
			return null;
		}
		int count = cursor.getCount();
		//if(DBG) Util.log(tag,"count=" + count);
		ReportData[] result = new ReportData[count];

		if (cursor != null) {
			if (cursor.moveToFirst()) {
				for (int i = 0; i < count; i++) {
					result[i] = new ReportData();
					result[i].setId(cursor.getLong(cursor
							.getColumnIndex(BugReport.COL_ID)));
					result[i].setCategory(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_CATEGORY)));
					result[i].setBugType(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_TYPE)));
					result[i].setName(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_NAME)));
					result[i].setInfo(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_INFO)));
					result[i].setFilePath(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_FILE_PATH)));
					result[i].setTime(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_TIME)));
					result[i].setUUID(cursor.getString(cursor
							.getColumnIndex(BugReport.COL_UUID)));
					result[i].setServerId(cursor.getLong(cursor
							.getColumnIndex(BugReport.COL_SERVER_ID)));
//					result[i].setSysInfo(getSysInfo(result[i].getId()));
					result[i].setSysInfo(getSysInfo());
					cursor.moveToNext();
				}
			}
			cursor.close();
			cursor = null;
		}
		return result;
	}


	/*
	 * Get system info.
	 */
	public ContentValues getSysInfo() {
		//if(DBG) Util.log(tag,"getSysInfo(id),id="+id);
		ContentValues sysInfo = null;
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_SYS_INFO, null,
				BugReport.COL_ID + "=" + 1, null, null);
		if (cursor != null) {
			int count = cursor.getCount();
			//if(DBG) Util.log(tag,"count="+count);
			if (count > 0) {
				if (cursor.moveToFirst()) {
					sysInfo = new ContentValues();
					for (int i = 0; i < count; i++) {
						String key = cursor.getString(cursor
								.getColumnIndex(BugReport.COL_KEY));
						String value = cursor.getString(cursor
								.getColumnIndex(BugReport.COL_VALUE));
						sysInfo.put(key, value);
						cursor.moveToNext();
					}
				}
			}
			cursor.close();
			cursor = null;
		}else{
			if(DBG) Util.log(TAG,"cursor == null!");
		}
		
		if(DBG) Util.log(TAG,"sysInfo == null? | " + (sysInfo == null));
		
		return sysInfo;
	}

	/**
	 * Store system info, or update it if already exists.
	 * @param sysInfo
	 */
	public void storeSystemInfo(ContentValues sysInfo) {
		
		Set<Map.Entry<String, Object>> entrySet = null;
		if (sysInfo != null && sysInfo.size() > 0) {
			//if(DBG) Util.log(tag,"sysInfo.size() = " + sysInfo.size());
			entrySet = sysInfo.valueSet();
			Iterator<Map.Entry<String, Object>> entriesIter = entrySet
					.iterator();
			while (entriesIter.hasNext()) {
				Map.Entry<String, Object> entry = entriesIter.next();
				String key = entry.getKey();
				String value = (String) entry.getValue();
				ContentValues sysInfoValue = new ContentValues();
				sysInfoValue.put(BugReport.COL_ID, 1);
				sysInfoValue.put(BugReport.COL_KEY, key);
				sysInfoValue.put(BugReport.COL_VALUE, value);
				mResolver.insert(BugReport.CONTENT_URI_SYS_INFO, sysInfoValue);
			}
		}else{
			if(DBG) Util.log(TAG,"sysInfo is null or size 0!");
		}
		
	}
	
	/**
	 * Get report data count.
	 * @return
	 */
	public int getCount() {
		//if(DBG) Util.log(tag,"getCount()");
		int recordCount = 0;
		String[] projection = { "count(*)" };
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_REPORT_DATA,
				projection, null, null, null);

		if (cursor != null) {
			if (cursor.moveToFirst()) {
				recordCount = cursor.getInt(0);
			}
			cursor.close();
			cursor = null;
		}
		return recordCount;
	}

	/**
	 * Clear report data, system info, and data file if exist.
	 */
	public void clearReportData() {
		//if(DBG) Util.log(tag,"clearReportData()");
		String[] projection = { BugReport.COL_FILE_PATH };
		String filePath = null;
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_REPORT_DATA,
				projection, null, null, null);
		if (cursor != null) {
			int count = cursor.getCount();
			if (count > 0) {
				if (cursor.moveToFirst()) {
					for (int i = 0; i < count; i++) {
						filePath = null;
						filePath = cursor.getString(cursor
								.getColumnIndex(BugReport.COL_FILE_PATH));
						if (!TextUtils.isEmpty(filePath)) {
							File dataFile = new File(filePath);
							if (dataFile.exists()) {
								dataFile.delete();
							}
							dataFile = null;
						}
					}
				}
			}
			cursor.close();
			cursor = null;
		}

		mResolver.delete(BugReport.CONTENT_URI_REPORT_DATA, null, null);
		mResolver.delete(BugReport.CONTENT_URI_SYS_INFO, null, null);
	}

	/**
	 * Delete report data,sys info,and data file if exist.
	 * @param id
	 */
	public void delReportData(long id) {
		//if(DBG) Util.log(tag,"delReportData()");
		String[] projection = { BugReport.COL_FILE_PATH };
		String filePath = null;
		if (id == -1) {
			return;
		}
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_REPORT_DATA,
				projection, BugReport.COL_ID + "=" + id, null, null);
		if (cursor != null) {
			if (cursor.getCount() > 0) {
				if (cursor.moveToFirst()) {
					filePath = cursor.getString(cursor
							.getColumnIndex(BugReport.COL_FILE_PATH));
					if (!TextUtils.isEmpty(filePath)) {
						File dataFile = new File(filePath);
						if (dataFile.exists()) {
							dataFile.delete();
						}
						dataFile = null;
					}
				}
			}
			cursor.close();
			cursor = null;
		}

		mResolver.delete(BugReport.CONTENT_URI_REPORT_DATA, BugReport.COL_ID
				+ "=" + id, null);
	}

	/**
	 * Set a new server id.
	 * @param localId
	 * @param serverId
	 */
	public void setServerId(long localId, long serverId) {
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_SERVER_ID, Long.valueOf(serverId));
		mResolver.update(BugReport.CONTENT_URI_REPORT_DATA, values,
				BugReport.COL_ID + "=" + localId, null);
	}

	/**
	 * Set a new file path.
	 * @param id
	 * @param filePath
	 */
	public void setFilePath(long id, String filePath) {
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_FILE_PATH, filePath);
		mResolver.update(BugReport.CONTENT_URI_REPORT_DATA, values,
				BugReport.COL_ID + "=" + id, null);
	}
	
	/**
	 * Set a new description info.
	 * @param id
	 * @param info
	 */
	public void setInfo(long id, String info) {
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_INFO, info);
		mResolver.update(BugReport.CONTENT_URI_REPORT_DATA, values,
				BugReport.COL_ID + "=" + id, null);
	}

	/*
	 * Delete oldest data
	 * TODO: sort order : "modified ASC", need to consider more
	 */
	private void delOldestData() {
		String[] projection = { BugReport.COL_ID };
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_REPORT_DATA,
				projection, null, null, "modified ASC");
		long id = -1;
		if (cursor != null) {
			if (cursor.moveToFirst()) {
				id = cursor.getLong(0);
			}
			cursor.close();
			cursor=null;
		}
		delReportData(id);
	}

	
	
	/**
	 * Get settings data.
	 * @return
	 * @throws Exception
	 */
	public SettingsData getSettings() throws Exception {
		//if(DBG) Util.log(tag, "getSettings()");
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_SETTINGS, null,
				null, null, null);

		if (cursor == null) {
			throw new Exception("Encounter error while get settings data!");
		}
		int count = cursor.getCount();
		if (count != 1) {
			throw new Exception("settings table has more data!count=" + count);
		}
		SettingsData result = null;

		if (cursor.moveToFirst()) {
			result = new SettingsData();
			int value = (cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_BUG_REPORTER)));
			result.bugReporter = (value == 1 ? true : false);
			result.serverAddress = cursor.getString(cursor
					.getColumnIndex(BugReport.COL_SERVER_ADDRESS));
			value = cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_WIFI_ONLY));
			result.wifiOnly = (value == 1 ? true : false);
			value = cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_UPLOAD_LOG));
			result.uploadLog = (value == 1 ? true : false);
			value = cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_USER_NOTIFY));
			result.userNotify = (value == 1 ? true : false);
			value = cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_FIRST_BOOT));
			result.firstBoot = (value == 1 ? true : false);
		}
		cursor.close();
		cursor = null;

		return result;
	}

	/**
	 * Set settings data.
	 * @param data
	 */
	public void setSettings(SettingsData data) {
		Util.log(TAG, "setSettings|bugReporter: " + (data.bugReporter ? 1 : 0));
		Util.log(TAG, "setSettings|serverAddress: " + data.serverAddress );
		Util.log(TAG, "setSettings|wifiOnly: " + (data.wifiOnly ? 1 : 0));
		Util.log(TAG, "setSettings|uploadLog: " + (data.uploadLog ? 1 : 0));
		Util.log(TAG, "setSettings|userNotify: " + (data.userNotify ? 1 : 0));
		Util.log(TAG, "setSettings|firstBoot: " + (data.firstBoot ? 1 : 0));
		
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_BUG_REPORTER, (data.bugReporter ? 1 : 0));
		values.put(BugReport.COL_SERVER_ADDRESS, data.serverAddress);
		values.put(BugReport.COL_WIFI_ONLY, (data.wifiOnly ? 1 : 0));
		values.put(BugReport.COL_UPLOAD_LOG, (data.uploadLog ? 1 : 0));
		values.put(BugReport.COL_USER_NOTIFY, (data.userNotify ? 1 : 0));
		values.put(BugReport.COL_FIRST_BOOT, (data.firstBoot ? 1 : 0));

		mResolver.update(BugReport.CONTENT_URI_SETTINGS, values, null, null);
	}

	/**
	 * Get the type control list.
	 * @return
	 * @throws Exception
	 */
	public TypeControl[] getTypeControlList() throws Exception {
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_TYPE_CONTROL,
				null, null, null, null);

		if (cursor == null) {
			throw new Exception("Encounter error while get type control data!");
		}
		int count = cursor.getCount();
		TypeControl[] result = new TypeControl[count];

		if (cursor.moveToFirst()) {
			for (int i = 0; i < count; i++) {
				result[i] = new TypeControl();
				result[i].type = cursor.getString(cursor
						.getColumnIndex(BugReport.COL_TYPE));
				int value = (cursor.getInt(cursor
						.getColumnIndex(BugReport.COL_STATE)));
				result[i].allowed = (value == 1 ? true : false);
				cursor.moveToNext();
			}
		}
		cursor.close();
		cursor = null;

		return result;
	}

	/**
	 * Get the state of a specified bug type. 
	 * @param type    bug type
	 * @return    TypeControl(including bug_type and bug_state)
	 * @throws Exception
	 */
	public TypeControl getTypeControl(String type) throws Exception {
		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_TYPE_CONTROL,
				null, BugReport.COL_TYPE + "='" + type + "'", null, null);

		if (cursor == null) {
			throw new Exception("Encounter error while get type control data!");
		}
		int count = cursor.getCount();
		if (count == 0) {
			cursor.close();
			cursor = null;
			return null;
		}
		if (count > 1) {
			throw new Exception(
					"Control type can't be duplicate,so count should not larger than 1.");
		}
		TypeControl result = null;
		if (cursor.moveToFirst()) {
			result = new TypeControl();
			result.type = cursor.getString(cursor
					.getColumnIndex(BugReport.COL_TYPE));
			int value = (cursor.getInt(cursor
					.getColumnIndex(BugReport.COL_STATE)));
			result.allowed = (value == 1 ? true : false);
		}
		cursor.close();
		cursor = null;

		return result;
	}

	/**
	 * Set the state of a specified bug type.
	 * @param control    TypeControl (including bug_type and bug_state)
	 */
	public void setTypeControl(TypeControl control) {
		//if (DBG) Util.log(tag, "setTypeControl()");
		boolean hasType = false;
		ContentValues values = new ContentValues();
		values.put(BugReport.COL_STATE, control.allowed ? 1 : 0);

		Cursor cursor = mResolver.query(BugReport.CONTENT_URI_TYPE_CONTROL,
				null, BugReport.COL_TYPE + "='" + control.type + "'", null,
				null);
		if (cursor == null) {
			hasType = false;
		} else {
			if (cursor.getCount() == 0) {
				hasType = false;
			} else {
				hasType = true;
			}
			cursor.close();
			cursor = null;			
		}
		if (hasType) {
			mResolver.update(BugReport.CONTENT_URI_TYPE_CONTROL, values,
					BugReport.COL_TYPE + "='" + control.type + "'", null);
		} else {
			values.put(BugReport.COL_TYPE, control.type);
			mResolver.insert(BugReport.CONTENT_URI_TYPE_CONTROL, values);
		}
	}

}
