import os
from fpdf import FPDF

class ProfessionalPDF(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 297, 'F')
        self.set_draw_color(52, 152, 219) 
        self.set_line_width(1)
        self.line(10, 25, 200, 25)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(100, 100, 100) 
        self.cell(0, 10, 'JARVIS SYSTEM ARCHITECTURE // v3.0 ULTIMATE', 0, 0, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(44, 62, 80) 
        self.cell(0, 10, title.upper(), 0, 1, 'L')
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def feature_section(self, title, items):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(41, 128, 185) 
        self.cell(0, 8, title, 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50) 
        for item in items:
            if ":" in item:
                key, value = item.split(":", 1)
                self.set_font('Arial', 'B', 10)
                self.write(5, f"   {chr(149)} {key}:") 
                self.set_font('Arial', '', 10)
                self.write(5, value) 
            else:
                self.set_font('Arial', '', 10)
                self.write(5, f"   {chr(149)} {item}")
            self.ln(6)
        self.ln(4)

    def deep_dive_text(self, text):
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)
        self.ln(5)

def create_manual():
    print("Generating JARVIS Review Submission Manual...")
    pdf = ProfessionalPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- TITLE PAGE ---
    pdf.ln(40)
    pdf.set_font("Arial", 'B', 32)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 15, "JARVIS SYSTEM ARCHITECTURE", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(52, 152, 219)
    pdf.cell(0, 15, "Official Review Submission & Manual", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 14)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 8, "An Autonomous Multimodal Desktop Agent", 0, 1, 'C')
    pdf.cell(0, 8, "with Self-Healing Agile Web Development Pipelines", 0, 1, 'C')
    pdf.ln(30)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Operator/Creator: Jagadees", 0, 1, 'C')
    pdf.cell(0, 8, "Primary AI Engine: Google Gemini 2.5 Flash-Lite", 0, 1, 'C')
    pdf.cell(0, 8, "Local Backup Engine: Llama 3 (Ollama Core)", 0, 1, 'C')
    pdf.add_page()

    # --- SECTION 1: DETAILED FEATURES & COMMANDS ---
    pdf.chapter_title("1. SYSTEM FEATURES & VOICE COMMAND MATRIX")

    pdf.feature_section("1. Core System & Voice Controls", [
        "Wake Up Word ('jarvis'): Plays winsound alert chime, speaks 'Yes, Sir?' and enters active mode.",
        "Shutdown Word ('exit' / 'quit'): Vocalizes 'Powering down.' and exits program immediately.",
        "Morning Status Briefing ('morning briefing'): Greets user based on time, details battery level, current time, and overall system state."
    ])

    pdf.feature_section("2. Web Browsing & Landing Page Design", [
        "DuckDuckGo Search ('search for [query]' / 'google [query]' / 'look up [query]' / 'find info on [query]' / 'tell me about [query]'): Performs text search, vocalizes summary, and opens results in the web browser.",
        "Futuristic Landing Page Creator ('create website [topic]' / 'design a page about [topic]'): Compiles a custom, Iron Man-themed HTML landing page, saves it directly on Desktop, and opens it."
    ])

    pdf.feature_section("3. Camera & Screen Vision Core", [
        "Analyze Screen ('what do you see'): Captures screen, prompts Gemini Vision to explain contents, and reads out analysis.",
        "Proactive Syntax Error Catcher (Automatic Background Run): Captures screen in RAM every 60s. If syntax/compiler errors are visible for over 10s, JARVIS proactively asks to help analyze and fix them."
    ])

    pdf.feature_section("4. Long-Term Vector Memory", [
        "Store General Fact ('remember that [fact]' / 'save this info [fact]' / 'remember [fact]'): Indexes fact in memory.json and ChromaDB. Vocalizes: 'I have stored that in my long-term memory: [fact]'.",
        "Open Database ('open memory' / 'show memory'): Launches memory.json in default text editor."
    ])

    pdf.feature_section("5. Desktop File Management", [
        "Create Folder ('create folder [name]'): Creates folder on Desktop and opens it.",
        "Create File ('create file [name]' / 'create file [name] inside [folder]'): Searches globally for folder, creates text file, and opens it.",
        "Open Folder ('open folder [name]'): Searches local system directories and opens folder in File Explorer.",
        "Force-Delete Folder/File ('delete folder [name]' / 'delete file [name]'): Asks: 'Delete [name]?'. Bypasses read-only and lock states to force-delete item if voice confirmation ('yes', 'delete', 'sure') is received."
    ])

    pdf.feature_section("6. Media, Volume & Shortcuts", [
        "YouTube Search ('play [song]' / 'play music [song]'): If YouTube window is open, focuses search, clears, types query, and enters. Else, opens Edge standalone YouTube window directly.",
        "Volume Control ('volume up' / 'volume down' / 'mute' / 'unmute'): Simulates hardware volume buttons using PyAutoGUI.",
        "Media Shortcuts ('pause' / 'play' / 'stop music' / 'next track' / 'previous track'): Simulates multimedia key presses.",
        "App Control ('open [app]' / 'close [app]'): Launches or taskkills system apps. Gracefully closes active tabs using Ctrl+W if app is a website."
    ])

    pdf.add_page()

    pdf.feature_section("7. Global Browser & OS Commands", [
        "Browser Tabs: 'new tab', 'close tab', 'switch tab', 'previous tab', 'new window', 'incognito', 'refresh', 'home page', 'back', 'forward'.",
        "Zoom & Scroll: 'zoom in', 'zoom out', 'reset zoom', 'scroll down', 'scroll up', 'scroll to top', 'scroll to bottom'.",
        "Window management: 'minimise window', 'maximise', 'close window', 'switch window', 'lock screen', 'show desktop'.",
        "Text Editing: 'select all', 'copy', 'paste', 'delete', 'enter', 'save', 'undo', 'redo', 'clear text', 'write [text]', 'type [text]'.",
        "Screenshot: 'screenshot' (Saves timestamped PNG on Desktop).",
        "System Utilities: 'task manager', 'file explorer', 'settings', 'run dialog', 'clipboard', 'emoji', 'control panel', 'magnifier', 'narrator', 'keyboard screen'.",
        "Default Folders: 'downloads folder', 'documents folder', 'pictures folder', 'videos folder', 'music folder', 'recycle bin'."
    ])

    pdf.feature_section("8. Audio, Video & Communications", [
        "Record Webcam Video ('record video'): Initiates background thread camera capture and saves to Desktop .avi. Ends when user commands 'stop video'.",
        "Record Audio ('record voice' / 'record audio'): Records microphone feed until ENTER is pressed in terminal, prompts for file name, and saves .wav to Desktop.",
        "Tech News briefing ('tell me the news' / 'tech news'): Gathers latest headlines via DDG, summaries with Gemini, and reads news in a news anchor persona.",
        "Reminders ('set a reminder'): Prompts for task and time, registers in jarvis_reminders.json, and plays alert at the time.",
        "Native WhatsApp ('whatsapp'): Asks for recipient (resolves number in contacts.json), prompts for message, opens WhatsApp Desktop protocol, types, and sends.",
        "Email Client ('send email'): Resolves recipient, subject, body, prompts to select attachment via tkinter GUI file selector, and sends via SMTP."
    ])

    # --- SECTION 2: HOW JARVIS BUILDS WEBSITES ---
    pdf.chapter_title("2. HOW JARVIS BUILDS WEBSITES (GOD MODE)")
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, "JARVIS's standout capability is the Autonomous Project Agent ('God Mode'). When given the command to build a website, it doesn't just output templates; it acts as a Product Manager, Developer, QA Engineer, and DevOps Specialist to research, code, test, self-heal, deploy, and push to GitHub.")
    pdf.ln(5)

    workflow_steps = [
        "STEP 1: INITIATION - Triggered by the command 'build a website [topic]' or 'create a project [topic]'. If the topic is not specified, JARVIS prompts the user for one.",
        "STEP 2: VOICE REQUIREMENTS GATHERING - JARVIS prompts the user: 'Please read out the full list of client requirements. I am listening.', and records the requirements directly via the microphone.",
        "STEP 3: VECTOR PREFERENCE RECALL - JARVIS queries ChromaDB long-term memory to see if the user has any past design or architecture preferences for website projects, injecting them into the requirements stack.",
        "STEP 4: LIVE COMPETITOR TREND RESEARCH - JARVIS queries DuckDuckGo for the top 10 website features and modern trends in 2026 corresponding to the project topic.",
        "STEP 5: AGILIST CONSULTATION - Using Gemini, JARVIS acts as a Senior Product Manager. It reviews the competitor trends against the client requirements, drafts suggestions on what features to remove (outdated) and what to add (modern), and asks the user to lock or edit requirements.",
        "STEP 6: FULL-STACK APPLICATION CODEGEN - Once requirements are locked, JARVIS generates a Flask (Python) backend using the Application Factory Pattern (run.py, config.py, app/__init__.py, app/routes.py, app/models.py) and a frontend styled with Tailwind CSS and FontAwesome CDN templates.",
        "STEP 7: COMPILING MANUAL DOCUMENTATION - JARVIS automatically compiles a classified dark-mode User Manual PDF containing locked requirements, market trends, and architecture details inside the project folder.",
        "STEP 8: DB SEEDING & SELF-HEALING LOCAL PREVIEW - JARVIS bootstraps the Flask SQLAlchemy SQLite schema and launches a subprocess server on Port 5000. If the server crashes on boot, JARVIS captures the stderr log, prompts Gemini to generate a patch, updates the source code on disk, and restarts the server automatically (recursive self-healing loop).",
        "STEP 9: ITERATIVE FEEDBACK LOOP - JARVIS opens the browser preview and enters a verbal loop: 'Are you satisfied, or do you want changes?'. The user can dictate refactoring commands which JARVIS implements and regenerates on the fly.",
        "STEP 10: SECURE PUBLIC DEPLOYMENT - When the user says 'deploy', JARVIS starts a secure public web tunnel via ngrok and saves a 'deployment_manifest.txt' with credentials, local ports, and public URLs.",
        "STEP 11: AUTONOMOUS GITHUB HANDOVER - JARVIS authenticates with PyGithub, creates a remote private repository, runs local git initialization, stages, commits, and pushes the master branch securely using the GITHUB_TOKEN."
    ]

    for step in workflow_steps:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(41, 128, 185) # Blue
        pdf.cell(10, 8, chr(149), 0, 0)
        
        parts = step.split("-", 1)
        phase_name = parts[0].strip()
        phase_desc = parts[1].strip()
        
        pdf.cell(0, 8, phase_name, 0, 1)
        
        pdf.set_font('Arial', '', 9.5)
        pdf.set_text_color(80, 80, 80) 
        pdf.set_x(20) 
        pdf.multi_cell(0, 4.5, phase_desc)
        pdf.ln(3)

    # --- SECTION 3: THE GENERALIST AGENT ---
    pdf.chapter_title("3. FEATURE DEEP DIVE: GENERALIST AGENT & SECURITY")
    
    pdf.deep_dive_text("The Generalist Agent (Interpreter Mode) handles tasks falling outside predefined routines by writing and executing Python scripts dynamically.")
    
    safety_points = [
        "MANUAL CONFIRMATION PROTOCOL: JARVIS has auto_run=False. It will print planned code and prompt 'Run this code? (y/n)'. It requires manual user input to execute.",
        "HYPNOTIC OS CONSTRAINTS: Embedded instructions strictly forbid deletion of critical system files, OS registry modifications, or execution of administrative tools.",
        "ISOLATED WORKING DIRECTORY: The agent is sandboxed to work exclusively within the 'Desktop/jarvis documents' folder to keep user environments clean."
    ]

    for point in safety_points:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(231, 76, 60) # Red for Safety
        pdf.cell(10, 8, "!", 0, 0, 'C')
        
        parts = point.split(":", 1)
        pdf.write(5, f"{parts[0]}:") 
        pdf.set_font('Arial', '', 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.write(5, parts[1])
        pdf.ln(6)

    # --- OUTPUT ---
    desktop = os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')
    filepath = os.path.join(desktop, "JARVIS_Review_Submission.pdf")
    
    try:
        pdf.output(filepath)
        print(f"Document Created Successfully: {filepath}")
        os.startfile(filepath)
    except Exception as e:
        print(f"Error creating PDF: {e}")

if __name__ == "__main__":
    create_manual()