# June - Voice AI Agent

A sophisticated voice-controlled AI assistant that combines speech recognition, natural language processing, and Android automation to execute voice commands on your phone.

## 🎯 Features

### Voice Commands
- **App Control**: "Open Gmail", "Open WhatsApp", "Open any app"
- **Phone Calls**: "Call John", "Dial 123-456-7890"
- **SMS Messages**: "Send text 'Hello' to Mom"
- **Universal App Detection**: Works with ANY installed app

### Technical Architecture
- **Server**: Python FastAPI with Whisper speech recognition
- **AI Processing**: Anthropic Claude API for natural language understanding
- **Client**: Android app with hold-to-record interface
- **Communication**: Local network REST API

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Android App   │───▶│  Python Server   │───▶│   Claude API    │
│  (Audio Record) │    │  (Whisper + API) │    │ (NLP Processing)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐             │
         │              │  Audio Analysis │             │
         │              │  - Whisper STT  │             │
         │              │  - FFmpeg       │             │
         │              └─────────────────┘             │
         │                                               │
         └──────────────── JSON Response ◀──────────────┘
                         (Action Commands)
```

## 🚀 Quick Start

### Prerequisites
- Windows PC with Python 3.8+
- Android phone
- Both devices on same WiFi network
- Anthropic Claude API key

### Server Setup
1. **Clone and Setup**:
   ```bash
   git clone https://github.com/killjay/June.git
   cd June
   ```

2. **Install Dependencies**:
   ```bash
   cd server
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure API**:
   - Get Anthropic Claude API key
   - Update `server.py` with your API key

4. **Install FFmpeg**:
   ```bash
   winget install FFmpeg
   ```

5. **Run Server**:
   ```bash
   python server.py
   ```

### Android Setup
1. **Build APK**:
   ```bash
   cd android-app
   ./gradlew assembleDebug
   ```

2. **Install on Phone**:
   - Enable Developer Options
   - Install `app-debug.apk`

3. **Configure Network**:
   - Update IP address in `MainActivity.kt` to your PC's IP
   - Ensure both devices on same WiFi

## 📱 Usage

1. **Launch App**: Open "Voice AI Agent" on Android
2. **Hold to Record**: Press and hold the button
3. **Speak Command**: Say your command clearly
4. **Release**: Let go when done speaking
5. **Action Executed**: Command is processed and executed

### Example Commands
```
"Open Gmail"                    → Opens Gmail app
"Call John Smith"              → Calls contact John Smith
"Send text 'Hello' to Mom"     → Opens SMS with message
"Open camera"                  → Opens camera app
"Dial 911"                     → Opens dialer with 911
```

## 🔧 Configuration

### Server Configuration
- **Port**: Default 5005 (configurable in `server.py`)
- **Host**: Binds to all interfaces (0.0.0.0)
- **Model**: Whisper "small" (244M parameters)

### Android Configuration
- **Server IP**: Update `SERVER_IP` in `MainActivity.kt`
- **Audio Format**: AAC encoding for compatibility
- **Permissions**: Microphone, Phone, Contacts, SMS

## 🛠️ Development

### Project Structure
```
June/
├── server/
│   ├── server.py           # FastAPI server with Whisper
│   ├── requirements.txt    # Python dependencies
│   └── .venv/             # Virtual environment
├── android-app/
│   ├── app/src/main/java/com/voiceaiagent/
│   │   └── MainActivity.kt # Main Android app logic
│   ├── build.gradle       # Android build config
│   └── app/build.gradle   # App-specific config
└── README.md
```

### Key Components

#### Server (`server.py`)
- **Whisper Integration**: Speech-to-text with English language forcing
- **Claude API**: Natural language processing for intent recognition
- **FastAPI**: REST API endpoint for audio processing
- **FFmpeg**: Audio format handling and conversion

#### Android App (`MainActivity.kt`)
- **Audio Recording**: MediaRecorder with AAC format
- **Universal App Detection**: Scans all installed apps
- **Contact Integration**: Phone and SMS contact lookup
- **Network Communication**: OkHttp for server requests

## 🎯 Voice Command Processing

1. **Audio Capture**: Android MediaRecorder → WAV/AAC file
2. **Network Transfer**: HTTP POST to Python server
3. **Speech Recognition**: Whisper transcription (English)
4. **NLP Processing**: Claude API intent parsing
5. **Action Execution**: Android Intent system

### Response Format
```json
{
  "action": "open_app",
  "app": "gmail"
}

{
  "action": "call", 
  "contact": "John Smith"
}

{
  "action": "send_sms",
  "contact": "Mom",
  "message": "Hello"
}
```

## 🔒 Security & Privacy

- **Local Processing**: Speech recognition happens on local network
- **No Cloud Storage**: Audio files are temporary and deleted
- **API Key Security**: Store Claude API key securely
- **Network Security**: Use on trusted WiFi networks only

## 🐛 Troubleshooting

### Common Issues

**"App not found" errors**:
- Check app installation and spelling
- Review Android logs for detailed app search results
- Verify app has launcher intent

**Audio transcription failures**:
- Ensure FFmpeg is in system PATH
- Check microphone permissions
- Verify network connectivity

**Server connection issues**:
- Confirm IP address configuration
- Check firewall settings
- Verify both devices on same network

### Debug Logging
- **Server**: Check console for Whisper transcription results
- **Android**: Use `adb logcat | grep VoiceAgent` for detailed logs

## 🚧 Future Enhancements

- **Wake Word Detection**: "Hey June" activation
- **Conversation Context**: Multi-turn conversations
- **Smart Home Integration**: IoT device control
- **Offline Mode**: Local speech recognition
- **Multiple Languages**: Beyond English support

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For issues and questions:
- Open GitHub issue
- Check troubleshooting section
- Review server logs for errors

---

**Built with ❤️ for voice automation enthusiasts**
