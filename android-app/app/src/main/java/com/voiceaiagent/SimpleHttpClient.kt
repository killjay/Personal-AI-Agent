package com.voiceaiagent

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

/**
 * Simple HTTP client for communicating with the Voice AI Agent server
 * Replaces Google API dependencies with direct HTTP calls
 */
class SimpleHttpClient {
    
    companion object {
        private const val TAG = "SimpleHttpClient"
        private const val SERVER_BASE_URL = "http://192.168.1.120:5000" // Adjust to your server IP
    }
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    
    /**
     * Get emails from the server
     */
    suspend fun getEmails(): String? = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("$SERVER_BASE_URL/gmail/unread")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                response.body?.string()
            } else {
                Log.e(TAG, "Failed to get emails: ${response.code}")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting emails", e)
            null
        }
    }
    
    /**
     * Get calendar events from the server
     */
    suspend fun getCalendarEvents(): String? = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("$SERVER_BASE_URL/calendar/upcoming")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                response.body?.string()
            } else {
                Log.e(TAG, "Failed to get calendar events: ${response.code}")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting calendar events", e)
            null
        }
    }
    
    /**
     * Send a query to the server
     */
    suspend fun sendQuery(query: String): String? = withContext(Dispatchers.IO) {
        try {
            val jsonBody = JSONObject().put("query", query)
            val requestBody = jsonBody.toString().toRequestBody("application/json".toMediaTypeOrNull())
            
            val request = Request.Builder()
                .url("$SERVER_BASE_URL/query")
                .post(requestBody)
                .build()
            
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                response.body?.string()
            } else {
                Log.e(TAG, "Failed to send query: ${response.code}")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error sending query", e)
            null
        }
    }
    
    /**
     * Test server connection
     */
    suspend fun testConnection(): Boolean = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("$SERVER_BASE_URL/health")
                .get()
                .build()
            
            val response = client.newCall(request).execute()
            response.isSuccessful
        } catch (e: Exception) {
            Log.e(TAG, "Error testing connection", e)
            false
        }
    }
}
