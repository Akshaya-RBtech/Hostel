package com.wastezero.app;

public class AppConfig {
    /**
     * Backend URL for WasteZero Flask Server.
     * DEVELOPMENT MODE: Uses local IP or Emulator IP.
     * PRODUCTION MODE: Uses the public deployed backend URL.
     */
    public static final boolean IS_DEVELOPMENT_MODE = BuildConfig.DEBUG;
    
    // The IP address of your laptop for development testing
    public static final String LOCAL_DEVELOPMENT_URL = "http://192.168.1.69:5000";
    
    // The public server URL for production (Deployment required)
    public static final String PRODUCTION_URL = "https://hostell-ger6.onrender.com"; // SUCCESSFUL PRODUCTION BACKEND
    
    public static final String BACKEND_URL = IS_DEVELOPMENT_MODE ? LOCAL_DEVELOPMENT_URL : PRODUCTION_URL;
}
