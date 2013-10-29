package com.borqs.bugreporter;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.SecureRandom;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import org.json.JSONException;
import org.json.JSONObject;

import com.borqs.bugreporter.manual.ManualReportActivity;
import com.borqs.bugreporter.settings.Settings;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.util.Util.ReportData;

import android.app.IntentService;
import android.content.Intent;
import android.os.SystemClock;
import android.text.TextUtils;

/**
 * Send issue report(JSON string format) to BugReporter server with device info, logs... etc.
 */
public class SenderService extends IntentService {
	
	private final static String TAG = "SenderService";	
	
	private Settings settings = null;
	

	public SenderService() {
		super(TAG);
	}

	/**
	 * Receive "send report" request, and send the report(JSON string format) to server.
	 */
	@Override
	protected void onHandleIntent(Intent intent) {
		
		//Get action, and make sure it's not null or 0-length
		String action = intent.getAction();
		if (TextUtils.isEmpty(action)) {
			return;
		}
		
		if (action.equals(Util.Action.SEND_REPORT)) {
			Util.log(TAG, "----SenderService---.");
			//Check if the network is available
			if (!Util.SysInfo.isNetworkAvailable(this)){
				if(Util.DBG) Util.log(TAG, "Network is not available.");
	    		return;
	    	}
			
			//Get server address
	    	settings = new Settings(this);
			String serverUrl = settings.getServerAddress();
			
			//Get report data from database
			ReportData[] data = null;
			data = ReportData.getReportData(this);
			if (data == null) {
				if (Util.DBG) Util.log(TAG, "data = null!");
				return;
			}
			
			for(int i = 0; i < data.length; i++){
				boolean deleteData = true;
				long newServerId = -1;
				String reportStr = null;

				//Send report to server
				try {
					// Convert report data to JSON string
					reportStr = ConvertToJSONString(data[i]);
					if (!TextUtils.isEmpty(reportStr)) {
						long t0 = System.currentTimeMillis();
						newServerId = sendReport(serverUrl, reportStr);
						Util.log(TAG, "SendReport() takes time: " + (System.currentTimeMillis() 
								- t0) + " (ms). " + "The newServerId = " + newServerId);
					}
				} catch (Exception e) {
					Util.log(TAG, "When sending data:" + e.toString());
				}
					
				//Upload log to server if send to server successfully
				if (newServerId > 0) {
					data[i].setServerId(newServerId);
					Util.log(TAG, "data[i].hasFilePath():" + data[i].filePath);
					if (data[i].hasFilePath()) {
						Util.log(TAG, "data[i].bugType: " + data[i].bugType);
						if (data[i].bugType.equals(ManualReportActivity.BUG_TYPE) || (settings.isUploadLog())) {
							long t0 = System.currentTimeMillis();
							boolean uploadSucceed = uploadFile(serverUrl, newServerId, data[i].getFilePath());
							Util.log(TAG, "UploadFile() takes time: " + (System.currentTimeMillis() 
									- t0) + " (ms).");
							//Set delete_local_data true if upload log to server successfully
							if (uploadSucceed) {
								deleteData = true;
							}
						}else {
							Util.log(TAG, "User don't want to upload log |settings.isUploadLog(): " + settings.isUploadLog());
							deleteData = true;
						}
					}
				}else {
					//Keep the log data if send report to server failed
					deleteData = false;
				}
				
				//Delete local data if necessary 
				if(deleteData) {
					data[i].delete(this);
				}
			}
		}else {
			return;
		}

	}
	

