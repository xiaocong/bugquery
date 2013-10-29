package com.borqs.bugreporter.settings;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;
import android.text.TextUtils;

import com.borqs.bugreporter.MessageReceiver;
import com.borqs.bugreporter.ProcessorService;
import com.borqs.bugreporter.SenderService;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.provider.BugReport;
import com.borqs.bugreporter.provider.DBHelper;

/**
 * Provide switch for turn on/off, data connection, types to report, log on/off, 
 * data not sent, system info... etc.
 *
 */
public class Settings {
	
	private static final boolean DBG = Util.DBG;
	private static final String TAG = "Settings";
	private Context context = null;
	private DBHelper dbHelper = null;
	
	//Define the BugReport sever
	public static final String PROP_BUGREPORTER_SERVER = "ro.bugreporter.server";
	public static final String DEFAULT_SERVER = "http://bugreport.borqs.com/bugreport/report";
	public static final String ATS_SERVER = "http://ats.borqs.com/bugreport/report";
//	public static final String DEFAULT_SERVER = "http://192.168.4.55:8010/api/brquery/report";
//	public static final String ATS_SERVER = "http://192.168.4.55:8010/api/brquery/report";
	
	
	public Settings(Context context){
		this.context = context;
		dbHelper = new DBHelper(context);
	}
	

	/**
	 * Define the settings data.
	 */
	public static class SettingsData {
		public boolean bugReporter   = true;
		public String  serverAddress = null;
		public boolean wifiOnly      = true;
		public boolean uploadLog     = true;
		public boolean userNotify    = true;
		public boolean firstBoot     = true;
	}
	
	/**
	 * Set default settings on first boot.
	 */
	public void setDefaultSettings(){
		if(isFirstBoot()){			
			setFirstBoot(false);
		}
		
	}
	
	
	/**
	 * Get if it's first boot
	 * @return
	 */
	public boolean isFirstBoot(){
		//if(DBG) Util.log(tag, "isFirstBoot()");
		try{
			SettingsData settings = dbHelper.getSettings();
			return settings.firstBoot;
		}catch(Exception e){
			e.printStackTrace();
			return false;
		}		
	}
	
