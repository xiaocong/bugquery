package com.borqs.bugreporter.settings;

import com.borqs.bugreporter.R;
import com.borqs.bugreporter.util.Util;
import com.borqs.bugreporter.util.Util.ReportData;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * View the local report data.
 */
public class LocalDataActivity extends Activity {
	
	private static final String TAG = "LocalDataActivity";
	
	private Context context = null;
	private LinearLayout totalList = null;
	private ReportData[] data = null;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		
		Intent intent=getIntent();
		String action = intent.getAction();
		if (null == action || "".equals(action)) {
			finish();
			return;
		}
		context = this;
		setContentView(R.layout.local_data_list);
		totalList = (LinearLayout)findViewById(R.id.local_data_list);
		
		//Display the local data
		if (action.equals(Util.Action.VIEW_LOCAL_DATA)) {
			try{
				data = ReportData.getReportData(context);
				if (data == null) {
					finish();
					return;
				}
				this.setTitle(this.getTitle().toString() + ": " + data.length);
				
				for (int i = 0; i < data.length; i++){
					Util.log(TAG, "data item: " + i);
					//one item
					LinearLayout item = new LinearLayout(context);
					item.setOrientation(LinearLayout.HORIZONTAL);
					
					//sub item
					LinearLayout subItem = new LinearLayout(context);
					subItem.setOrientation(LinearLayout.VERTICAL);
					
					//type
					TextView typeView = new TextView(context);
					typeView.setText("Type: " + data[i].getBugType());
					
					//name
					TextView nameView = new TextView(context);
					nameView.setText("Name: " + data[i].getName());
					
					//description
					TextView descriptionView = new TextView(context);
					descriptionView.setText("Description: " + data[i].getInfo());
					
					subItem.addView(typeView);
					subItem.addView(nameView);
					subItem.addView(descriptionView);
					
					final ReportData reportData = data[i];
					Button removeButton = new Button(context);
					
					//Get screen width
					DisplayMetrics metric = new DisplayMetrics();
			        getWindowManager().getDefaultDisplay().getMetrics(metric);
			        int width = metric.widthPixels; 
			        
			        //set button width
			        removeButton.setWidth(width);
					removeButton.setText("remove");
					removeButton.setOnClickListener(new OnClickListener(){
						public void onClick(View v) {
							reportData.delete(context);
							totalList.removeAllViews();
							finish();
							Intent intent = new Intent(Util.Action.VIEW_LOCAL_DATA);
							startActivity(intent);
						}						
					});
					subItem.addView(removeButton);
					
					item.addView(subItem);
					totalList.addView(item);
				}
			}catch (Exception e) {
				e.printStackTrace();
				finish();
				return;
			}
			
			
		}else {
			finish();
			return;
		}
		
		
	}

	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		menu.add("Send Manually");
		return true;
	}

	@Override
	public boolean onMenuItemSelected(int featureId, MenuItem item) {
		context.startService(new Intent(Util.Action.SEND_REPORT));
		
		//TODO: Should wait for the result.
		totalList.removeAllViews();
		finish();
		Intent intent = new Intent(Util.Action.VIEW_LOCAL_DATA);
		startActivity(intent);
		return true;
	}
	
}
