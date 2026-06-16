import streamlit as st
import json
import os
import time
import psutil # ✨ NEW: For Hardware Stats
import config

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title=f"{config.AI_NAME} HUD",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (THEME INJECTION) ---
st.markdown("""
    <style>
        /* IMPORT FUTURISTIC FONT */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;700&display=swap');

        /* MAIN BACKGROUND & TEXT */
        .stApp {
            background-color: #050505;
            color: #00FFFF;
            font-family: 'Roboto Mono', monospace;
        }

        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* NEON TITLES */
        h1, h2, h3 {
            font-family: 'Orbitron', sans-serif;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #fff;
            text-shadow: 0 0 10px #00FFFF;
        }

        /* SIDEBAR STYLING */
        section[data-testid="stSidebar"] {
            background-color: #0a0a0a;
            border-right: 1px solid #00FFFF;
        }

        /* DATA CARDS & CONTAINERS */
        div.stContainer, div[data-testid="stMetricValue"] {
            background: rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 5px;
            padding: 10px;
        }

        /* PROGRESS BARS (Cyan Glow) */
        .stProgress > div > div > div > div {
            background-color: #00FFFF;
            box-shadow: 0 0 10px #00FFFF;
        }

        /* CHAT BUBBLES */
        .stChatMessage {
            background-color: rgba(0, 0, 0, 0.5);
            border-left: 3px solid #00FFFF;
            margin-bottom: 10px;
        }

        /* BUTTONS (Neon Outline) */
        button {
            border: 1px solid #00FFFF !important;
            background-color: transparent !important;
            color: #00FFFF !important;
            font-family: 'Orbitron', sans-serif !important;
        }
        button:hover {
            background-color: #00FFFF !important;
            color: #000 !important;
            box-shadow: 0 0 15px #00FFFF;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS (Preserved) ---
st.sidebar.title("⚙️ PROTOCOLS")
st.sidebar.header("Identity Management")

with st.sidebar.form("settings_form"):
    new_name = st.text_input("AI Codename", value=config.AI_NAME)
    new_owner = st.text_input("Operator Name", value=config.OWNER_NAME)
    
    if st.form_submit_button("UPDATE CONFIG"):
        # Read the config file text
        with open("config.py", "r") as f:
            lines = f.readlines()
        
        # Rewrite the file with new values
        with open("config.py", "w") as f:
            for line in lines:
                if "AI_NAME =" in line:
                    f.write(f'AI_NAME = "{new_name}"\n')
                elif "OWNER_NAME =" in line:
                    f.write(f'OWNER_NAME = "{new_owner}"\n')
                else:
                    f.write(line)
        
        st.sidebar.success("SYSTEM UPDATED. REBOOT REQUIRED.")
        time.sleep(1)
        st.rerun()

# --- HEADER SECTION (New HUD Look) ---
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    # Animated Arc Reactor GIF
    st.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzJjYzAA/3o7TKSjRrfIPjeiVyM/giphy.gif", width=80)
with col2:
    st.title(f"SYSTEM: {config.AI_NAME.upper()}")
    st.caption(f"OPERATOR: {config.OWNER_NAME.upper()} | STATUS: ONLINE")
with col3:
    # Live Clock
    st.markdown(f"<h2 style='text-align: right; color: #00FFFF;'>{time.strftime('%H:%M:%S')}</h2>", unsafe_allow_html=True)

st.markdown("---")

# --- MAIN LAYOUT ---
# Left: Chat Feed | Right: System Telemetry
main_col, stat_col = st.columns([2, 1])

# --- LOG FILE READER ---
log_file = "jarvis_logs.jsonl"
logs = []
if os.path.exists(log_file):
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    logs.append(json.loads(line_str))
        logs = logs[::-1] # Newest on top
    except Exception:
        logs = []

# --- 1. LEFT COLUMN: TABS (LIVE FEED & COGNITIVE MEMORY) ---
with main_col:
    tab1, tab2 = st.tabs(["📡 DATA UPLINK", "🧠 COGNITIVE BRAIN & MEMORY"])
    
    with tab1:
        st.subheader("CONSOLE INTERACTION FEED")
        chat_container = st.container(height=500)
        
        with chat_container:
            if not logs:
                st.info("AWAITING INPUT...")
            
            for log in logs[:20]: # Show last 20 to keep it fast
                timestamp = log.get("timestamp", "Unknown")
                msg_type = log.get("type", "system")
                message = log.get("message", str(log))
                
                if msg_type == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**[{timestamp}] USER:** {message}")
                elif msg_type == "jarvis":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(f"**[{timestamp}] AI:** {message}")
                elif msg_type == "task":
                    st.warning(f"⚡ ACTION [{timestamp}]: {message}")
                else:
                    st.code(f"LOG: {message}")

    with tab2:
        st.subheader("COGNITIVE MEMORY HUD")
        
        try:
            from memory_moduler import MemorySystem
            mem = MemorySystem()
        except Exception as e:
            st.error(f"Failed to load memory module: {e}")
            mem = None

        if mem:
            # 👤 Operator Profile Section
            st.write("### 👤 Operator Cognitive Persona")
            profile = mem.get_user_profile()
            
            p_style = profile.get("conversational_style", "conversational")
            p_interaction = profile.get("interaction_type", "text")
            p_topics = profile.get("frequent_topics", {})
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Detected Style", p_style.upper())
            with c2:
                st.metric("Preferred Input", p_interaction.upper())
            with c3:
                top_topics = sorted(p_topics.items(), key=lambda x: x[1], reverse=True)
                fav_topic = top_topics[0][0].replace("_", " ").upper() if top_topics else "NONE"
                st.metric("Primary Topic", fav_topic)
                
            if p_topics:
                st.write("**Topic Interaction Frequency:**")
                cols = st.columns(len(p_topics))
                for idx, (t, count) in enumerate(p_topics.items()):
                    cols[idx].code(f"{t.replace('_', ' ')}: {count}")
            
            st.markdown("---")
            
            # 1. Facts Section
            st.write("### 📝 Stored Facts about Operator")
            facts = mem.data.get("facts", [])
            if facts:
                for i, fact in enumerate(facts):
                    c1, c2 = st.columns([5, 1])
                    c1.info(fact)
                    if c2.button("Forget", key=f"forget_fact_{i}"):
                        res = mem.forget_fact(i + 1)
                        st.success(res)
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.info("No personal facts stored yet.")
                
            # 2. Rules Section
            st.write("### 📜 Dynamic Directives & Behavioral Rules")
            rules = mem.recall_rules()
            if rules:
                for i, rule in enumerate(rules):
                    c1, c2 = st.columns([5, 1])
                    c1.warning(rule)
                    if c2.button("Purge", key=f"forget_rule_{i}"):
                        res = mem.forget_rule(i + 1)
                        st.success(res)
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.info("No behavioral rules learned yet.")
                
            # 3. Preferences Section
            st.write("### ⚙️ Operator Preferences")
            prefs = mem.recall_preferences()
            if prefs:
                for k, v in list(prefs.items()):
                    c1, c2 = st.columns([5, 1])
                    c1.code(f"{k} = {v}")
                    if c2.button("Clear", key=f"forget_pref_{k}"):
                        res = mem.forget_preference(k)
                        st.success(res)
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.info("No preferences saved yet.")

            # 4. Manual Cognitive Injection
            st.markdown("---")
            st.write("### ➕ Manual Cognitive Injection")
            with st.form("manual_memory_form", clear_on_submit=True):
                mem_type = st.selectbox("Memory Type", ["Fact", "Behavioral Rule", "Preference"])
                
                # Render inputs conditionally
                pref_key = st.text_input("Preference Key (e.g. favorite_color, speak_language) - Preference Type Only")
                pref_val = st.text_input("Preference Value - Preference Type Only")
                mem_content = st.text_area("Memory Content / Behavioral Directive - Fact & Rule Types Only")
                
                submit_btn = st.form_submit_button("INJECT INTO BRAIN")
                if submit_btn:
                    if mem_type == "Fact":
                        if mem_content.strip():
                            res = mem.remember_fact("remember that " + mem_content.strip())
                            st.success(res)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Please provide fact content.")
                    elif mem_type == "Behavioral Rule":
                        if mem_content.strip():
                            res = mem.remember_rule(mem_content.strip())
                            st.success(res)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Please provide rule content.")
                    elif mem_type == "Preference":
                        if pref_key.strip() and pref_val.strip():
                            res = mem.set_preference(pref_key.strip(), pref_val.strip())
                            st.success(res)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Please provide both key and value for preference.")

# --- 2. RIGHT COLUMN: HARDWARE TELEMETRY ---
with stat_col:
    st.subheader("⚙️ SYSTEM INTEGRITY")
    
    # A. CPU
    cpu = psutil.cpu_percent()
    st.write(f"**CPU CORE:** {cpu}%")
    st.progress(cpu / 100)
    
    # B. RAM
    ram = psutil.virtual_memory()
    st.write(f"**MEMORY BANK:** {ram.percent}%")
    st.progress(ram.percent / 100)
    
    # C. BATTERY (If Laptop)
    battery = psutil.sensors_battery()
    if battery:
        plugged = "🔌 AC" if battery.power_plugged else "🔋 BAT"
        st.write(f"**POWER CELL:** {battery.percent}% ({plugged})")
        st.progress(battery.percent / 100)
    
    # D. METRICS (Preserved from old code)
    total_cmds = len([l for l in logs if l.get('type') == 'user'])
    tasks_done = len([l for l in logs if l.get('type') == 'task'])
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("CMDS", total_cmds)
    c2.metric("TASKS", tasks_done)
    
    st.markdown("---")
    st.write("### 🛑 OVERRIDE")
    if st.button("PURGE LOGS"):
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
        st.rerun()

# --- AUTO REFRESH LOOP (Every 1s) ---
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

time.sleep(1)
st.rerun()