# Voice AI Agent - Testing Guide

## Prerequisites
- Android Studio installed
- Android device with USB debugging enabled
- Both PC and Android device on the same WiFi network

## Server Setup (COMPLETED)
✅ The server is now running on your PC at `http://192.168.1.120:5005`
✅ All dependencies are installed
✅ Server is listening for voice commands

## Android App Setup

1. **Open Android Studio**
   - Open the folder: `C:\Users\inand\OneDrive\Desktop\APPS\Prototype\Voice AI Agent\android-app`

2. **Build the Project**
   ✅ **Fixed**: Gradle build configuration is now complete
   - Let Gradle sync and build the project
   - The Gradle wrapper will download automatically
   - All dependencies and plugins are properly configured

3. **Connect Your Android Device**
   - Enable Developer Options and USB Debugging
   - Connect via USB cable
   - Accept the debugging prompt on your device

4. **Install and Run the App**
   - Click "Run" in Android Studio
   - Select your connected device
   - The app will install and launch

## Testing the Voice AI Agent

1. **Grant Permissions**
   - When the app launches, grant all requested permissions:
     - Microphone access (for recording)
     - Phone access (for making calls)
     - SMS access (for sending messages)
     - Contacts access (for looking up contacts)

2. **Test Voice Commands**
   - Hold down the "Hold to Record" button
   - Speak clearly: "June, call mom" or "June, open WhatsApp"
   - Release the button
   - The app will:
     - Send your audio to the server
     - Server transcribes with Whisper
     - Server sends to Claude AI for intent parsing
     - App receives action and executes it
     - Shows success/error notification

3. **Example Commands to Try**
   - "June, call mom"
   - "June, send SMS to John saying hello"
   - "June, open WhatsApp"
   - "June, open camera"

## Troubleshooting

### If the app can't connect to the server:
- Ensure both devices are on the same WiFi
- Try opening `http://192.168.1.120:5005/docs` in your phone's browser
- Check if Windows Firewall is blocking the connection

### If permissions are denied:
- Go to Settings > Apps > Voice AI Agent > Permissions
- Enable all required permissions manually

### If voice recognition isn't working:
- Speak clearly and close to the phone
- Make sure to say "June" to activate the command
- Check the server terminal for error messages

## Current Server Status
🟢 Server running at: http://192.168.1.120:5005
🟢 Whisper model loaded
🟢 Claude API configured
🟢 Ready to receive voice commands

Your Voice AI Agent is now ready for testing!
