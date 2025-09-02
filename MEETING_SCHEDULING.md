# AI Agent Meeting Scheduling Feature

June can now act as an intelligent AI agent to automatically schedule meetings when requested!

## 🤖 How It Works

When you ask June to schedule a meeting, it:

1. **Understands Natural Language**: Uses GPT-OSS model (Hugging Face) to extract meeting details from your voice command
2. **Asks for Clarification**: If critical information is missing, June will ask you to provide it
3. **Creates Calendar Events**: Automatically adds the meeting to your Google Calendar
4. **Sends Invitations**: Can send email invites to attendees if email addresses are provided

## 🎤 Voice Commands Examples

### Complete Requests
- *"June, schedule a meeting with John tomorrow at 2pm"*
- *"Schedule a 30 minute call with Sarah for Friday"*
- *"Set up a team meeting next week"*
- *"Book a meeting with alex@company.com for tomorrow at 10am"*

### Partial Requests (June will ask for clarification)
- *"Schedule a meeting with John"* → June asks: "When would you like to schedule it?"
- *"Set up a meeting for tomorrow"* → June asks: "Who would you like to meet with?"

## 🧠 AI Intelligence Features

### **Smart Detail Extraction**
June understands various ways of expressing meeting details:
- **Time**: "tomorrow", "next week", "Friday at 2pm", "Monday morning"
- **Duration**: "30 minute call", "hour-long meeting", "quick 15 minute check-in"
- **Attendees**: Names, email addresses, or groups like "team meeting"

### **Missing Information Handling**
If you don't provide enough details, June intelligently asks for the missing information:
- Missing attendee: *"I need to know who you want to meet with"*
- Missing time: *"When would you like to schedule it?"*

### **Smart Defaults**
- **Default duration**: 60 minutes if not specified
- **Default time**: 2:00 PM if only date is provided
- **Auto-scheduling**: Finds the next occurrence of requested day/time

## 🔧 Technical Implementation

### **Server Architecture**
1. **Main AI Server** (`server.py`):
   - Detects meeting scheduling requests with keywords like "schedule meeting", "book meeting"
   - Uses GPT-OSS model (Hugging Face) to extract meeting details from natural language
   - Handles missing information and user clarifications
   - Converts relative times ("tomorrow", "next week") to specific dates/times

2. **MCP Server** (`mcp_server.py`):
   - New `/calendar/create_event` endpoint for creating calendar events
   - Integrates with Google Calendar API
   - Handles authentication and permissions
   - Sends email invitations to attendees

### **Android App Integration**
- No changes needed to the Android app!
- Uses existing "speak" action to provide feedback to user
- Meeting confirmations are spoken through the TTS system

## 📅 Calendar Integration

### **Google Calendar Features**
- ✅ Creates events in user's primary Google Calendar
- ✅ Sets proper start and end times with timezone support
- ✅ Adds meeting title, description, and location
- ✅ Sends email invitations to attendees automatically
- ✅ Provides calendar link for easy access

### **Event Details**
```json
{
  "title": "Meeting with John",
  "start_time": "2025-08-30T14:00:00",
  "end_time": "2025-08-30T15:00:00", 
  "description": "Scheduled via June AI Assistant",
  "attendees": ["john@company.com"],
  "location": "Optional location"
}
```

## 🎯 Use Cases

### **Business Scenarios**
- *"Schedule a client call with Mike for Monday at 3pm"*
- *"Set up a project review meeting next Tuesday"*
- *"Book a 15 minute standup for tomorrow morning"*

### **Personal Scenarios**
- *"Schedule coffee with Sarah this Friday"*
- *"Set up a family dinner for Sunday at 6pm"*
- *"Book a doctor appointment for next week"*

### **Team Coordination**
- *"Schedule an all-hands meeting for next Monday"*
- *"Set up a weekly team sync every Thursday"*
- *"Book the conference room for our presentation tomorrow"*

## 🚀 Future Enhancements

### **Planned Features**
- **Recurring Meetings**: "Schedule a weekly team meeting"
- **Meeting Room Booking**: Integration with office calendar systems
- **Time Zone Handling**: "Schedule with John in London time"
- **Availability Checking**: "Find a time when everyone is free"
- **Meeting Reminders**: "Remind me 15 minutes before the meeting"

### **Advanced AI Capabilities**
- **Context Awareness**: Remember previous meetings with the same person
- **Smart Scheduling**: Suggest optimal meeting times based on calendar patterns
- **Meeting Preparation**: Automatically add agenda items or documents
- **Follow-up Actions**: Schedule follow-up meetings or reminders

## 🔒 Privacy & Security

- **Local Processing**: Meeting details are processed locally before sending to calendar
- **Google Authentication**: Secure OAuth2 authentication with Google Calendar
- **No Data Storage**: Meeting requests are not stored or logged permanently
- **User Control**: User can review and modify meetings in their Google Calendar

---

**June is now a true AI agent that can take action on your behalf - starting with intelligent meeting scheduling!**

This feature demonstrates how voice AI can go beyond simple commands to become a proactive assistant that understands context, asks clarifying questions, and takes real actions in the digital world.
