# JARVIS User Guide & Capabilities Manual

Welcome, Sir. This document outlines the complete system architecture, capabilities, and vocal commands of the **JARVIS** Assistant.

---

## 🛠️ System Architecture

JARVIS is built using a custom Python modular architecture that connects hardware sensors, OS automation, local storage, and cloud AI:
- **Neural Engine**: Primary processing via **Google Gemini 2.5 Flash-Lite**, with **Gemini 2.0 Flash-Lite** as a fast backup for timeouts, and **Llama 3 (Ollama)** as a local fallback for offline usage.
- **Speech System**: Speech-to-text using `SpeechRecognition` with neural filter validation (Silero VAD) to ignore non-human noise. Text-to-speech using standard Windows Audio (`SAPI.SpVoice`).
- **Vision Core**: Active screen monitoring using `mss` (instant screen grabs to memory) and `pyautogui` for screenshots, enabling visual self-awareness.
- **Memory Bank**: Vector-based semantic memory using `ChromaDB` (SentenceTransformers) for long-term recall, and `memory.json` for general factual recall.
- **Project Controller**: Agile project builder utilizing `Flask`, `Tailwind CSS`, `Docker`, `ngrok` (secure web tunnels), and `Git/GitHub` (repo creation & pushes).

---

## 📡 Capabilities & Voice Commands Matrix

JARVIS operates in two modes:
1. **Standby Mode**: Listens silently for the wake word.
2. **Active Mode**: Triggered by the wake word. Executes commands and automatically returns to standby unless a conversation thread continues.

---

### 1. System & Wake Controls

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Wake Up** | `"jarvis"` | Plays a chime, speaks `"Yes, Sir?"`, and enters active mode. |
| **Standby / Sleep** | `"go to sleep"`, `"sleep mode"`, `"standby"`, `"go to standby"` | Speaks `"Entering standby mode."` and enters passive standby mode, listening only for the wake word. |
| **Exit** | `"exit"`, `"quit"` | Powers down the system and terminates execution (`os._exit(0)`). |

---

### 2. Web Search & Design

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **DDG Web Search** | `"search for [query]"`, `"google [query]"`, `"look up [query]"`, `"find info on [query]"`, `"tell me about [query]"` | Searches DuckDuckGo, vocalizes the top summary, and opens the link in Edge/Chrome. |
| **Instant Designer** | `"create website [topic]"`, `"design a page about [topic]"` | Generates a futuristic, Iron Man-themed HTML page, saves it to your Desktop, and opens it. |

---

### 3. Vision & Screen Analysis

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Analyze Screen** | `"what do you see"` | Takes a screen capture, sends it to Gemini, and reads a detailed analysis of what is currently on your screen. |
| **Proactive Error Catcher** | *(Automatic Background Run)* | Scans active programming environments (VS Code, terminal, PyCharm). If a syntax or compilation error is visible on screen for more than **10 seconds**, JARVIS speaks: *"Sir, I notice you are stuck on a syntax error. Would you like me to analyze the screen and suggest a fix?"* |

---

### 4. Vector Memory & Facts

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Learn Fact** | `"remember that [fact]"`, `"save this info [fact]"`, `"remember [fact]"` | Cleans and formats the fact, saves it to `memory.json` / ChromaDB, and confirms: *"I have stored that in my long-term memory: '[fact]'"*. |
| **Recall Memory** | `"what have you learned about me"`, `"what do you know about me"`, `"show learned memory"` | Speaks a detailed summary of all learned facts, rules, and preferences. |
| **Forget Fact** | `"forget fact [query]"`, `"delete fact [query]"` | Purges the matched learned personal fact from `memory.json`. |
| **Forget Rule** | `"forget rule [query]"`, `"delete rule [query]"` | Purges the matched dynamic behavior rule from `memory.json`. |
| **Forget Preference**| `"forget preference [key]"`, `"delete preference [key]"` | Purges the matched user preference key from `memory.json`. |
| **Open Memory** | `"open memory"`, `"show memory"` | Opens the `memory.json` database file directly in your default text editor. |

---

### 5. Desktop File Manager

JARVIS interacts directly with your Desktop (`C:\Users\DELL\OneDrive\Desktop`):

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Create Folder** | `"create folder [name]"` | Creates the folder on your Desktop and opens it. |
| **Create File** | `"create file [name]"`, `"create file [name] inside [folder]"` | Creates a text file (appending `.txt` automatically if missing) on your Desktop or inside a specified folder, then opens it. |
| **Open Folder** | `"open folder [name]"` | Searches globally on your PC and opens the folder in File Explorer. |
| **Delete Item** | `"delete folder [name]"`, `"delete file [name]"` | Asks for confirmation: *"Delete [name]?"*. If you answer *"yes"*, *"delete"*, or *"sure"*, JARVIS bypasses lock/read-only states to force-delete the item. |

