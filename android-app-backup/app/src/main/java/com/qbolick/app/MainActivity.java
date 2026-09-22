package com.qbolick.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TextView title = new TextView(this);
        title.setText("QBOLICK");
        title.setTextSize(32);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setBackgroundColor(Color.BLACK);

        setContentView(title);
    }
}
