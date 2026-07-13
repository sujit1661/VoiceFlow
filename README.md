# 🎙️ Flow — AI Voice-to-Text Assistant

> **Don't type, just speak.** Flow is an AI-powered voice dictation assistant that transforms natural speech into polished, context-aware writing. Powered by **Groq Whisper Large v3** for ultra-fast speech recognition and **LLaMA 3.1** for intelligent text refinement, Flow lets you write anywhere using only your voice.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Electron](https://img.shields.io/badge/Electron-Desktop_App-47848F?logo=electron)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-AI-orange)
![Whisper](https://img.shields.io/badge/Whisper-Large_v3-red)
![License](https://img.shields.io/badge/License-MIT-green)
---

# 📖 Overview

Flow is a cross-platform AI-powered voice dictation application designed to replace typing with natural speech.

With a single keyboard shortcut, users can record their voice, convert speech into text using **Groq Whisper Large v3**, enhance the transcript using **LLaMA 3.1**, and automatically insert the polished text into any application.

Unlike traditional speech-to-text software, Flow understands context and rewrites spoken language into clean, readable content suitable for emails, documents, chats, notes, or technical writing.

Whether you're writing an email, documenting code, taking notes, or chatting with teammates, Flow makes voice-based writing fast, natural, and effortless.

---

# 🎯 Motivation

Typing can interrupt creativity and reduce productivity, especially during brainstorming, meetings, or coding sessions.

Traditional speech recognition tools simply transcribe words without improving readability, often leaving users with filler words, grammar mistakes, and poorly structured text.

Flow was built to solve these challenges by combining real-time speech recognition with AI-powered language refinement.

The application enables users to:

- Speak naturally
- Receive accurate transcription
- Automatically remove filler words
- Correct grammar
- Improve sentence structure
- Format text for different writing contexts
- Type directly into any application

Flow transforms voice into polished writing with minimal effort.

---

# ✨ Features

## 🎤 Voice Recording

- One-key voice recording
- Hold-to-record functionality
- Lightweight recording interface
- Cross-platform support
- Low-latency audio capture

---

## ⚡ Lightning-Fast Transcription

Powered by **Groq Whisper Large v3**

Features include:

- High transcription accuracy
- Fast speech recognition
- Multi-language support
- Automatic punctuation
- Robust handling of natural speech

---

## 🤖 AI Text Enhancement

Powered by **LLaMA 3.1**

Flow automatically:

- Removes filler words
- Fixes grammar
- Improves sentence structure
- Corrects punctuation
- Enhances readability
- Rewrites awkward phrases
- Preserves the original meaning

---

## 📝 Context-Aware Writing

Flow adapts the output based on where the text will be used.

Available writing modes:

- General Writing
- Professional Emails
- Documentation
- Personal Notes
- Chat Messages
- Technical Documentation

---

## ⌨️ Global Typing

Flow can automatically type generated text into any application.

Supported applications include:

- Gmail
- Outlook
- Slack
- Discord
- VS Code
- Cursor
- Notion
- Microsoft Word
- Google Docs
- Chrome
- Any text input field

---

## 🌐 FastAPI Backend

Includes a production-ready backend with:

- REST APIs
- WebSocket streaming
- Audio upload
- AI processing
- Health monitoring

---

## 🔄 Real-Time Streaming

Supports WebSocket streaming for:

- Live AI responses
- Token-by-token output
- Reduced latency
- Better user experience

---

# 🏛️ System Architecture

```text
                     User
                       │
                       ▼
             Hold Ctrl to Record
                       │
                       ▼
              Audio Recording
                       │
                       ▼
        Groq Whisper Large v3
          (Speech-to-Text)
                       │
                       ▼
          Raw Transcript
                       │
                       ▼
          LLaMA 3.1 Instant
        (Grammar + Polishing)
                       │
                       ▼
        Clean Final Output
                       │
                       ▼
     Auto Type Into Any Application
```

---

# 🎙️ Voice Processing Pipeline

Flow follows a multi-stage AI pipeline.

```text
Microphone Input
        │
        ▼
Audio Recording
        │
        ▼
Whisper Large v3
        │
        ▼
Raw Transcript
        │
        ▼
LLaMA 3.1
        │
        ▼
Grammar Correction
        │
        ▼
Context Formatting
        │
        ▼
Polished Text
        │
        ▼
Automatic Typing
```

---

# 🚀 Key Features

Flow provides a complete AI-powered writing workflow.

✅ Voice Recording

✅ Speech Recognition

✅ Grammar Correction

✅ AI Text Rewriting

✅ Context-Aware Writing

✅ Auto Typing

✅ FastAPI Backend

✅ WebSocket Streaming

✅ Global Hotkeys

✅ Cross-Platform Support

---

# 🛠️ Technology Stack

| Category | Technologies |
|-----------|-------------|
| Programming Language | Python, JavaScript |
| Desktop Framework | Electron |
| Backend | FastAPI |
| ASGI Server | Uvicorn |
| Speech Recognition | Groq Whisper Large v3 |
| AI Text Polishing | Groq LLaMA 3.1 8B Instant |
| Frontend | HTML, CSS, JavaScript |
| Styling | Tailwind CSS |
| Desktop Integration | Electron IPC |
| Audio Recording | MediaRecorder, PyAudio |
| Global Hotkeys | Electron GlobalShortcut / pynput |
| Auto Typing | pyautogui |
| Environment | python-dotenv |

---

# 📂 Project Structure

```text
flow/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
│
├──electron
|   ├── main.js
|   ├── overlay.html
|   ├── package.json
|
├── frontend/
│   ├── index.html
│   ├── app.html
│   ├── features.html
│   ├── use-cases.html
│   ├── about.html
│   ├── contact.html
│   ├── css/
│   └── js/
│
├── hotkey_service/
│   ├── service.py
│   └── requirements.txt
│
├── Procfile
├── start.bat
├── README.md
└── .gitignore
```

---

# 🌟 Why Flow?

Unlike traditional dictation software, Flow combines speech recognition with AI language refinement.

Instead of producing raw transcripts, Flow generates polished, readable content ready to use immediately.

### Traditional Speech Recognition

- Raw transcription
- Grammar mistakes
- Filler words
- Manual editing
- Limited formatting

### Flow

- Accurate transcription
- AI-enhanced writing
- Grammar correction
- Context-aware formatting
- Instant typing anywhere
- Professional-quality output

---

# 🎯 Use Cases

Flow is useful for a wide range of scenarios.

### 💼 Professional Work

- Emails
- Reports
- Documentation
- Meeting notes

---

### 👨‍💻 Software Development

- Code comments
- Pull request descriptions
- Documentation
- Commit messages

---

### 🎓 Education

- Lecture notes
- Assignments
- Study summaries
- Research writing

---

### ✍️ Content Creation

- Blog writing
- Articles
- Social media posts
- Script writing

---

### 💬 Communication

- Slack
- Discord
- Microsoft Teams
- WhatsApp Web
- Telegram Desktop

---
---

# ⚙️ Getting Started

Follow the steps below to run Flow locally.

---

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/sujit1661/Flow.git

cd Flow
```

---

## 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
```

### Activate the Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

---

## 3️⃣ Install Backend Dependencies

```bash
cd backend

pip install -r requirements.txt
```

Required packages include:

- FastAPI
- Uvicorn
- Groq SDK
- python-dotenv
- websockets
- python-multipart

---

## 4️⃣ Configure Environment Variables

Create a `.env` file inside the **backend** directory.

```env
GROQ_API_KEY=your_groq_api_key
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:8000
```

You can get a free API key from:

https://console.groq.com

---

## 5️⃣ Run the Backend

```bash
uvicorn main:app --reload
```

Backend URL

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

---

## 6️⃣ Run the Frontend

Simply open:

```
frontend/index.html
```

or

```
http://127.0.0.1:8000
```

if served through FastAPI.

---

# 🚀 Application Workflow

Flow follows a simple but powerful AI pipeline.

```text
Hold Ctrl
     │
     ▼
Voice Recording
     │
     ▼
Whisper Large v3
     │
     ▼
Raw Transcript
     │
     ▼
LLaMA 3.1
     │
     ▼
Grammar Correction
     │
     ▼
Context Formatting
     │
     ▼
Auto Typing
```

---

# 🌐 REST API

Flow exposes REST endpoints for integration with web applications, desktop clients, and mobile apps.

---

## Health Check

### GET `/health`

Checks whether the backend is running.

### Response

```json
{
    "status": "healthy"
}
```

---

## Speech Transcription

### POST `/api/transcribe`

Uploads an audio recording for speech recognition.

### Request

| Field | Type |
|--------|------|
| audio | Audio File |

Supported formats

- WAV
- MP3
- WEBM
- M4A

### Response

```json
{
    "success": true,
    "text": "Hello everyone",
    "raw": "hello everyone"
}
```

---

## AI Text Polishing

### POST `/api/polish`

Improves grammar, punctuation, and writing quality.

### Request

```json
{
    "text":"hello everyone today i want discuss project",

    "context":"email"
}
```

### Response

```json
{
    "success":true,

    "polished":"Hello everyone, today I would like to discuss the project."
}
```

---

# ⚡ WebSocket Streaming

### Endpoint

```
/ws/stream
```

Streaming enables token-by-token AI responses.

### Client Request

```json
{
    "text":"raw transcript",

    "context":"general"
}
```

### Server Events

```json
{
    "type":"start"
}
```

```json
{
    "type":"token",

    "token":"Hello"
}
```

```json
{
    "type":"done",

    "full_text":"Hello everyone."
}
```

---

# 📝 Writing Modes

Flow automatically adapts writing style based on context.

| Mode | Description |
|------|-------------|
| general | Everyday writing |
| email | Professional emails |
| document | Reports and articles |
| note | Quick notes |
| chat | Casual conversations |
| code | Technical writing |

---

# ⌨️ Global Hotkey Service

Flow includes a background service that allows voice dictation in any application.

---

## Install

```bash
cd hotkey_service

pip install -r requirements.txt
```

---

## Run

```bash
python service.py
```

---

## Hotkeys

| Shortcut | Action |
|----------|--------|
| Hold Ctrl | Start Recording |
| Release Ctrl | Stop Recording |
| ESC | Exit Service |

---

# 🔄 Background Workflow

```text
Ctrl Pressed
      │
      ▼
Recording Started
      │
      ▼
Ctrl Released
      │
      ▼
Upload Audio
      │
      ▼
Speech Recognition
      │
      ▼
AI Text Enhancement
      │
      ▼
Automatic Typing
```

---

# 🌍 Supported Applications

Flow works with virtually any application that accepts keyboard input.

Examples include:

- Gmail
- Google Docs
- Microsoft Word
- Notion
- Slack
- Discord
- VS Code
- Cursor
- PyCharm
- IntelliJ IDEA
- WhatsApp Web
- Telegram Desktop
- Chrome
- Firefox
- Edge
- many more 

---

# 🚀 Deployment

Flow is production-ready and can be deployed to:

- Railway
- Render
- FastAPI Cloud
- Heroku
- VPS
- Docker

---

## Required Environment Variables

```env
GROQ_API_KEY=your_key

ENVIRONMENT=production

ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

# 💬 Example Usage

## Email

```
Write an email thanking the client for attending today's meeting.
```

---

## Notes

```
Take notes from today's lecture.
```

---

## Documentation

```
Explain how Retrieval-Augmented Generation works.
```

---

## Chat

```
Reply politely to this Slack message.
```

---

## Programming

```
Generate documentation for this Python function.
```

---

# 📊 Performance

Powered by Groq's ultra-fast inference.

Typical processing time:

| Stage | Average Time |
|--------|-------------:|
| Audio Upload | < 100 ms |
| Whisper Transcription | ~300–800 ms |
| AI Text Polishing | ~200–500 ms |
| Total Response | ~1 second (varies by audio length) |

> Actual performance depends on audio duration, network latency, and model availability.

---

# 🔒 Security & Privacy

Flow is designed with user privacy and security in mind.

### Security Features

- API keys stored securely using environment variables
- No hardcoded credentials
- Secure REST API communication
- WebSocket support for real-time responses
- CORS configuration for production deployments

### Privacy

- Audio is processed only when the user records.
- No permanent storage of voice recordings.
- Transcriptions exist only for processing unless explicitly saved.
- API keys remain on the server and are never exposed to the frontend.

---

# ⚠️ Limitations

Current limitations include:

- Requires an active internet connection
- Depends on Groq API availability
- Background hotkey service must be running
- Auto typing requires accessibility permissions on some operating systems
- Performance may vary depending on microphone quality

---

# 🛣️ Roadmap

### Version 1.0

- Voice Recording
- AI Transcription
- AI Text Polishing
- Global Auto Typing
- FastAPI Backend
- Electron Desktop Application

---

### Version 1.5

- Voice Commands
- Custom Keyboard Shortcuts
- Dark & Light Themes
- Clipboard Integration
- Offline History

---

### Version 2.0

- Multiple AI Providers
- Translation Support
- Speaker Identification
- Voice Profiles
- Custom Prompt Templates

---

### Version 3.0

- Offline Speech Recognition
- Offline LLM Support
- AI Meeting Assistant
- Calendar Integration
- Email Automation
- Plugin System

---

# 🤝 Contributing

Contributions are always welcome.

To contribute:

1. Fork the repository.

2. Create a new branch.

```bash
git checkout -b feature-name
```

3. Commit your changes.

```bash
git commit -m "Add new feature"
```

4. Push your branch.

```bash
git push origin feature-name
```

5. Open a Pull Request.

---

# 🐞 Troubleshooting

### Backend won't start

Make sure all backend dependencies are installed.

```bash
pip install -r requirements.txt
```

---

### Invalid Groq API Key

Verify that your `.env` file contains a valid API key.

```env
GROQ_API_KEY=your_api_key
```

---

### Microphone not detected

- Check microphone permissions.
- Ensure another application is not using the microphone.
- Restart the application after granting permissions.

---

### Auto Typing doesn't work

Some operating systems require accessibility permissions.

**Windows**

Run the application as Administrator if necessary.

**macOS**

Grant Accessibility permissions under:

```
System Settings

↓

Privacy & Security

↓

Accessibility
```

**Linux**

Install PortAudio:

```bash
sudo apt install portaudio19-dev
```

---

### Electron application doesn't launch

Install frontend dependencies.

```bash
cd electron

npm install

npm start
```

---

# 📈 Future Enhancements

Planned improvements include:

- AI voice commands
- Wake-word detection
- Multiple language transcription
- Real-time translation
- AI writing styles
- Custom AI prompts
- Cloud synchronization
- User accounts
- Conversation history
- Mobile application
- Browser extension
- Desktop notifications
- Automatic updates
- Analytics dashboard

---

# 👨‍💻 Author

**Sujit Sadalage**

**B.Tech in Artificial Intelligence & Data Science (2022–2026)**

Aspiring **AI Engineer | Backend Developer | Python Developer**

- GitHub: https://github.com/sujit1661

---

# ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub.

Your support helps improve the project and encourages future development.

---

# 📄 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project for personal and commercial purposes under the terms of the license.

---

# 🙏 Acknowledgements

Special thanks to the amazing open-source projects and communities that made Flow possible.

- Groq
- OpenAI Whisper
- FastAPI
- Electron
- Tailwind CSS
- Uvicorn
- Python
- JavaScript

---

> **Flow** — Speak naturally. Write intelligently. 🚀---