---

### 6. Media & System Automation

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Play Music** | `"play music [song]"`, `"play [song]"` | If YouTube is already open, targets the search bar, enters the song, and presses enter. If closed, launches YouTube as a standalone app. |
| **Volume Control** | `"volume up"`, `"volume down"`, `"mute"`, `"unmute"` | Adjusts your PC volume or mutes the system. |
| **Media Player** | `"pause"`, `"play"`, `"stop music"`, `"next track"`, `"previous track"` | Executes media hotkeys (Play, Pause, Track Skip). |
| **Application Launch** | `"open [app name]"` | Opens system applications (Notepad, Calculator, Paint, Chrome, VS Code) using `AppOpener` or fallback search. |
| **Close Application**| `"close [app name]"` | Taskkills the program or gracefully closes the tab (`Ctrl+W`) if it is a web service. |

---

### 7. Global Browser & OS Hotkeys

| Action Category | Supported Commands | Keyboard Shortcut Executed |
| :--- | :--- | :--- |
| **Browser Tabs** | `"new tab"`, `"close tab"`, `"switch tab"`, `"previous tab"`, `"new window"`, `"incognito"`, `"refresh"`, `"home page"`, `"back"`, `"forward"` | `Ctrl+T`, `Ctrl+W`, `Ctrl+Tab`, `Alt+Left`, `F5`, etc. |
| **Zoom & Scroll** | `"zoom in"`, `"zoom out"`, `"reset zoom"`, `"scroll down"`, `"scroll up"`, `"scroll to top"`, `"scroll to bottom"` | `Ctrl++`, `Ctrl+-`, Mouse Scroll Wheel, `Ctrl+Home`, etc. |
| **Windows Control**| `"minimise window"`, `"maximise"`, `"minimise"`, `"close window"`, `"switch window"`, `"lock screen"`, `"show desktop"` | `Win+Down`, `Win+Up`, `Alt+F4`, `Win+L`, `Win+D`, etc. |
| **Text Editing** | `"select all"`, `"copy"`, `"paste"`, `"delete"`, `"enter"`, `"save"`, `"undo"`, `"redo"`, `"clear text"`, `"write [text]"`, `"type [text]"` | `Ctrl+A`, `Ctrl+C`, `Ctrl+V`, `Ctrl+S`, `Ctrl+Z`, types text, etc. |
| **Screenshot** | `"screenshot"` | Captures your screen and saves it as `screenshot_[timestamp].png` on your Desktop. |
| **System Panels** | `"task manager"`, `"file explorer"`, `"settings"`, `"run dialog"`, `"clipboard"`, `"emoji"`, `"control panel"` | `Ctrl+Shift+Esc`, `Win+E`, `Win+I`, `Win+R`, `Win+V`, etc. |
| **Folders** | `"downloads folder"`, `"documents folder"`, `"pictures folder"`, `"videos folder"`, `"music folder"`, `"recycle bin"` | Launches the respective system directory. |

---

### 8. Voice & Video Recording

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Record Video** | `"record video"` | Opens your webcam feed and records until you say `"stop video"` or `"jarvis stop video"`. Saves `.avi` to Desktop. |
| **Record Audio** | `"record voice"`, `"record audio"` | Records your microphone. Press `ENTER` in the terminal to stop, then JARVIS prompts for a custom name and saves `.wav` to Desktop. |

---

### 9. Secretary & Communication

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Daily Briefing** | `"morning briefing"` (or automatic at 9 AM) | Greets the user, states battery status, current time, and overall system status. |
| **Tech News Anchor** | `"tell me the news"`, `"tech news"` | Searches the web, formats modern tech/AI news, and reads it like a news anchor. |
| **Reminders** | `"set a reminder"` | Asks for task and time (e.g. `"17:00"`). Saves in `jarvis_reminders.json` and alerts you at the specified time. |
| **WhatsApp message**| `"whatsapp"` | Prompts for a contact name (from `contacts.json` or manual prompt), asks for the message, opens WhatsApp Desktop protocol, and hits Enter. |
| **Email Sender** | `"send email"` | Checks config credentials, prompts for contact recipient, subject, body, asks if you want to attach a file (opens Tkinter file picker), and securely sends via Gmail SMTP. |

---

