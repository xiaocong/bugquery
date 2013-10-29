package com.borqs.bugreporter.dev;

import android.app.LauncherActivity;
import android.content.Intent;

public class DevLauncherActivity extends LauncherActivity {
    protected Intent getTargetIntent() {
        Intent targetIntent = new Intent(Intent.ACTION_MAIN, null);
        targetIntent.addCategory(Intent.CATEGORY_TEST);
        targetIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        return targetIntent;
    }
}
