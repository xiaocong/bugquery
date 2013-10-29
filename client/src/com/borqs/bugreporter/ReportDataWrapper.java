package com.borqs.bugreporter;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.borqs.bugreporter.provider.DBHelper;
import com.borqs.bugreporter.settings.Settings;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.util.Util.ReportData;

import android.app.IntentService;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.os.Bundle;
import android.text.TextUtils;

/**
 * A formal interface to receive and wrapper all issue reports from 
 * dropbox, livetime, kernel panic, 3rd-parties, and manual report.
 * 
 * All direct operation on report data should rely on this class.
 * 
 * action: "com.borqs.bugreporter.BUG_NOTIFY"
 * extras: CATEGORY
 *         BUG_TYPE (this extra is mandatory)
 *         NAME
 *         DESCRIPTION
 *         FILE_PATH
 *         FILE_KEEP
 *         SYS_INFO
 *         
 *         ENABLE_ONLINE_LOGCAT
 *         ENABLE_ONLINE_LOGCAT_RADIO
 *         
 *         
 */
public class ReportDataWrapper extends IntentService {
	
	private static final String TAG = "ReportDataWrapper";
	
	
	public ReportDataWrapper() {
		super(TAG);
	}

	/**
	 * Receive and wrapper all the issue reports.
	 */
	@Override
	protected void onHandleIntent(Intent intent) {
		DBHelper dbHelper = new DBHelper(this);
		ReportData reportData = new ReportData();
		
		//Get action, and make sure it's not null or 0-length
		String action = intent.getAction();
		if (TextUtils.isEmpty(action)) {
			Util.log(TAG, "Invalid action!");
			return;
		}
		
		if (action.equals(Util.Action.BUG_NOTIFY)) {
			Util.log(TAG, "Received intent.");
			
			// 1. Wrapper data
			// 1.1 BUG_TYPE
			if(intent.hasExtra(Util.ExtraKeys.BUG_TYPE)){
				//bug_type is a mandatory extra
				reportData.bugType = intent.getStringExtra(Util.ExtraKeys.BUG_TYPE);
				if(TextUtils.isEmpty(reportData.bugType)){
					throw new IllegalArgumentException("The bug type is empty!");
				}
			} else {
				throw new IllegalArgumentException("No bug type!");
			}
			
			
			// 1.2 CATEGORY
			if (intent.hasExtra(Util.ExtraKeys.CATEGORY)) {
				reportData.category = intent
						.getStringExtra(Util.ExtraKeys.CATEGORY);
				if (TextUtils.isEmpty(reportData.category)) {
					throw new IllegalArgumentException("bug category is empty!");
				}
				Util.log(TAG, "category: " + reportData.category);
			}

			// 1.3 NAME
			if (intent.hasExtra(Util.ExtraKeys.NAME)) {
				reportData.name = intent.getStringExtra(Util.ExtraKeys.NAME);
				if (TextUtils.isEmpty(reportData.name)) {
					throw new IllegalArgumentException("bug name is empty!");
				}
			}

			// 1.4 DESCRIPTION
			if (intent.hasExtra(Util.ExtraKeys.DESCRIPTION)) {
				reportData.info = intent
						.getStringExtra(Util.ExtraKeys.DESCRIPTION);
				if (TextUtils.isEmpty(reportData.info)) {
					throw new IllegalArgumentException(
							"bug description is empty!");
				}
			}

			// 1.5 FILE_PATH
			if (intent.hasExtra(Util.ExtraKeys.FILE_PATH)) {
				reportData.filePath = intent
						.getStringExtra(Util.ExtraKeys.FILE_PATH);
				if (TextUtils.isEmpty(reportData.filePath)) {
					throw new IllegalArgumentException("file path is empty!");
				}
			}

			// 1.6 FILE_KEEP
			if (intent.hasExtra(Util.ExtraKeys.FILE_KEEP)) {
				reportData.fileKeep = intent
						.getStringExtra(Util.ExtraKeys.FILE_KEEP);
				if (TextUtils.isEmpty(reportData.fileKeep)) {
					throw new IllegalArgumentException(
							"file path(keep) is empty!");
				}
			}

			// 1.7 ENABLE_ONLINE_LOGCAT
			if (intent.hasExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT)) {
				String value = null;
				value = intent
						.getStringExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT);
				if ("true".equalsIgnoreCase(value)) {
					reportData.hasOnlineLog = true;
				} else if ("false".equalsIgnoreCase(value)) {
					reportData.hasOnlineLog = false;
				} else {
					throw new IllegalArgumentException(
							"Invalid value of option \"enable online logcat\"!");
				}
			}

