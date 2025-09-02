package com.voiceaiagent

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.ContactsContract
import android.provider.MediaStore
import android.speech.tts.TextToSpeech
import android.util.Log
import android.view.MotionEvent
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.util.concurrent.TimeUnit
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.sqrt

class MainActivity : AppCompatActivity() {
    private var recorder: MediaRecorder? = null
    private var audioFile: File? = null
    private val serverUrl = "http://192.168.1.120:5005/voice" // Your PC's IP address
    private lateinit var recordButton: Button
    private lateinit var statusText: TextView
    private var isRecording = false
    
    // Voice Activity Detection
    private var audioRecord: AudioRecord? = null
    private var isListening = false
    private var isWakeWordDetected = false
    private var recordingBuffer = mutableListOf<Short>()
    private val handler = Handler(Looper.getMainLooper())
    private var silenceTimer: Runnable? = null
    
    // Audio configuration
    private val sampleRate = 16000
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT
    private val bufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
    
    // Voice Activity Detection thresholds
    private val silenceThreshold = 300  // Lower threshold for better sensitivity
    private val wakeWordThreshold = 10000 // Higher threshold for wake word detection
    
    // Text-to-Speech
    private lateinit var textToSpeech: TextToSpeech
    private var isTTSInitialized = false
    private val silenceTimeoutMs = 2000L // 2 seconds of silence to stop recording
    private val maxRecordingTimeMs = 30000L // 30 seconds max recording

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        recordButton = findViewById(R.id.recordButton)
        statusText = findViewById(R.id.statusText)
        
        // Initialize Text-to-Speech
        initializeTTS()
        
