package com.voiceaiagent

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import org.json.JSONObject

/**
 * Simple Service - Manages communication with the Voice AI Agent server
 * Replaces the complex MCP Server with direct HTTP calls
 */
class SimpleService(private val context: Context) {
    
    companion object {
        private const val TAG = "SimpleService"
        
        @Volatile
        private var INSTANCE: SimpleService? = null
        
        fun getInstance(context: Context): SimpleService {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SimpleService(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
    
    private val httpClient = SimpleHttpClient()
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var isRunning = false
    
    /**
     * Start Simple Service
     */
    suspend fun startService(): Boolean {
        return try {
            if (isRunning) {
                Log.i(TAG, "Simple Service already running")
                return true
            }
            
            Log.i(TAG, "🚀 Starting Simple Service...")
            
            // Test connection to server
            val connected = httpClient.testConnection()
            
            if (connected) {
                isRunning = true
                Log.i(TAG, "✅ Simple Service started successfully")
                true
            } else {
                Log.e(TAG, "❌ Failed to connect to server")
                false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error starting Simple Service: ${e.message}")
            false
        }
    }
    
    /**
     * Stop Simple Service
     */
    fun stopService() {
        Log.i(TAG, "🛑 Stopping Simple Service...")
        isRunning = false
        serviceScope.cancel()
        Log.i(TAG, "✅ Simple Service stopped")
    }
    
    /**
     * Check if service is running
     */
    fun isServiceRunning(): Boolean = isRunning
    
    /**
     * Get service status
     */
    fun getServiceStatus(): JSONObject {
        return JSONObject().apply {
            put("serviceName", "simple-service")
            put("initialized", isRunning)
            put("timestamp", System.currentTimeMillis())
        }
    }
    
    /**
     * Get emails from server
     */
    suspend fun getEmails(): JSONObject {
        return try {
            if (!isRunning) {
                return JSONObject().apply {
                    put("error", "Service not running")
                }
            }
            
            val response = httpClient.getEmails()
            if (response != null) {
                JSONObject(response)
            } else {
                JSONObject().apply {
                    put("error", "Failed to get emails")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting emails", e)
            JSONObject().apply {
                put("error", e.message)
            }
        }
    }
    
    /**
     * Get calendar events from server
     */
    suspend fun getCalendarEvents(): JSONObject {
        return try {
            if (!isRunning) {
                return JSONObject().apply {
                    put("error", "Service not running")
                }
            }
            
            val response = httpClient.getCalendarEvents()
            if (response != null) {
                JSONObject(response)
            } else {
                JSONObject().apply {
                    put("error", "Failed to get calendar events")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting calendar events", e)
            JSONObject().apply {
                put("error", e.message)
            }
        }
    }
    
    /**
     * Send query to server
     */
    suspend fun sendQuery(query: String): JSONObject {
        return try {
            if (!isRunning) {
                return JSONObject().apply {
                    put("error", "Service not running")
                }
            }
            
            val response = httpClient.sendQuery(query)
            if (response != null) {
                JSONObject(response)
            } else {
                JSONObject().apply {
                    put("error", "Failed to send query")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error sending query", e)
            JSONObject().apply {
                put("error", e.message)
            }
        }
    }
    
    /**
     * Test server connection
     */
    suspend fun testConnection(): Boolean {
        return try {
            httpClient.testConnection()
        } catch (e: Exception) {
            Log.e(TAG, "Error testing connection", e)
            false
        }
    }
}
