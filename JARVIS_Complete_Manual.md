# 🧠 JARVIS: Complete System Capabilities & Reference Manual

Welcome, Sir. This manual provides an exhaustive, feature-by-feature reference of the **JARVIS** Desktop Assistant. It documents every single command, system control, dynamic skill, background daemon, and automation tool built into the codebase, along with exact command triggers and syntax.

---

## 🛠️ System Architecture & Engine Core

JARVIS is built on a modular Python architecture designed for real-time speech processing, vision analysis, system automation, and agentic workflows:

- **AI Brain ([ai_module.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/ai_module.py))**: Powered primarily by **Gemini 3.5 Flash** (via a rotating API key pool to prevent rate limits), with **Gemini 2.5 Flash-Lite** as a legacy fallback, and local **Llama 3 (via Ollama)** for complete offline operation.
- **Dynamic Skills Loader**: Modulizes the codebase by dynamically scanning and importing scripts from the [skills/](file:///C:/Users/DELL/OneDrive/Desktop/assistent/skills) folder on startup.
- **Multitasking Engine**: Background threads manage voice synthesis (Edge TTS/pyttsx3), proactive screen monitoring, and concurrent multi-agent tasks.

---

## 📡 Complete Capabilities & Triggers Matrix

JARVIS listens for spoken inputs (via Google Speech Recognition with Silero VAD) or typed commands entered silently through the PyQt5 Console Dock.

---

### 1. System Wake, Standby & Shutdown Controls

Controls the operating state, volume, and shutdown protocols of JARVIS.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Wake Up Word** | Plays a high-pitched chime, logs status, and puts JARVIS in active listening mode. | `"jarvis"` (spoken in standby) |
| **Hard Shutdown** | Safely records shutdown statistics to disk and terminates the JARVIS process instantly. | `"exit"`, `"quit"` |
| **PC Volume Up** | Turns up the host machine's master system volume by 5% increments. | `"volume up"` |
| **PC Volume Down** | Turns down the host machine's master system volume by 5% increments. | `"volume down"` |
| **PC Mute** | Mutes the host machine's master system volume. | `"mute"` |
| **PC Unmute** | Restores the host machine's master system volume. | `"unmute"` |

---

### 2. Audio Briefing & News Anchor

Compiles real-time briefings from the secure network and reads them in a human-like voice.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Morning Briefing** | Triggers automatically on first daily boot. States time, power status, searches DDG for AI news, compiles a 4-6 sentence summary, and speaks it. | `"morning briefing"`, `"start briefing"` |
| **Compile Latest Briefing** | Force-compiles and reads a fresh briefing of AI news headlines. | `"tell me the briefing"` |
| **Resume Briefing** | Resumes a previously paused briefing from the exact sentence where it was interrupted. | `"resume briefing"`, `"continue briefing"` |
| **Vocal Interrupt** | Instantly silences SAPI/Edge-TTS voice playback, pauses the briefing progress, and returns to standby. | Speak: `"stop"`, `"cancel"`, `"quiet"`, `"hush"` OR Press: `Esc` key |

---

### 3. YouTube Transcript Analyzer (Watch Video)

Allows JARVIS to "watch" and analyze YouTube videos by extracting and studying their transcripts.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Transcript Analysis** | Automatically intercepts any command containing a YouTube link, extracts the case-sensitive 11-char ID, downloads the transcript, and passes it to the AI brain as context to answer your request. | Any query containing a URL matching:<br>- `youtube.com/watch?v=[ID]` <br>- `youtu.be/[ID]` <br>- `youtube.com/embed/[ID]` <br><br>*Example: "Summarize this video https://youtu.be/dQw4w9WgXcQ"* |
| **Failure/Disabled Fallback** | Detects if a video has subtitles disabled or is set to private. Gracefully alerts the user without crashing the thread. | *(Automatically triggered on API exceptions)* |

---

### 4. Multi-Agent Orchestration (Supervisor Core)

Decomposes complex requests into task dependency graphs, executes tasks in parallel, and merges outputs.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Supervisor Planner** | Prompts Gemini to generate a JSON plan of tasks with IDs, assigned agents, and dependencies, runs independent tasks concurrently in a thread pool, passes contexts, and outputs a consolidated report. | Commands starting with:<br>- `"orchestrate [task list/request]"` <br>- `"plan and execute [request]"` <br>- `"run plan [request]"` |

---

### 5. Autonomous Browser Agent (Web Automation)

An agent that opens Chrome, navigates Google, clicks buttons, types queries, and reads pages to complete web goals.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Playwright Web Agent** | Launches a background Chromium instance, uses an iterative AI loop (`GOTO`, `CLICK`, `TYPE`, `WAIT`, `ANSWER`) to solve complex web search goals, and returns the final answer. | Commands containing:<br>- `"browse web [goal]"` <br>- `"search online for [goal]"` <br>- `"autonomous browser"` <br>- `"web agent"` |

---

### 6. Agile Web Codegen & Deployment (Devin Mode)

JARVIS's most powerful developer tool. Code, seed, test, auto-heal, and deploy Flask-Tailwind projects.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Autonomous Codegen** | Runs a multi-step engineer loop. Generates standard Flask factory structures (models, routes, seeding scripts) and Tailwind frontend layouts. | `"build a website"`, `"create a project"`, `"make a website [topic]"` |
| **Self-Healing Server** | Launches a local server in a virtual sandbox on Port 5000. If the server crashes on boot, JARVIS captures the error trace, rewrites the buggy code via Gemini, and restarts the server automatically. | *(Automatic loop during project launch)* |
| **Internet Deployment** | Kills conflicting ports, launches a secure `ngrok` tunnel, and saves deployment credentials to `deployment_manifest.txt`. | Speak `"deploy"` during the codegen iteration loop. |
| **GitHub Handover** | Creates a remote private repository, commits all code files, and pushes them to your GitHub account using your token. | `"push to github"`, `"deploy to github"` |
| **GitHub Deletion** | Destructive deletion of a remote repository from your GitHub account (requires confirmation). | `"delete repository [name]"`, `"drop github repository [name]"` |
| **Recall & Open Project** | Searches desktop archives for a project, resolves port conflicts, compiles virtual environment, and launches the preview in browser. | `"open project [name]"` |

---

### 7. Instant Webpage Designer (Local Single-Page)

Creates lightweight themed mockups using randomized CSS archetypes.

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Designer Module** | Generates an `index.html` page using a random theme (Iron Man, Cyberpunk, Obsidian, emerald Matrix, Synthwave) and opens it in browser. | Commands matching: `"build webpage [topic]"`, `"create page [topic]"`, `"design web page [topic]"` |

---

### 8. Web Search (DuckDuckGo & HD Images)

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **DDG Search** | Searches DuckDuckGo, speaks the top result summary, and launches the browser tab. | Commands containing:<br>- `"search for [query]"`<br>- `"google [query]"`<br>- `"look up [query]"`<br>- `"find info on [query]"` |
| **HD Image Search** | Searches DuckDuckGo for high-resolution images, downloads the thumbnail via Bing Thumbnail API, and opens it on screen. | Commands containing visual and image keywords:<br>- `"show me [topic] images"`<br>- `"display image of [topic]"`<br>- `"give me picture of [topic]"` |

---

### 9. Vision System & Screen Analysis

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Inspect Desktop** | Takes a screenshot, reads it into memory, and speaks a detailed visual analysis of what you are looking at. | `"what do you see"` |
| **Proactive Error Catcher** | *(Background service)* Scans screen for code/terminal errors. If an error is stuck for >10 seconds, JARVIS proactively offers to diagnose the bug. | *(Automatic background process)* |

---

### 10. Factual Vector Memory & JSON Database

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Store Fact (JSON)** | Saves a personal detail or fact to vector memory (`memory.json`). | `"remember that [fact]"`, `"save this info [fact]"`, `"remember [fact]"` |
| **Inspect DB** | Opens the raw memory JSON database file in your default text editor. | `"open memory"`, `"show memory"` |
| **Recall Memories (ChromaDB)** | Recall details from long-term memory (stores vector embeddings under `Desktop/JARVIS_Memory`). | *(Automatic context query parsing)* |

---

### 11. Desktop File & Folder Management (Skills Module)

Modular commands executed via [skills/file_management.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/skills/file_management.py).

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Create Folder** | Creates a directory on your Desktop and opens it. | `"create folder [name]"` |
| **Create Text File** | Writes a blank `.txt` file on your Desktop, or inside an existing folder, and opens it. | `"create file [name]"`, `"create file [name] inside [folder]"` |
| **Open Folder** | Searches your user directories (Documents, Downloads, Desktop) and opens the folder. | `"open folder [name]"` |
| **Force Delete** | Asks for confirmation, then bypasses locks to permanently delete a folder/file. | `"delete folder [name]"` |

---

### 12. Media Player & Hotkey Automation

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Play Song** | Opens YouTube standalone web app, searches for the song, and presses enter to play. | `"play music [song]"`, `"play [song]"` |
| **Pause/Play Media** | Emulates keyboard Media Play/Pause hotkey. | `"pause"`, `"play"` |
| **Stop Music** | Emulates keyboard Media Stop hotkey. | `"stop music"` |
| **Next Track** | Skips to the next song/video in queue. | `"next track"` |
| **Previous Track** | Skips back to the previous song/video in queue. | `"previous track"` |

---

### 13. System App Controller

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Launch App** | Resolves name and opens Notepad, Paint, Calculator, Chrome, VS Code, etc. | `"open [app name]"` |
| **Kill App** | Taskkills the program process tree or closes the active browser tab. | `"close [app name]"` |
| **Focus Window** | Brings the matching open program window to the foreground. | `"focus window [name]"`, `"activate window [name]"`, `"switch to window [name]"` |
| **List Windows** | Lists all currently open application titles on the Desktop. | `"list open windows"`, `"list active windows"`, `"show open windows"` |

---

### 14. Voice, Video & Screen Recorder

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Webcam Record** | Records webcam video input to `jarvis_video.avi` in your `jarvis documents` directory. | `"record video"` |
| **Screen Record** | Captures desktop screen video input to `jarvis_screen.avi` in your `jarvis documents` directory. | `"record screen"`, `"start screen recording"` |
| **Stop Recording** | Gracefully halts webcam or screen video recording and saves output. | `"stop video"`, `"stop screen recording"`, `"stop recording"` |
| **Audio Recorder** | Records microphone input. Press ENTER in the terminal to stop, name the file, and save. | `"record voice"`, `"record audio"` |

---

### 15. Scheduler & Reminders

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **Set Alert** | Prompts for task and time, saves in `jarvis_reminders.json`, and triggers a vocal/text alert. | `"set a reminder"` |

---

### 16. Communication Dispatchers

| Feature Name | Function & Use | Command / Trigger Syntax |
| :--- | :--- | :--- |
| **WhatsApp message** | Retrieves number from contacts, prompts for text, launches WhatsApp Desktop, and sends the message. | `"whatsapp"` |
| **Secure Email** | Prompts for contact, subject, message body, lets you select an attachment file via UI file dialog, and sends via Gmail SMTP. | `"send email"` |

---

### 17. Master OS Hotkeys

Emulates standard Windows shortcut key presses directly.

| Vocal Trigger / Command | Action Executed | Keyboard Combination |
| :--- | :--- | :--- |
| `"new tab"` | Opens new browser tab | `Ctrl + T` |
| `"close tab"` | Closes active browser tab | `Ctrl + W` |
| `"switch tab"` | Cycles through open browser tabs | `Ctrl + Tab` |
| `"refresh"` | Reloads the active browser page | `F5` / `Ctrl + R` |
| `"incognito"` | Opens a new incognito window | `Ctrl + Shift + N` |
| `"history"` | Opens browser history panel | `Ctrl + H` |
| `"downloads"` | Opens browser downloads panel | `Ctrl + J` |
| `"scroll down"` | Scrolls page down | Mouse scroll down |
| `"scroll up"` | Scrolls page up | Mouse scroll up |
| `"scroll to top"` | Jumps to top of page | `Ctrl + Home` |
| `"scroll to bottom"` | Jumps to bottom of page | `Ctrl + End` |
| `"minimise window"` | Minimizes current window | `Win + Down` |
| `"maximise"` | Maximizes current window | `Win + Up` |
| `"close window"` | Closes active window | `Alt + F4` |
| `"lock screen"` | Locks the Windows user session | `Win + L` |
| `"show desktop"` | Minimizes all windows to show Desktop | `Win + D` |
| `"select all"` | Selects all text/items in focus | `Ctrl + A` |
| `"copy"` | Copies selected text/item | `Ctrl + C` |
| `"paste"` | Pastes text/item from clipboard | `Ctrl + V` |
| `"save"` | Saves active file | `Ctrl + S` |
| `"undo"` | Undoes last text edit | `Ctrl + Z` |
| `"redo"` | Redoes last undone text edit | `Ctrl + Y` |
| `"enter"` | Emulates Enter key press | `Enter` |
| `"delete"` | Emulates Delete key press | `Delete` |
| `"clear text"` | Clears focus input text field | `Backspace` loop |
| `"screenshot"` | Captures screen and saves PNG to Desktop | `PrtScn` (via pyautogui) |
| `"task manager"` | Opens Windows Task Manager | `Ctrl + Shift + Esc` |
| `"file explorer"` | Opens Windows File Explorer | `Win + E` |
| `"settings"` | Opens Windows Settings App | `Win + I` |
| `"run dialog"` | Opens Windows Run dialog | `Win + R` |
| `"clipboard"` | Opens Windows Clipboard History panel | `Win + V` |
| `"emoji"` | Opens Windows Emoji picker panel | `Win + .` |
| `"control panel"` | Opens Windows Legacy Control Panel | Launches `control` command |
| `"magnifier"` | Launches Windows Magnifier tool | `Win + +` |
| `"narrator"` | Toggles Windows Narrator tool | `Win + Ctrl + Enter` |
| `"on-screen keyboard"` | Launches Windows On-Screen Keyboard | Launches `osk` command |
| `"brightness"` | Opens Windows Quick Settings Panel | `Win + A` |
| `"recycle bin"` | Opens system Recycle Bin folder | Opens folder path |
| `"documents folder"` | Opens user Documents folder | Opens folder path |
| `"pictures folder"` | Opens user Pictures folder | Opens folder path |
| `"videos folder"` | Opens user Videos folder | Opens folder path |

---

### 18. Generalist Fallback (Restricted Sandbox Solver)

When you ask JARVIS to execute a command that does not match any preset trigger or skill pattern, JARVIS automatically invokes the **GeneralistAgent** (Open Interpreter in restricted mode).

- **Restricted Directory**: It is strictly locked to only modify or create files inside `Desktop/jarvis documents` for security.
- **Manual Confirmation**: By default, `auto_run=False` is set. It will list the commands it intends to run in your terminal and wait for your manual approval (pressing `y` or `n`) before running them.
- **Forbidden Actions**: Blocked from running administrative commands, registry hacks, or system-wide deletions (`rm -rf`, disk formatting, etc.).

---

## ⚡ Technical Mechanics & Configuration Overviews

This section provides technical documentation for developers or users wanting to customize system constants.

### A. Core Configurations ([config.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/config.py))
- **Email Dispatcher**: Uses SSL connection over `smtp.gmail.com` on Port 465. Passwords must use Gmail App Passwords (`config.EMAIL_PASS`).
- **Rotating Key Pool**: Rotating key lists dynamically override standard rate limits. API responses are auto-cleaned of markdown markers prior to spoken delivery.
- **Local AI Fallback**: Ollama server endpoint `http://localhost:11434/api/generate` running `llama3` by default.

### B. Proactive Watchdog Daemons ([proactive_module.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/proactive_module.py))
- **System Diagnostics**: Periodic checks run in background threads. Battery warnings alert users when the percent drops below 20% on DC power. CPU thresholds alarm users if utilization exceeds 85% with a 10-minute warning cooldown.
- **Screen Traceback Detector**: Silently grabs grayscaled desktop screen regions using `mss` (RAM capture, avoiding disk IO). Checks coding environments (VS Code, terminal, PyCharm). If tracebacks or syntax trace lines persist for more than 10 seconds, it launches a vocal repair option.

### C. Speech & Neural Verification ([speech_module.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/speech_module.py))
- **Silero VAD Integration**: PyTorch-based neural Voice Activity Detection. Processes sound signals, converting audio arrays to 16kHz mono formats. Background static noise is evaluated by neural filters to verify human speech patterns before engaging APIs.
- **Adaptive Calibration**: Acoustic profiles are calibrated using a 1.0-second room sweep on initialization. Adaptive 0.2-second sweeps run dynamically prior to each audio recording.

### D. GUI HUD Dock console ([jarvis_gui.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/jarvis_gui.py))
- **View States**: Collapsed mode is a transparent floating glassmorphic pill widget. Hovering over it for 2 seconds activates Magenta border relocation, which dynamically binds to system cursor movements until clicked. 
- **Voice animations**: Uses custom rendering painters in PyQt5 to dynamically map SAPI/Edge-TTS thread signals into waveform animations.

### E. Web Designer & Devin loops ([agent_module.py](file:///C:/Users/DELL/OneDrive/Desktop/assistent/agent_module.py))
- **Seeding Databases**: Auto-seeding functions are designed to use local model scopes to avoid SQLAlchemy argument errors.
- **Host Binding Fix**: The launch utility scans all active network connections, identifying conflict PIDs bound to Port 5000, and taskkills parent/child trees before binding new Flask sockets.