	/**
	 * Set first boot
	 * @param value
	 */
	public void setFirstBoot(boolean value){
		//if(DBG) Util.log(tag, "setFirstBoot()");
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.firstBoot = value;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();			
		}
	}
	
	
	/**
	 * Get the BugReporter status
	 * @return
	 */
	public boolean isBugReporterEnabled(){
		if(DBG) Util.log(TAG, "isBugReporterEnabled()");
		try{
			SettingsData settings = dbHelper.getSettings();
			return settings.bugReporter;
		} catch (Exception e) {
			e.printStackTrace();
			return false;
		}	
	}
	
	/**
	 * Set a new status of the BugReporter 
	 * @param value
	 */
	public void setBugReporterEnable(boolean value){
		if(DBG) Util.log(TAG, "setBugReporterEnable()|value: " + value);
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.bugReporter = value;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();			
		}
		setComponentEnable(value);
		/*
		if(isTypeEnabled(LiveTimeMonitor.NAME)){
			LiveTimeMonitor.set(context, value);
		}*/
	}	
	
	
	/**
	 * Get the server address
	 * @return
	 */
	public String getServerAddress(){
		if(DBG) Util.log(TAG, "getServerAddress()");
		try{
			SettingsData settings = dbHelper.getSettings();
			if(TextUtils.isEmpty(settings.serverAddress)){
				/*
				 * Read from system properties then hard code.
				 */
				if(DBG) Util.log(TAG, "Get default server:" + DEFAULT_SERVER);
				return DEFAULT_SERVER;
			}else{
				if(DBG) Util.log(TAG, "Address = " + settings.serverAddress);
				return settings.serverAddress;
			}
		}catch(Exception e){
			e.printStackTrace();
			return null;
		}
	}
	/**
	 * Set a new server address
	 * @param address
	 */
	public void setServerAddress(String address){
		if(DBG) Util.log(TAG, "setServerAddress()|address" + address);
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.serverAddress = address;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();			
		}
	}


	/**
	 * Get if data sending only via wifi.
	 * @return
	 */
	public boolean isViaWifiOnly(){
		if(DBG) Util.log(TAG, "isViaWifiOnly()");
		try{
			SettingsData settings = dbHelper.getSettings();
			return settings.wifiOnly;
		}catch(Exception e){
			e.printStackTrace();
			return false;
		}
	}
	/**
	 * Set the data sending
	 * @param onlyWifi
	 */
	public void setViaWifiOnly(boolean onlyWifi){
		if(DBG) Util.log(TAG, "setViaWifiOnly()|onlyWifi: " + onlyWifi);
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.wifiOnly = onlyWifi;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();
		}
	}
	

	/**
	 * Get the value of uploadLog
	 * @return
	 */
	public boolean isUploadLog(){
		if(DBG) Util.log(TAG, "isUploadLog()");
		try{
			SettingsData settings = dbHelper.getSettings();
			return settings.uploadLog;
		}catch(Exception e){
			e.printStackTrace();
			return false;
		}		
	}
	/**
	 * Set a new value of uploadLog
	 * @param value
	 */
	public void setUploadLog(boolean value){
		if(DBG) Util.log(TAG, "setUploadLog()|value: " + value);
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.uploadLog = value;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();			
		}
	}
	
	/**
	 * Check if show user notifications.
	 * @return
	 */
	public boolean isShowUserNotificaion(){
		if(DBG) Util.log(TAG, "isShowUserNotificaion()");
		try{
			SettingsData settings = dbHelper.getSettings();
			return settings.userNotify;
		}catch(Exception e){
			e.printStackTrace();
			return true;
		}
	}
	/**
	 * Set a new value of show user notifications
	 * @param agree
	 */
	public void setShowUserNotification(boolean value){
		if(DBG) Util.log(TAG, "setShowUserNotifications()|value: " + value);
		try{
			SettingsData settings = dbHelper.getSettings();
			settings.userNotify = value;
			dbHelper.setSettings(settings);
		}catch(Exception e){
			e.printStackTrace();
		}
	}
	
	
	

	/**
	 * Define the type control
	 */
	public static class TypeControl{
		public String type = null;
		public boolean allowed = true;
	}

	/**
	 * For internal monitor to check whether it is enabled.
	 * blocked--> disable
	 * allowed--> enable
	 * not in list-->build default(user build:disable,eng build:enable)
	 * @param type
	 * @return
	 */
	public boolean isTypeEnabled(String type){
		if(DBG) Util.log(TAG, "isTypeEnabled()|type=" + type);
		try{
			TypeControl control = dbHelper.getTypeControl(type);			
			if(control != null){
				return control.allowed;
			}
			Util.log(TAG, "control = null...why?");
			
			control = getDefaultTypeControl();	
			if(control != null){
				//TODO: add new type here?  Any risks here?
				setTypeEnabled(type, true);
				return control.allowed;
			}			
		}catch(Exception e){
			e.printStackTrace();
		}
		return !Util.SysInfo.isUserBuild();
	}
	
	/**
	 * Set type control in type control list. If the type not in list, add it.
	 * @param type
	 * @param state
	 */
	public void setTypeEnabled(String type, boolean status){
		if(DBG) Util.log(TAG, "settings: setTypeControl(),type:" + type + ",allowed:" + status);
		if(type!=null){
			TypeControl control = new TypeControl();
			control.type = type;
			control.allowed = status;
			
			//If the type not in list, add it.
			dbHelper.setTypeControl(control);
		}
	}
	
	/*
	 * Get default type control
	 */
	private TypeControl getDefaultTypeControl()throws Exception{
		if(DBG) Util.log(TAG,"getDefaultTypeControl()");
		return dbHelper.getTypeControl(BugReport.TYPE_UNKNOWN);
	}
	
	
	
	
	/**
	 * Disable/enable Components in Bug Report when disable/enable the function of bug report
	 * Should also disable service & activity.
	 * @param opened
	 */
	public void setComponentEnable(boolean opened) {
		if(DBG) Util.log(TAG, "setComponentEnable(),open?"+opened);
		
		PackageManager pm = context.getPackageManager();
		if (pm == null) {
			if(DBG) Util.log(">>>>>Can not get PackageManager");
			return;
		}
		
		ComponentName msgReceiver = new ComponentName(context.getPackageName(), MessageReceiver.class.getName());
		ComponentName reportProcessor = new ComponentName(context.getPackageName(), ProcessorService.class.getName());
		ComponentName senderService = new ComponentName(context.getPackageName(), SenderService.class.getName());
				
		if(opened){
			pm.setComponentEnabledSetting(msgReceiver, PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
			pm.setComponentEnabledSetting(reportProcessor, PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
			pm.setComponentEnabledSetting(senderService, PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
		} else {
			pm.setComponentEnabledSetting(msgReceiver, PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
			pm.setComponentEnabledSetting(reportProcessor, PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
			pm.setComponentEnabledSetting(senderService, PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
		}
	}

}