			// 1.8 ENABLE_ONLINE_LOGCAT_RADIO
			if (intent.hasExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT_RADIO)) {
				String value = null;
				value = intent
						.getStringExtra(Util.ExtraKeys.ENABLE_ONLINE_LOGCAT_RADIO);
				if ("true".equalsIgnoreCase(value)) {
					reportData.hasOnlineRadioLog = true;
				} else if ("false".equalsIgnoreCase(value)) {
					reportData.hasOnlineRadioLog = false;
				} else {
					throw new IllegalArgumentException(
							"Invalid value of option \"enable online logcat radio\"!");
				}
			}

			// 1.9 TIME
			reportData.time = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss",
					Locale.CHINA).format(new Date(System.currentTimeMillis()));
			reportData.uuid = UUID.randomUUID().toString();

			// 1.10 SYSTEM_INFO
			SharedPreferences sp = this.getSharedPreferences(
					"SystemInfoPreference", MODE_PRIVATE);
			if (sp.getBoolean(Util.SysInfo.SYSTEM_INFO, false)) {
				// If true, get system info from database
				Util.log(TAG, "get sysInfo from database...");
				reportData.sysInfo = dbHelper.getSysInfo();
			} else {
				// If false, get system info now, and save to database
				Util.log(TAG, "get sysInfo now...");
				reportData.sysInfo = Util.SysInfo.getSysInfo(this);
				
				// store shared preference value
				Editor editor = sp.edit();
				editor.putBoolean(Util.SysInfo.SYSTEM_INFO, true);
				editor.commit();

				// store to database
				dbHelper.storeSystemInfo(reportData.sysInfo);
			}

			
			//If BUG_TYPE is enabled, save report data to database and handle log 
			Settings settings = new Settings(this);
			String type = reportData.isError() ? reportData.bugType : reportData.name;
			if (settings.isTypeEnabled(type)) {

				//2. Save report data to database
				reportData.id = dbHelper.addReportData(reportData.category,
						reportData.bugType, reportData.name, reportData.info,
						reportData.filePath, reportData.time, reportData.uuid,
						reportData.sysInfo);
				Util.log(TAG, "reportData.id: " + reportData.id);
				
				//3. Handle log
				//3.1 Create dataFileDir
				String dataFileDir = this.getFilesDir().getPath() + File.separatorChar + reportData.id + File.separatorChar;
				Util.log(TAG, "==dataFileDir: " + dataFileDir);
				File fileDir = new File(dataFileDir);
				if(!fileDir.exists()){
					Util.log(TAG, "==fileDir doesn't exist!");
					try{
						if(!fileDir.mkdir()){
							throw new Exception("Create data file directory fail!");
						}else {
							Util.log(TAG, "Create it successfully!");
						}
					}catch (Exception e) {
						e.printStackTrace();
					}
				}
				
				//3.2 Get online log for Manually_Report bugs
				//3.2.1 Get online logcat / radio log
				if(reportData.hasOnlineLog){
					Util.DataFile.getOnlineLogcatLog( dataFileDir + "online_logcat.log");
				}
				if(reportData.hasOnlineRadioLog){
					Util.DataFile.getRadioLog(dataFileDir + "radio_logcat.log");
				}
				
				//3.2.2 Get logs from DropBoxCollector
				//1)logs from filePath
				if(reportData.filePath != null){
					reportData.filePath = getLogFromPath(reportData.filePath, dataFileDir, false);
					Util.log(TAG, "==reportData.filePath: " + reportData.filePath);
				}else {
					dbHelper.setFilePath(reportData.id, "");
				}
				//2)logs from fileKeep
				if(reportData.fileKeep != null){
					reportData.fileKeep = getLogFromPath(reportData.fileKeep, dataFileDir, true);
					Util.log(TAG, "==reportData.fileKeep: " + reportData.fileKeep);
				}
				
				//3.3 Zip the log files
				String zippedFileName = this.getFilesDir().getPath() + File.separatorChar + reportData.id + ".zip";
				zippedFileName = ZipLogFiles(dataFileDir, zippedFileName);
				reportData.filePath = zippedFileName;
				//Set file_path in database
				dbHelper.setFilePath(reportData.id, zippedFileName);
				Util.log(TAG, "zippedFilePath: " + zippedFileName);
				//Delete the original log files after zip
				Util.DataFile.delete(this.getFilesDir().getPath() + File.separatorChar + reportData.id);
				
				
			}else {
				//If BUG_TYPE is disabled, delete report data and related log.
				Util.log(TAG, "This tpye: " + reportData.bugType + "is disabled... Don't need to report.");
				if(TextUtils.isEmpty(reportData.filePath)) {
					Util.log(TAG, "reportData.filePath is empty. Don't need to delete extra log...");
				}else {
					Util.log(TAG, "Need to delete reportData.filePath: " + reportData.filePath);
					if(reportData.filePath.contains(";")){
						String[] fileList = reportData.filePath.split(";");
						for(int i = 0; i < fileList.length; i++){
							Util.log(TAG, "Deleting: " + fileList[i] + " ...");
							Util.DataFile.delete(fileList[i]);
						}
					}else {
						Util.DataFile.delete(reportData.filePath);
					}
					
				}
				reportData.delete(this);
				reportData = null;
				return;
			}
			
		}else {
			return;
		}
		
		//Send data to SenderService
		Intent target = new Intent(Util.Action.SEND_REPORT);
		startService(target);
	}

	/**
	 * Get log from specified log path
	 * @param path Source log path
	 * @param destDir Destination log path 
	 * @param keep Boolean, keep the source log files if true, and delete them if false
	 * @return 
	 */
	public String getLogFromPath(String path, String destDir, Boolean keep) {
		Util.log(TAG, "==getLogFrom: " + path);
		if(path.contains(";")){
			String[] fileList = path.split(";");
			String tmpPath = null;
			for(int i = 0; i < fileList.length; i++){
				tmpPath = null;
				try {
					if(Util.DBG) Util.log(TAG, "==filename: " + fileList[i]);
					
					if (keep) {
						Util.log(TAG, "fileKeep");
						tmpPath = Util.DataFile.copy(fileList[i], destDir);
					}else {
						Util.log(TAG, "filePath");
						tmpPath = Util.DataFile.move(fileList[i], destDir);
					}
					
					if(Util.DBG) Util.log(TAG, "==tmpPath: " + tmpPath);
				} catch (Exception e) {
					e.printStackTrace();
				}
				if(tmpPath == null){
					if(Util.DBG) Util.log(TAG, "Error file path:" + fileList[i]);
				}
			}
		}else{
			try {
				Util.log(TAG, "==filePath: " + path);
				if (keep) {
					path = Util.DataFile.copy(path, destDir);
				}else {
					path = Util.DataFile.move(path, destDir);
				}
				//return dest file path
				Util.log(TAG, "==copy or move logs to: " + path);
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
		
		return path;
	}
	
	public String ZipLogFiles(String dataFileDir, String zippedFileName) {
		Util.log(TAG, "==ZipLogFiles");
		
		File fileDir = new File(dataFileDir);
		File[] fileList = fileDir.listFiles();
		Util.log(TAG, "==fileList: " + fileList.length);
		if(fileList != null && fileList.length > 0){
			Util.log(TAG, "==start zip file!");
			//zip
			Util.DataFile.zip(dataFileDir, zippedFileName);
			
			//Check zipped file size
			File zippedFile = new File(zippedFileName);
			if (zippedFile.length() > 1 * 1024 * 1024) {
				if (Util.DBG) Util.log(TAG, "Data file size larger than 1M");
				//TODO: How to deal with file oversized.
			}
			return zippedFileName;
			
		}else{
			return "";
		}
	}

}
