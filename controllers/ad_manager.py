import flet as ft
import sys
import os

class AdManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized: return
        self.initialized = True
        self.is_android = "ANDROID_ARGUMENT" in os.environ
        self.test_mode = True 
        
        # AdMob IDs (Test IDs by default)
        # Replace these with real IDs for release!
        self.BANNER_ID = "ca-app-pub-8287106746857092/8682304054" # Test ID
        
        if self.is_android:
            self._init_android()
            
    def _init_android(self):
        try:
            from jnius import autoclass, cast
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.AdView = autoclass('com.google.android.gms.ads.AdView')
            self.AdRequest = autoclass('com.google.android.gms.ads.AdRequest')
            self.AdSize = autoclass('com.google.android.gms.ads.AdSize')
            self.MobileAds = autoclass('com.google.android.gms.ads.MobileAds')
            self.LayoutParams = autoclass('android.widget.FrameLayout$LayoutParams')
            self.Gravity = autoclass('android.view.Gravity')
            
            # Initialize Mobile Ads (Async)
            # We need a context. PythonActivity.mActivity is the Context.
            activity = self.PythonActivity.mActivity
            
            def init_callback(status):
                print("AdMob Initialized")
                
            # In real Java: MobileAds.initialize(context, listener)
            # Mapping listeners in jnius is complex, so we often skip or pass null if allowed.
            # 23.0.0+ needs initialization.
            self.MobileAds.initialize(activity)
            
        except Exception as e:
            print(f"WARNING: Android AdMob Init Failed: {e}")

    def get_banner_widget(self):
        """Returns a Flet Control representing the Banner Ad."""
        if self.is_android:
            # On Android, we create the native view and let it sit on top.
            # We assume Flet Layout leaves space, or we overlay it.
            if not self.initialized: return ft.Container()
            
            self._create_android_banner()
            return ft.Container(height=50, bgcolor=ft.Colors.TRANSPARENT) 
        else:
            # Desktop / Web Placeholder
            return self._get_desktop_placeholder()

    def _create_android_banner(self):
        try:
            from jnius import autoclass, cast
            
            activity = self.PythonActivity.mActivity
            
            # Create AdView
            ad_view = self.AdView(activity)
            ad_view.setAdSize(self.AdSize.BANNER)
            ad_view.setAdUnitId(self.BANNER_ID)
            
            # Create Request
            builder = self.AdRequest.Builder()
            request = builder.build()
            
            # Load Ad
            ad_view.loadAd(request)
            
            # Add to Layout
            # We put it at the bottom center
            layout_params = self.LayoutParams(
                self.LayoutParams.WRAP_CONTENT,
                self.LayoutParams.WRAP_CONTENT
            )
            layout_params.gravity = self.Gravity.BOTTOM | self.Gravity.CENTER_HORIZONTAL
            
            # We need to run this on the UI thread
            activity.addContentView(ad_view, layout_params)
            print("Android Banner Added to View Hierarchy")
            
        except Exception as e:
            print(f"Error creating Android Banner: {e}")