	/**
	 * Send report data and read feedback,
	 * @param reportStr
	 * @return id from server, maybe -1.
	 * @throws Exception Throws if encounter permanently error.
	 */
	public long sendReport(String url,String reportStr) {
		if (Util.DBG) {
			Util.log(TAG, "sendReport(),serverUrl = " + url);
		}
		
		long id = -1;
		HttpURLConnection conn = null;
		BufferedWriter writer = null;
		BufferedInputStream feedbackStream = null;
		BufferedInputStream errorStream = null;
		
		try{
			//Create a trust manage that doesn't validate the certificate chains
			TrustManager[] trustAllCerts = new TrustManager[] { new X509TrustManager() {
				public java.security.cert.X509Certificate[] getAcceptedIssuers() {
					return null;
				}
				
				public void checkClientTrusted(
						java.security.cert.X509Certificate[] certs,
						String authType) {
				}
				
				public void checkServerTrusted(
						java.security.cert.X509Certificate[] certs,
						String authType) {
				}
			} };
			
			//Install the all-trusting trust manager
			final SSLContext sc = SSLContext.getInstance("SSL");
			sc.init(null, trustAllCerts, new SecureRandom());
			HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
			
			//Create all-trusting host name verifier
			HostnameVerifier allHostValid = new HostnameVerifier() {
				@Override
				public boolean verify(String hostname, SSLSession session) {
					// Trust all.
					return true;
				}
			};
			
			//Install the all-trusting host name verifier
			HttpsURLConnection.setDefaultHostnameVerifier(allHostValid);
			
			//Transfer report stream
			URL reportUrl = new URL(url);
			conn = (HttpURLConnection) reportUrl.openConnection();
			conn.setDoInput(true);//Set whether this URLConnection allows input.
			conn.setDoOutput(true);//Set whether this URLConnection allows output.
			conn.setUseCaches(false);//Set whether this connection allows to use caches or not.
			conn.setConnectTimeout(30 * 1000);//Sets the maximum time to wait while connecting.
			conn.setReadTimeout(30 * 1000);//Sets the maximum time to wait for an input stream read.
			conn.setRequestProperty("Charset", "UTF-8");//Set the specified request header field.
			conn.setRequestProperty("Client-Name", "BugReporter");
			conn.setRequestProperty("Content-Type", "text/plain");
			
			writer = new BufferedWriter(new OutputStreamWriter(conn.getOutputStream()));
			writer.write(reportStr);
			writer.write("\n");
			writer.flush();
			writer.close();
			writer = null;
			
			//Get the response code and check if send successfully.
			int responseCode = conn.getResponseCode();
			switch(responseCode) {
			case 200://HTTP status code, 200: OK 
				feedbackStream = new BufferedInputStream(conn.getInputStream());
				String feedbackStr = readStream(feedbackStream);
				if(Util.DBG) Util.log(TAG, "feedback String is: " + feedbackStr);
				JSONObject jsonObject = new JSONObject(feedbackStr);
				id = Long.parseLong(jsonObject.getString(Util.JSON.Server_ID));
				if(Util.DBG) Util.log(TAG, "Send report success,serverid = " + id);
				break;
			case 500://HTTP status code, 500: Internal error 
				errorStream = new BufferedInputStream(conn.getInputStream());
				String errorMsgStr = readStream(errorStream);
				if(Util.DBG) Util.log(TAG, "Send report fail, error message: " + errorMsgStr);
				throw new Exception("Send report fail, error message: " + errorMsgStr);
			default://Throw exception with the responseCode
				if(Util.DBG) Util.log(TAG, "Send report fail, with response code: " + responseCode);
				throw new Exception("Send report fail, unknown reason. " +
						"Response code: " + responseCode);
			}
			
		}catch (Exception e) {
			e.printStackTrace();
			return -1;
		}finally {
			if (errorStream != null) {
				try {
					errorStream.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				errorStream = null;
			}
			
			if (feedbackStream != null) {
				try {
					feedbackStream.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				feedbackStream = null;
			}
			
			if (writer != null) {
				try {
					writer.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				writer = null;
			}
			
			if (conn != null) {
				try {
					conn.disconnect();
				} catch (Exception e) {
					e.printStackTrace();
				}
				conn = null;
			}
		}
		
		//return the server id after sending successfully
		return id;
	}
	
	/**
	 * Upload log file to server.
	 * @param url
	 * @param id
	 * @param filePath
	 * @return
	 */
	public boolean uploadFile(String url,long id, String filePath){
		if (Util.DBG) {
			Util.log(TAG, "sendReport(),serverUrl = " + url);
			Util.log(TAG, "sendReport(),serverId = " + id);
			Util.log(TAG, "sendReport(),filePath = " + filePath);
		}
		
		long feedbackId = -1;
		HttpURLConnection conn = null;
		BufferedInputStream fileStream = null;
		BufferedOutputStream outputStream = null;
		BufferedInputStream feedbackStream = null;
		BufferedInputStream errorStream = null;
		final int MAX_RETRY = 3;
		
		for (int i = 0; i < MAX_RETRY; i++) {
			try {
				URL uploadURL = new URL(url);
				conn = (HttpURLConnection)uploadURL.openConnection();
				conn.setDoInput(true);
				conn.setDoOutput(true);
				conn.setRequestMethod("PUT");//Set the request command to be sent to the remote HTTP server.
				conn.setUseCaches(false);
				conn.setConnectTimeout(30 * 1000);
				conn.setReadTimeout(30 * 1000);
				conn.setRequestProperty("Charset", "UTF-8");
				conn.setRequestProperty("Client-Name", "BugReporter");
				conn.setRequestProperty("Content-Type", "application/zip");
				conn.setRequestProperty("Record-Id", ("" + id));// write "id"
				
				outputStream = new BufferedOutputStream(conn.getOutputStream());
				fileStream = new BufferedInputStream(new FileInputStream(filePath));
				
				//For debug, log the file size
				File file = new File(filePath);
				if(Util.DBG) Util.log(TAG, "log file size: " + (file.length() / 1024f) + "KB");
				
				byte[] buffer = new byte[64 * 1024];
				int len = -1;
				while ((len = fileStream.read(buffer)) != -1) {
					outputStream.write(buffer, 0, len);
				}
				outputStream.flush();
				outputStream.close();
				outputStream = null;
				
				//Get the response code and check if send successfully
				int responseCode = conn.getResponseCode();
				switch(responseCode) {
				case 200:
					feedbackStream = new BufferedInputStream(conn.getInputStream());
					String feedbackStr = readStream(feedbackStream);
					JSONObject jsonObject = new JSONObject(feedbackStr);
					feedbackId = Long.parseLong(jsonObject.getString(Util.JSON.Server_ID));
					if(Util.DBG) Util.log(TAG, "Upload log file successfully. feedbackId: " + feedbackId);
					if(feedbackId == id) {
						// Notify user send successfully
						if (settings.isShowUserNotificaion()){
							Util.notify(this, "Data sending is successful, server id is: "
									+ id + " .", Util.Action.NOTIFY_RESULT, false, false);
						} else {
							Util.log(TAG, "userNotify is disabled, please enable it in settings -> User Notifications "
									+ "if you want to get notifications");
						}
					}else {
						Util.log(TAG, "Server error: id is not equal. Original id: " + id 
								+ ", feedback id: " + feedbackId);
					}
					break;
				case 500:
					errorStream = new BufferedInputStream(conn.getErrorStream());
					String errorMsgStr = readStream(errorStream);
					if(Util.DBG) Util.log(TAG, "Upload log file fail, error message: " + errorMsgStr);
					throw new Exception("Server Error:" + errorMsgStr);
				default:
					if(Util.DBG) Util.log(TAG, "Upload log file fail, unknown reason.");
					throw new Exception("Upload log file fail, unknown reason. " +
						"Response code: " + responseCode);
				}
				
				//Get here means send successfully. So don't need to retry.
				return true;
				
			}catch (Exception e) {
				e.printStackTrace();
				if(Util.DBG) Util.log(TAG, "When upload log file, " + e.toString());
				SystemClock.sleep(5000);
				continue;
			}finally {
				if (errorStream != null) {
					try {
						errorStream.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
					errorStream = null;
				}
				
				if (feedbackStream != null) {
					try {
						feedbackStream.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
					feedbackStream = null;
				}
				
				if (outputStream != null) {
					try {
						outputStream.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
					outputStream = null;
				}
				
				if (fileStream != null) {
					try {
						fileStream.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
					fileStream = null;
				}
				
				if (conn != null) {
					try{
						conn.disconnect();
					}catch (Exception e) {
						e.printStackTrace();
					}
					conn = null;
				}
			}
		}
		
		return false;
	}
	
	
	
	/**
	 * Convert the report data into JSON string which can be send directly. 
	 * JSONObject: ReportDataJSONString
	 * Extras: UUID
	 *         SYS_INFO
	 *         BUG_INFO (bug_type, name, info, time)
	 *         CATEGORY
	 * 
	 * @param data
	 * @return string
	 */
	public String ConvertToJSONString(ReportData data) {
		//if(DBG) Util.log(tag,"toJSONString()");
		try{
			//Define the report data JSON string object
			JSONObject reportDataJSONString = new JSONObject();
			
			//Define bugInfo and sysInfo JSON string object
			JSONObject bugInfo = new JSONObject();
			JSONObject sysInfo = new JSONObject();			
			
			//Get bugInfo
			bugInfo.put(Util.JSON.BUG_TYPE, data.getBugType() );
			bugInfo.put(Util.JSON.NAME, data.getName());
			bugInfo.put(Util.JSON.INFO, data.getInfo());
			bugInfo.put(Util.JSON.TIME, data.getTime());
			
			//Get systeInfo
			Util.log(TAG,"this.sysInfo,null?" + (data.getSysInfo() == null));
			Set<Map.Entry<String,Object>> valueSet = data.getSysInfo().valueSet();
			Iterator<Map.Entry<String,Object>> list = valueSet.iterator();
			while(list.hasNext()){
				Map.Entry<String, Object> entry = list.next();
				sysInfo.put(entry.getKey(), (String)entry.getValue());
			}
			
			//Put these info to reportDataJSONString object
			reportDataJSONString.put(Util.JSON.UUID, data.getUUID());
			reportDataJSONString.put(Util.JSON.SYS_INFO, sysInfo);
			reportDataJSONString.put(Util.JSON.BUG_INFO, bugInfo);
			reportDataJSONString.put(Util.JSON.CATEGORY, data.getCategory());
			
			return reportDataJSONString.toString();
			
		}catch(JSONException je){
			return null;
		}
	}
	
	/*
	 * Read string from input stream.
	 */
	private String readStream(InputStream is) throws IOException  {
		StringBuffer stringBuffer = new StringBuffer();
		int len = 0;
		byte[] buf = new byte[1024];
		while ((len = is.read(buf)) != -1) {
			stringBuffer.append(new String(buf, 0, len));
		}
		return stringBuffer.toString();
	}

}
