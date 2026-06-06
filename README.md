<div align="center">
  <h1>🤖 JARVIS</h1>
  <p><strong>A Next-Generation Autonomous Voice Assistant & Multi-Agent Orchestrator</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
  [![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange.svg)](https://github.com/joaomdmoura/crewAI)
  [![Gemini](https://img.shields.io/badge/Google-Gemini%202.5%20Pro-green.svg)](https://deepmind.google/technologies/gemini/)
  [![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
</div>

<br>

JARVIS is not just a voice assistant; it is an intelligent desktop orchestrator capable of reasoning, web browsing, hardware automation, and operating an entire internal software engineering department autonomously.

Built entirely in Python, JARVIS integrates large language models (LLMs), persistent vector memory, computer vision, and complex task-delegation architectures into a unified voice interface.

---

## 🌟 Core Architecture

JARVIS is divided into several sophisticated modules that handle distinct functionalities:

*   **`jarvis.py` (The CEO):** The master orchestrator that listens to voice commands, analyzes intent, and routes tasks to the appropriate sub-module or agent.
*   **`ai_module.py` (The Brain):** Handles direct conversational interactions and reasoning via Google's Gemini 2.5 Pro models.
*   **`agent_module.py` (The Workforce):** Manages specialized agents (Memory, Document Generation, Video/Audio Recording, News).
*   **`vision_module.py` (The Eyes):** Interfaces with your local camera and screen buffers to provide real-time vision capabilities.
*   **`automation_module.py` (The Hands):** Automates the Windows OS, utilizing `pyautogui` and `win32com` to control tabs, media, applications, and hardware settings.

---

## 🔥 Key Features

### 🏢 Autonomous Software Factory (CrewAI Integration)
By saying *"Jarvis, build a project"*, JARVIS boots up an isolated `uv` subprocess containing a **CrewAI Multi-Agent Factory**. 
*   A **Product Manager** agent searches the live web for 2026 design trends and writes a Software Requirement Specification (SRS).
*   A **Senior Software Engineer** agent autonomously writes the Python/HTML/CSS code files directly to your hard drive.
*   A **QA Reviewer** agent audits the code for bugs.
JARVIS handles the orchestration, providing terminal feedback, and opens the final generated project folder when the agents finish compiling.

### 🌐 Live Web Search & Image Retrieval
JARVIS is hooked directly into the DuckDuckGo Search API (`ddgs`). He can bypass LLM hallucinations by securely browsing the web for live, up-to-date data, summarizing top articles, and fetching high-definition images natively to your desktop.

### 🧠 Persistent Vector Memory
Utilizing **ChromaDB**, JARVIS features a dedicated long-term memory module. When instructed to *"Remember that..."*, JARVIS stores the information via vector embeddings, allowing for semantic recall across different user sessions.

### 🎥 Multi-Modal Recording Suite
JARVIS features a background-threaded `RecorderAgent` capable of seamlessly capturing:
*   Real-time Screen Recording.
*   Webcam Video Recording.
*   Microphone Audio Recording.

### 📧 Automated Communications
JARVIS has deep integration into communication channels:
*   **Email:** Can autonomously draft emails, request attachments via secure UI prompts, and dispatch emails via SMTP.
*   **WhatsApp:** Integrates seamlessly into the native Windows WhatsApp application to dispatch messages using URI protocols.

### 📝 Dynamic Document Generation
JARVIS can research a topic from memory and output beautifully formatted PDF reports using `FPDF` (featuring a custom dark-mode, neon-styled document template) or standard Word Documents (`.docx`).

---

## 🛠️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/jagadeesvarrao-design/JARVIS.git
   cd JARVIS
   ```

2. **Install Dependencies:**
   Ensure you are using Python 3.10+ (Recommended: 3.12+).
   ```bash
   pip install -r requirments.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your API Keys:
   ```env
   GEMINI_API_KEY=your_google_gemini_key_here
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   ```

4. **Launch JARVIS:**
   Run the batch file for standard boot sequence:
   ```bash
   wakeup_jarvis.bat
   ```
   Or run the Python script directly:
   ```bash
   python jarvis.py
   ```

---

## 🚀 Future Roadmap
- [ ] Integration with advanced Home Assistant IoT devices.
- [ ] Native Streamlit UI dashboard for real-time memory visualization.
- [ ] Multi-threaded LLM streaming for lower latency responses.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