### 10. Autonomous Agile Developer (God Mode)

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Build Project** | `"build a website"`, `"create a project"` | Runs the following automated pipeline:<br>1. Listens to your client requirements.<br>2. Recalls past design preferences from vector memory.<br>3. Searches top 10 trends on DuckDuckGo and suggests structural improvements (Remove / Add).<br>4. Generates standard full-stack Flask Backend + Tailwind CSS Frontend files.<br>5. Saves them under `Desktop/JARVIS_Projects/`.<br>6. Generates a project documentation PDF.<br>7. Seeds the SQLite Database.<br>8. Launches the server on Port 5000.<br>9. **Self-Heals**: If the server crashes on startup, JARVIS reads the error log, edits the code via Gemini, and restarts the server.<br>10. Prompts for changes (iterative development) or `"deploy"`.<br>11. **Internet Deployment**: Creates a public tunnel using ngrok, saves a `deployment_manifest.txt` with credentials and URL.<br>12. **GitHub Handover**: Commits the code and pushes it to a private repository on your GitHub account using your token. |
| **Open Project** | `"open project [name]"` | Locates the project folder on your Desktop, initializes the self-healing server loop, and launches the URL. |

---

### 11. Operator Persona & Self-Learning (Cognitive Engine)

JARVIS features a background self-learning engine that tracks user conversational styles and topics silently.

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Speak Introduction** | `"tell me about yourself"`, `"who are you"`, `"speak a brief about yourself"` | Reads codebase structure, active custom skills, configuration states, and capabilities manual to formulate a custom butler-style self-introduction. |
| **Show Operator Profile** | `"show my profile"`, `"who am i to you"` | Speaks a summary report detailing the detected conversational style, top topic frequency, and interaction habits. |
| **Line-Length Constraints** | *(Automatic)* | Simple queries (general facts, country profiles, basic greeting chit-chat) are constrained exactly to 3–6 lines. Complex queries (coding, debug, architecture design) are programmatically constrained to less than 12 lines (max 11 lines). |

---

### 12. Smart E-Commerce Shopper (Indian Market)

JARVIS includes a shopping agent configured exclusively to find the best prices on Indian e-commerce sites.

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Price Comparison** | `"buy [item]"`, `"find lowest price of [item]"`, `"check price of [item]"` | Suffixes search queries with `"price India"`. Compares prices on verified Indian domains (e.g. `amazon.in`, `flipkart.com`, `croma.com`), analyzes review sites using Gemini to avoid scam sellers, and justifies selection. |
| **Checkout Automation** | *(Automatic after selection)* | Spawns a visible Playwright Chrome session, navigates to the cheapest verified merchant, adds the product to the cart, proceeds to checkout, and stops securely at the payment page for the operator. |

---

### 13. Multilingual Routing & Regional Voices

JARVIS supports regional accents and native speech translation dynamically.

| Action | Vocal Trigger / Command | Detail |
| :--- | :--- | :--- |
| **Switch Language** | `"speak in [language]"`, `"talk in [language]"` | Remaps the text-to-speech output to a specific regional voice. Supported languages: Telugu, Hindi, Bengali, Tamil, Kannada, Malayalam, Marathi, Urdu, Gujarati, and English. |
| **Auto-Detect Telugu** | *(Automatic)* | Scans text for Telugu script characters (`[\u0C00-\u0C7F]`) and automatically switches TTS to `te-IN-MohanNeural` voice model. |
| **Bidirectional Translation** | *(Automatic)* | Translates incoming regional languages to English for execution routing, and translates responses back to the regional script before reading. |

---

### 14. Graphical HUD & Streamlit Dashboard

JARVIS includes visual interfaces for system interaction and cognitive memory management.

| Interface | Start Command / Script | Details |
| :--- | :--- | :--- |
| **PyQt5 HUD Dock** | `.\wakeup_jarvis.bat` (launches `jarvis_gui.py`) | Floating status bar on the screen featuring:<br>- **Voice Wave Visualizer**: Dynamic face widget displaying moods (Listening, Thinking, Speaking, Error, Standby).<br>- **Add Contact Dialogue**: Built-in modal window to register contacts.<br>- **Attachment Handler**: File-stash button to select email/WhatsApp files.<br>- **Holographic Window**: Renders downloaded search images on visual explanation queries. |
| **Streamlit Cognitive HUD** | `.\start_dashboard.bat` (launches `dashboard.py`) | Fully featured browser panel displaying:<br>- **Cognitive Memory Lists**: Fact list, dynamic behavior rules, and preferences.<br>- **Forget / Manual Injection buttons**: Human-in-the-loop control to insert or purge rules and facts.<br>- **Operator Style Analytics**: Metrics detailing detected conversational style and favourite topic frequencies. |

---

## 🛡️ Security & Generalist Fallback

If you ask JARVIS to do a task that is not covered by the predefined commands, it will trigger the **GeneralistAgent** (Open Interpreter in restricted mode).
- Requires manual step-by-step confirmation (`auto_run=False`).
- Restricted from deleting system files or using administrator commands.
- Constrained to work only within the `Desktop/jarvis documents` folder.