        requestPermissions()
        setupUI()
    }

    private fun setupUI() {
        recordButton.text = "Hold to Record"
        recordButton.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startRecording()
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    stopRecording()
                    true
                }
                else -> false
            }
        }
        statusText.text = "Hold button and speak your command"
    }

    private fun startContinuousListening() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Audio permission required", Toast.LENGTH_SHORT).show()
            return
        }

        if (isListening) return

        try {
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize * 2
            )

            if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
                showError("Failed to initialize audio recording")
                return
            }

            audioRecord?.startRecording()
            isListening = true
            isWakeWordDetected = false

            Thread {
                val buffer = ShortArray(bufferSize)
                while (isListening) {
                    val bytesRead = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                    if (bytesRead > 0) {
                        processAudioBuffer(buffer, bytesRead)
                    }
                }
            }.start()

            runOnUiThread {
                statusText.text = "Listening for 'June'..."
            }

        } catch (e: Exception) {
            showError("Failed to start listening: ${e.message}")
        }
    }

    private fun stopContinuousListening() {
        isListening = false
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        
        if (isRecording) {
            finishRecording()
        }
    }

    private fun processAudioBuffer(buffer: ShortArray, length: Int) {
        val rms = calculateRMS(buffer, length)
        
        if (!isWakeWordDetected) {
            // Look for wake word activation - use lower RMS threshold
            if (rms > 50) { // Much lower RMS threshold for wake word detection
                detectWakeWord(buffer, length)
            }
        } else if (isRecording) {
            // During recording, monitor for voice activity
            recordingBuffer.addAll(buffer.take(length))
            
            if (rms > 30) { // Lower RMS threshold for silence detection
                // Voice detected, reset silence timer
                resetSilenceTimer()
            } else {
                // Silence detected, start/continue silence timer
                startSilenceTimer()
            }
            
            // Safety: stop recording after max time
            if (recordingBuffer.size > sampleRate * 30) { // 30 seconds max
                handler.post { finishRecording() }
            }
        }
    }

    private fun calculateRMS(buffer: ShortArray, length: Int): Double {
        var sum = 0.0
        for (i in 0 until length) {
            val sample = buffer[i].toDouble()
            sum += sample * sample
        }
        return sqrt(sum / length)
    }

    private fun detectWakeWord(buffer: ShortArray, length: Int) {
        // Simple wake word detection based on audio pattern
        // For now, we'll trigger on any sustained audio above threshold
        
        var consecutiveHighSamples = 0
        var maxAmplitude = 0
        
        for (i in 0 until length) {
            val amplitude = abs(buffer[i].toInt())
            if (amplitude > maxAmplitude) {
                maxAmplitude = amplitude
            }
            
            if (amplitude > wakeWordThreshold / 3) { // Lower threshold: 166 instead of 250
                consecutiveHighSamples++
            } else {
                consecutiveHighSamples = 0
            }
            
            // If we have enough consecutive samples, consider it a wake word
            if (consecutiveHighSamples > sampleRate / 20) { // Only 0.05 second of audio (800 samples)
                runOnUiThread {
                    statusText.text = "Audio detected! Max: $maxAmplitude"
                }
                handler.post { onWakeWordDetected() }
                return
            }
        }
        
        // Update status when voice is detected
        if (maxAmplitude > wakeWordThreshold / 3) {
            runOnUiThread {
                statusText.text = "Voice detected - say 'June'..."
            }
        }
    }

    private fun onWakeWordDetected() {
        if (isWakeWordDetected) return
        
        isWakeWordDetected = true
        recordingBuffer.clear()
        isRecording = true
        
        statusText.text = "Wake word detected! Listening for command..."
        Toast.makeText(this, "June detected - speak your command", Toast.LENGTH_SHORT).show()
        
        // Start silence timer immediately
        startSilenceTimer()
    }

    private fun startSilenceTimer() {
        silenceTimer?.let { handler.removeCallbacks(it) }
        silenceTimer = Runnable {
            if (isRecording) {
                finishRecording()
            }
        }
        handler.postDelayed(silenceTimer!!, silenceTimeoutMs)
    }

    private fun resetSilenceTimer() {
        silenceTimer?.let { handler.removeCallbacks(it) }
    }

    private fun finishRecording() {
        if (!isRecording) return
        
        isRecording = false
        isWakeWordDetected = false
        resetSilenceTimer()
        
        statusText.text = "Processing command..."
        
        // Convert recorded buffer to audio file
        try {
            val outputDir = externalCacheDir ?: cacheDir
            audioFile = File.createTempFile("voice_cmd", ".wav", outputDir)
            
            saveAudioToFile(recordingBuffer.toShortArray(), audioFile!!)
            sendAudioToServer(audioFile!!)
            
        } catch (e: Exception) {
            showError("Failed to save audio: ${e.message}")
            statusText.text = "Say 'June' then your command"
        }
        
        recordingBuffer.clear()
    }

    private fun saveAudioToFile(audioData: ShortArray, file: File) {
        try {
            FileOutputStream(file).use { out ->
                // Write WAV header
                writeWavHeader(out, audioData.size * 2, sampleRate)
                
                // Write audio data
                for (sample in audioData) {
                    out.write(sample.toInt() and 0xff)
                    out.write((sample.toInt() shr 8) and 0xff)
                }
            }
        } catch (e: Exception) {
            throw IOException("Failed to write audio file: ${e.message}")
        }
    }

    private fun writeWavHeader(out: FileOutputStream, audioDataSize: Int, sampleRate: Int) {
        val header = ByteArray(44)
        val totalDataLen = audioDataSize + 36
        val channels = 1
        val byteRate = sampleRate * channels * 2
        
        header[0] = 'R'.code.toByte()  // RIFF
        header[1] = 'I'.code.toByte()
        header[2] = 'F'.code.toByte()
        header[3] = 'F'.code.toByte()
        
        header[4] = (totalDataLen and 0xff).toByte()
        header[5] = ((totalDataLen shr 8) and 0xff).toByte()
        header[6] = ((totalDataLen shr 16) and 0xff).toByte()
        header[7] = ((totalDataLen shr 24) and 0xff).toByte()
        
        header[8] = 'W'.code.toByte()  // WAVE
        header[9] = 'A'.code.toByte()
        header[10] = 'V'.code.toByte()
        header[11] = 'E'.code.toByte()
        
        header[12] = 'f'.code.toByte() // fmt
        header[13] = 'm'.code.toByte()
        header[14] = 't'.code.toByte()
        header[15] = ' '.code.toByte()
        
        header[16] = 16  // fmt chunk size
        header[17] = 0
        header[18] = 0
        header[19] = 0
        
        header[20] = 1   // audio format (PCM)
        header[21] = 0
        
        header[22] = channels.toByte()
        header[23] = 0
        
        header[24] = (sampleRate and 0xff).toByte()
        header[25] = ((sampleRate shr 8) and 0xff).toByte()
        header[26] = ((sampleRate shr 16) and 0xff).toByte()
        header[27] = ((sampleRate shr 24) and 0xff).toByte()
        
        header[28] = (byteRate and 0xff).toByte()
        header[29] = ((byteRate shr 8) and 0xff).toByte()
        header[30] = ((byteRate shr 16) and 0xff).toByte()
        header[31] = ((byteRate shr 24) and 0xff).toByte()
        
        header[32] = (channels * 2).toByte() // block align
        header[33] = 0
        
        header[34] = 16  // bits per sample
        header[35] = 0
        
        header[36] = 'd'.code.toByte() // data
        header[37] = 'a'.code.toByte()
        header[38] = 't'.code.toByte()
        header[39] = 'a'.code.toByte()
        
        header[40] = (audioDataSize and 0xff).toByte()
        header[41] = ((audioDataSize shr 8) and 0xff).toByte()
        header[42] = ((audioDataSize shr 16) and 0xff).toByte()
        header[43] = ((audioDataSize shr 24) and 0xff).toByte()
        
        out.write(header)
    }

    private fun requestPermissions() {
        val permissions = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.SEND_SMS,
            Manifest.permission.READ_CONTACTS
        )
        ActivityCompat.requestPermissions(this, permissions, 0)
    }

    override fun onDestroy() {
        super.onDestroy()
        stopContinuousListening()
        if (::textToSpeech.isInitialized) {
            textToSpeech.stop()
            textToSpeech.shutdown()
        }
    }

    override fun onPause() {
        super.onPause()
        // Keep listening in background for wake word
    }

    override fun onResume() {
        super.onResume()
        if (!isListening) {
            startContinuousListening()
        }
    }

    private fun sendAudioToServer(audio: File) {
        val client = OkHttpClient.Builder().callTimeout(60, TimeUnit.SECONDS).build()
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", audio.name, audio.asRequestBody("audio/wav".toMediaTypeOrNull()))
            .build()
        val request = Request.Builder().url(serverUrl).post(requestBody).build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { 
                    showError("Network error: ${e.message}")
                    statusText.text = "Say 'June' then your command"
                }
            }
            override fun onResponse(call: Call, response: Response) {
                if (!response.isSuccessful) {
                    runOnUiThread { 
                        showError("Server error: ${response.code}")
                        statusText.text = "Say 'June' then your command"
                    }
                    return
                }
                val body = response.body?.string() ?: ""
                Log.d("VoiceAgent", "Server response: $body")
                try {
                    val action = JSONObject(body)
                    runOnUiThread { 
                        Toast.makeText(this@MainActivity, "Received: $body", Toast.LENGTH_SHORT).show()
                    }
                    handleAction(action)
                } catch (e: Exception) {
                    runOnUiThread { 
                        showError("Invalid server response")
                        statusText.text = "Say 'June' then your command"
                    }
                }
            }
        })
    }

    private fun handleAction(action: JSONObject) {
        runOnUiThread {
            Log.d("VoiceAgent", "Received action: $action")
            val actionType = action.optString("action")
            Log.d("VoiceAgent", "Action type: $actionType")
            
            when (actionType) {
                "call" -> {
                    // Check for enhanced response format first
                    val actionTypeField = action.optString("action_type")
                    val dialString = action.optString("dial_string")
                    val phoneNumber = action.optString("phone_number")
                    val contactName = action.optString("contact_name")
                    val directDial = action.optBoolean("direct_dial", false)
                    val useContacts = action.optBoolean("use_contacts", true)
                    
                    Log.d("VoiceAgent", "Enhanced calling - action_type: $actionTypeField, dial_string: $dialString, direct_dial: $directDial")
                    
                    val numberToCall = when {
                        // Priority 1: Use dial_string if present and direct_dial is true
                        directDial && dialString.isNotEmpty() -> {
                            Log.d("VoiceAgent", "Using direct dial with number: $dialString")
                            dialString
                        }
                        // Priority 2: Use phone_number if present
                        phoneNumber.isNotEmpty() -> {
                            Log.d("VoiceAgent", "Using phone_number: $phoneNumber")
                            phoneNumber
                        }
                        // Priority 3: Fall back to legacy contact field
                        else -> {
                            val contact = action.optString("contact")
                            Log.d("VoiceAgent", "Falling back to contact lookup for: $contact")
                            
                            // Check if contact is a phone number (contains only digits, +, -, spaces, parentheses)
                            if (contact.matches(Regex("[+\\d\\s\\-()]+")) && contact.replace(Regex("[^\\d]"), "").length >= 3) {
                                contact // It's already a phone number
                            } else {
                                lookupContactNumber(contact) // Look up contact name
                            }
                        }
                    }
                    
                    if (numberToCall != null && numberToCall.isNotEmpty()) {
                        val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$numberToCall"))
                        if (intent.resolveActivity(packageManager) != null) {
                            startActivity(intent)
                            val displayName = if (directDial) "number $numberToCall" else (contactName.takeIf { it.isNotEmpty() } ?: numberToCall)
                            showSuccess("Calling $displayName")
                        } else {
                            showError("Cannot make calls")
                        }
                    } else {
                        // If no contact found, open dialer
                        val fallbackContact = action.optString("contact")
                        val intent = Intent(Intent.ACTION_DIAL)
                        startActivity(intent)
                        showError("Contact '$fallbackContact' not found, opening dialer")
                    }
                }
                "send_sms" -> {
                    val contact = action.optString("contact")
                    val message = action.optString("message")
                    val phoneNumber = lookupContactNumber(contact)
                    if (phoneNumber != null) {
                        val smsIntent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:$phoneNumber"))
                        smsIntent.putExtra("sms_body", message)
                        if (smsIntent.resolveActivity(packageManager) != null) {
                            startActivity(smsIntent)
                            showSuccess("SMS sent to $contact")
                        } else {
                            showError("Cannot send SMS")
                        }
                    } else {
                        showError("Contact '$contact' not found")
                    }
                }
                "open_app" -> {
                    val appName = action.optString("app").lowercase()
                    Log.d("VoiceAgent", "Trying to open app: $appName")
                    
                    // First, let's debug what apps are actually available
                    debugInstalledApps(appName)
                    
                    if (openAppByName(appName)) {
                        showSuccess("Opened $appName")
                    } else {
                        showError("App $appName not found. Check logs for available apps.")
                    }
                }
                "error" -> {
                    showError(action.optString("message"))
                }
                "speak" -> {
                    val message = action.optString("message")
                    Log.d("VoiceAgent", "Speaking message: $message")
                    speakText(message)
                }
                "notes" -> {
                    val message = action.optString("message")
                    val noteContent = action.optString("note_content", "")
                    Log.d("VoiceAgent", "Notes action: $message")
                    speakText("Note created successfully")
                    showSuccess(message)
                }
                "list" -> {
                    val message = action.optString("message")
                    val items = action.optJSONArray("items")
                    Log.d("VoiceAgent", "List action: $message")
                    speakText("Added to your list")
                    showSuccess(message)
                }
                else -> {
                    showError("Unknown action: $actionType")
                }
            }
            statusText.text = "Say 'June' then your command"
        }
    }

    private fun lookupContactNumber(contactName: String): String? {
        val contentResolver = contentResolver
        val cursor = contentResolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
            ),
            "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?",
            arrayOf("%$contactName%"),
            null
        )
        
        cursor?.use {
            if (it.moveToFirst()) {
                val phoneNumberIndex = it.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER)
                if (phoneNumberIndex >= 0) {
                    return it.getString(phoneNumberIndex)
                }
            }
        }
        return null
    }

    private fun openAppByName(appName: String): Boolean {
        val searchName = appName.lowercase().trim()
        Log.d("VoiceAgent", "Searching for app: $searchName")
        
        // Step 1: Try Intent categories and common actions first
        when (searchName) {
            "calendar" -> {
                val calendarIntent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_APP_CALENDAR)
                }
                if (calendarIntent.resolveActivity(packageManager) != null) {
                    startActivity(calendarIntent)
                    return true
                }
            }
            "camera" -> {
                val cameraIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                if (cameraIntent.resolveActivity(packageManager) != null) {
                    startActivity(cameraIntent)
                    return true
                }
            }
            "contacts" -> {
                val contactsIntent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_APP_CONTACTS)
                }
                if (contactsIntent.resolveActivity(packageManager) != null) {
                    startActivity(contactsIntent)
                    return true
                }
            }
            "messages", "sms", "messaging" -> {
                val smsIntent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_APP_MESSAGING)
                }
                if (smsIntent.resolveActivity(packageManager) != null) {
                    startActivity(smsIntent)
                    return true
                }
            }
            "phone", "dialer", "call" -> {
                val dialerIntent = Intent(Intent.ACTION_DIAL)
                if (dialerIntent.resolveActivity(packageManager) != null) {
                    startActivity(dialerIntent)
                    return true
                }
            }
            "email", "mail" -> {
                val emailIntent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_APP_EMAIL)
                }
                if (emailIntent.resolveActivity(packageManager) != null) {
                    startActivity(emailIntent)
                    return true
                }
            }
            "browser", "chrome", "internet" -> {
                val browserIntent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_APP_BROWSER)
                }
                if (browserIntent.resolveActivity(packageManager) != null) {
                    startActivity(browserIntent)
                    return true
                }
            }
        }

        // Step 2: Get ALL installed apps and search through them
        try {
            val allApps = packageManager.getInstalledApplications(0)
            Log.d("VoiceAgent", "Found ${allApps.size} installed apps")
            
            // Create a list of apps with their names and package names
            val appList = mutableListOf<Pair<String, String>>()
            
            for (app in allApps) {
                try {
                    // Get the app name
                    val appLabel = packageManager.getApplicationLabel(app).toString().lowercase()
                    val packageName = app.packageName
                    
                    // Check if this app has a launcher intent (can be opened)
                    val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
                    if (launchIntent != null) {
                        appList.add(Pair(appLabel, packageName))
                    }
                } catch (e: Exception) {
                    // Skip apps that cause errors
                    continue
                }
            }
            
            Log.d("VoiceAgent", "Found ${appList.size} launchable apps")
            
            // Step 3: Search for exact matches first
            for ((appLabel, packageName) in appList) {
                if (appLabel == searchName) {
                    Log.d("VoiceAgent", "Exact match found: $appLabel -> $packageName")
                    val intent = packageManager.getLaunchIntentForPackage(packageName)
                    if (intent != null) {
                        startActivity(intent)
                        return true
                    }
                }
            }
            
            // Step 4: Search for partial matches (contains search term)
            for ((appLabel, packageName) in appList) {
                if (appLabel.contains(searchName)) {
                    Log.d("VoiceAgent", "Partial match found: $appLabel -> $packageName")
                    val intent = packageManager.getLaunchIntentForPackage(packageName)
                    if (intent != null) {
                        startActivity(intent)
                        return true
                    }
                }
            }
            
            // Step 5: Search by package name keywords (expanded list)
            val packageKeywords = mapOf(
                "gmail" to listOf("gmail", "google.android.gm", "mail", "email"),
                "whatsapp" to listOf("whatsapp", "whats"),
                "facebook" to listOf("facebook", "katana", "meta"),
                "instagram" to listOf("instagram", "insta"),
                "youtube" to listOf("youtube", "yt"),
                "chrome" to listOf("chrome", "browser", "com.android.chrome", "com.chrome", "google.android.browser"),
                "browser" to listOf("chrome", "browser", "firefox", "opera", "edge"),
                "maps" to listOf("maps", "google.android.apps.maps", "navigation"),
                "spotify" to listOf("spotify", "music"),
                "netflix" to listOf("netflix", "media"),
                "uber" to listOf("uber", "ubercab"),
                "telegram" to listOf("telegram", "tg"),
                "discord" to listOf("discord"),
                "zoom" to listOf("zoom", "meeting"),
                "tiktok" to listOf("tiktok", "musically", "bytedance"),
                "snapchat" to listOf("snapchat", "snap"),
                "twitter" to listOf("twitter", "x"),
                "linkedin" to listOf("linkedin"),
                "skype" to listOf("skype"),
                "slack" to listOf("slack"),
                "dropbox" to listOf("dropbox"),
                "drive" to listOf("drive", "docs", "google"),
                "photos" to listOf("photos", "gallery", "camera"),
                "calendar" to listOf("calendar", "cal"),
                "email" to listOf("email", "mail", "gmail"),
                "camera" to listOf("camera", "photo", "cam"),
                "calculator" to listOf("calculator", "calc"),
                "settings" to listOf("settings", "config")
            )
            
            packageKeywords[searchName]?.let { keywords ->
                for ((appLabel, packageName) in appList) {
                    for (keyword in keywords) {
                        if (packageName.lowercase().contains(keyword) || appLabel.contains(keyword)) {
                            Log.d("VoiceAgent", "Keyword match found: $appLabel -> $packageName")
                            val intent = packageManager.getLaunchIntentForPackage(packageName)
                            if (intent != null) {
                                startActivity(intent)
                                return true
                            }
                        }
                    }
                }
            }
            
            // Step 6: Fuzzy search - search for apps where search term appears anywhere
            for ((appLabel, packageName) in appList) {
                val words = searchName.split(" ")
                var matchCount = 0
                for (word in words) {
                    if (word.length > 2 && (appLabel.contains(word) || packageName.lowercase().contains(word))) {
                        matchCount++
                    }
                }
                if (matchCount > 0) {
                    Log.d("VoiceAgent", "Fuzzy match found: $appLabel -> $packageName")
                    val intent = packageManager.getLaunchIntentForPackage(packageName)
                    if (intent != null) {
                        startActivity(intent)
                        return true
                    }
                }
            }
            
        } catch (e: Exception) {
            Log.e("VoiceAgent", "Error searching apps: ${e.message}")
        }
        
        Log.d("VoiceAgent", "No app found for: $searchName")
        return false
    }
    
    private fun debugInstalledApps(searchTerm: String) {
        Log.d("VoiceAgent", "=== DEBUGGING APPS FOR: $searchTerm ===")
        try {
            val allApps = packageManager.getInstalledApplications(0)
            var foundCount = 0
            
            for (app in allApps) {
                try {
                    val launchIntent = packageManager.getLaunchIntentForPackage(app.packageName)
                    if (launchIntent != null) {
                        val appLabel = packageManager.getApplicationLabel(app).toString().lowercase()
                        
                        // Log apps that might match our search
                        if (appLabel.contains(searchTerm) || 
                            app.packageName.lowercase().contains(searchTerm) ||
                            searchTerm.contains(appLabel) ||
                            appLabel.contains("chrome") || 
                            appLabel.contains("browser") ||
                            appLabel.contains("gmail") ||
                            appLabel.contains("whatsapp")) {
                            
                            Log.d("VoiceAgent", "FOUND POTENTIAL MATCH: '$appLabel' -> ${app.packageName}")
                            foundCount++
                        }
                    }
                } catch (e: Exception) {
                    // Skip
                }
            }
            Log.d("VoiceAgent", "Found $foundCount potential matches for '$searchTerm'")
        } catch (e: Exception) {
            Log.e("VoiceAgent", "Error debugging apps: ${e.message}")
        }
        Log.d("VoiceAgent", "=== END DEBUG ===")
    }

    private fun showError(msg: String) {
        runOnUiThread { Toast.makeText(this, "Error: $msg", Toast.LENGTH_LONG).show() }
    }
    private fun showSuccess(msg: String) {
        runOnUiThread { Toast.makeText(this, msg, Toast.LENGTH_SHORT).show() }
    }

    // Simple hold-to-record methods
    private fun startRecording() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Audio permission required", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            isRecording = true
            
            // Create temp audio file
            val outputDir = File(externalCacheDir, "audio")
            if (!outputDir.exists()) outputDir.mkdirs()
            audioFile = File.createTempFile("voice_cmd", ".aac", outputDir)
            
            // Initialize MediaRecorder
            recorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.AAC_ADTS)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(audioFile!!.absolutePath)
                prepare()
                start()
            }
            
            runOnUiThread {
                recordButton.text = "Recording..."
                statusText.text = "Speak your command"
            }
            
        } catch (e: Exception) {
            showError("Failed to start recording: ${e.message}")
        }
    }

    private fun stopRecording() {
        if (!isRecording) return
        
        try {
            isRecording = false
            
            recorder?.apply {
                stop()
                release()
            }
            recorder = null
            
            runOnUiThread {
                recordButton.text = "Hold to Record"
                statusText.text = "Processing..."
            }
            
            // Send the recorded audio to server
            sendAudioToServer(audioFile!!)
            
        } catch (e: Exception) {
            showError("Failed to stop recording: ${e.message}")
        }
    }

    private fun initializeTTS() {
        textToSpeech = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                isTTSInitialized = true
                Log.d("VoiceAgent", "TTS initialized successfully")
            } else {
                Log.e("VoiceAgent", "TTS initialization failed")
                showError("Text-to-speech initialization failed")
            }
        }
    }

    private fun speakText(text: String) {
        if (isTTSInitialized) {
            Log.d("VoiceAgent", "Speaking: $text")
            textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
            showSuccess("Speaking: ${text.take(50)}${if (text.length > 50) "..." else ""}")
        } else {
            Log.e("VoiceAgent", "TTS not initialized")
            showError("Text-to-speech not ready")
        }
    }
}
