import unittest
import sys
import os
import time
import shutil
import json
import re
from unittest.mock import MagicMock, patch

# Ensure sys.stdout handles UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Ensure Assist workspace is in path
sys.path.append(os.getcwd())

class TestJarvisConfig(unittest.TestCase):
    def test_config_variables(self):
        """Test config module attributes and key pools."""
        import config
        self.assertTrue(hasattr(config, "API_KEYS_POOL"), "API_KEYS_POOL should be defined in config")
        self.assertIsInstance(config.API_KEYS_POOL, list, "API_KEYS_POOL should be a list")
        self.assertTrue(hasattr(config, "AI_MODELS"), "AI_MODELS should be defined in config")
        self.assertTrue(hasattr(config, "KEY_COOLDOWNS"), "KEY_COOLDOWNS should be defined in config")


class TestJarvisIdentity(unittest.TestCase):
    def test_identity_constants(self):
        """Test identity module constants and introductions."""
        import identity
        self.assertIsNotNone(identity.BOT_NAME, "BOT_NAME should be set")
        self.assertIsNotNone(identity.VERSION, "VERSION should be set")
        self.assertIsNotNone(identity.CREATOR, "CREATOR should be set")
        
        intro = identity.get_introduction()
        self.assertIn(identity.BOT_NAME, intro)
        self.assertIn(identity.CREATOR, intro)


class TestJarvisLogger(unittest.TestCase):
    def setUp(self):
        self.temp_log_file = "test_jarvis_temp_logs.json"

    def tearDown(self):
        if os.path.exists(self.temp_log_file):
            try:
                os.remove(self.temp_log_file)
            except:
                pass

    def test_logger_read_write(self):
        """Test logger activity logging and reading functions."""
        import logger_module
        logger = logger_module.ActivityLogger(filename=self.temp_log_file)
        
        # Test logging
        logger.log_message("user", "Hello Jarvis")
        logger.log_message("jarvis", "Hello Sir")
        
        # Test file persistence
        self.assertTrue(os.path.exists(self.temp_log_file), "Log file should be created")
        
        # Test read
        with open(self.temp_log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["role"], "user")
        self.assertEqual(data[1]["message"], "Hello Sir")


class TestJarvisContact(unittest.TestCase):
    def setUp(self):
        self.temp_contacts = "test_contacts_temp.json"
        # Write clean mock contacts dictionary
        mock_data = {
            "dad": {"phone": "+919988776655", "email": "dad@example.com"},
            "mom": {"phone": "+918877665544", "email": "mom@example.com"},
            "developer": {"phone": "+911234567890", "email": "dev@example.com"}
        }
        with open(self.temp_contacts, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=4)

    def tearDown(self):
        if os.path.exists(self.temp_contacts):
            try:
                os.remove(self.temp_contacts)
            except:
                pass

    def test_contact_manager_lookup(self):
        """Test contact fuzzy lookup and info querying."""
        import contact_module
        
        cm = contact_module.ContactManager(filename=self.temp_contacts)
        
        # Direct match
        dad = cm.get_contact("dad")
        self.assertIsNotNone(dad)
        self.assertEqual(dad["email"], "dad@example.com")
        
        # Fuzzy match
        mom_fuzzy = cm.get_contact("mo")
        self.assertIsNotNone(mom_fuzzy)
        self.assertEqual(mom_fuzzy["email"], "mom@example.com")
        
        # Add contact
        cm.add_contact("bro", "9988776655", "bro@example.com")
        
        bro = cm.get_contact("bro")
        self.assertIsNotNone(bro)
        self.assertEqual(bro["phone"], "9988776655")


class TestJarvisMemory(unittest.TestCase):
    def setUp(self):
        self.temp_memory = "test_memory_temp.json"
        mock_data = {
            "facts": [
                "Owner likes black coffee.",
                "Project folder is desktop."
            ],
            "preferences": {},
            "custom_rules": []
        }
        with open(self.temp_memory, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=4)

    def tearDown(self):
        if os.path.exists(self.temp_memory):
            try:
                os.remove(self.temp_memory)
            except:
                pass

    def test_memory_recall_and_save(self):
        """Test memory load, recall, and persistence logic."""
        import memory_moduler
        
        ms = memory_moduler.MemorySystem(filename=self.temp_memory)
        
        # Test list recall
        facts_str = ms.recall()
        self.assertIsNotNone(facts_str)
        self.assertIn("Owner likes black coffee.", facts_str)
        
        # Test remember logic
        ms.remember_fact("remember that Owner prefers Python coding.")
        recalled = ms.recall()
        self.assertIn("Owner prefers python coding.", recalled)


class TestJarvisSpeech(unittest.TestCase):
    @patch('speech_recognition.Microphone')
    @patch('speech_recognition.Recognizer')
    def test_speech_recognizer_init(self, mock_rec, mock_mic):
        """Test SpeechRecognizer parameters initialization."""
        import speech_module
        
        sr_obj = speech_module.SpeechRecognizer()
        self.assertIsNotNone(sr_obj.recognizer)
        self.assertIsNotNone(sr_obj.microphone)
        self.assertEqual(sr_obj.recognizer.pause_threshold, 1.2)
        
    def test_speech_regex_routing(self):
        """Test language triggers matching regexes."""
        import speech_module
        
        # Telugu detection
        self.assertTrue(bool(speech_module.TELUGU_SCRIPT_RE.search("హలో జార్విస్")))
        self.assertFalse(bool(speech_module.TELUGU_SCRIPT_RE.search("Hello Jarvis")))


class TestJarvisVision(unittest.TestCase):
    @patch('vision_module.VisionSystem._gdi_capture')
    def test_vision_screen_change(self, mock_gdi):
        """Test VisionSystem frame differences and downsampling."""
        import vision_module
        from PIL import Image
        
        vs = vision_module.VisionSystem()
        
        # Create a mock solid image
        img1 = Image.new('RGB', (1920, 1080), color='white')
        img2 = Image.new('RGB', (1920, 1080), color='black')
        
        mock_gdi.return_value = img1
        
        # First capture returns True (initialization frame)
        changed_first = vs.has_screen_changed()
        self.assertTrue(changed_first)
        
        # Same image returns False (no change)
        changed_same = vs.has_screen_changed()
        self.assertFalse(changed_same)
        
        # Different image returns True
        mock_gdi.return_value = img2
        changed_diff = vs.has_screen_changed()
        self.assertTrue(changed_diff)


class TestJarvisAutomation(unittest.TestCase):
    @patch('ctypes.windll.user32.GetForegroundWindow')
    @patch('ctypes.windll.user32.GetWindowTextLengthW')
    @patch('ctypes.windll.user32.GetWindowTextW')
    def test_automation_controller(self, mock_text, mock_length, mock_hwnd):
        """Test active window title sensor."""
        import automation_module
        
        # Mock window title retrieval
        mock_hwnd.return_value = 12345
        mock_length.return_value = 18
        
        def mock_get_text(hwnd, buf, size):
            buf.value = "Visual Studio Code"
            return 18
        mock_text.side_effect = mock_get_text
        
        ac = automation_module.ApplicationController()
        title = ac.get_active_window_title()
        self.assertEqual(title, "visual studio code")


class TestJarvisAIBrain(unittest.TestCase):
    @patch('requests.get')
    def test_ai_brain_key_rotation(self, mock_get):
        """Test AIBrain key rotation indices."""
        import ai_module
        import config
        
        # Setup mock configs
        config.API_KEYS_POOL = ["key1", "key2", "key3"]
        config.KEY_COOLDOWNS = {}
        
        brain = ai_module.AIBrain()
        self.assertEqual(brain.current_key_index, 0)
        
        # Verify get available index returns expected key
        self.assertEqual(brain._get_available_key_index(), 0)
        
        # Trigger rotation
        brain._rotate_key()
        self.assertEqual(brain.current_key_index, 1)

    @patch('requests.post')
    def test_openai_fallback(self, mock_post):
        """Test ChatGPT fallback query wrapper."""
        import ai_module
        import config
        
        config.OPENAI_API_KEY = "test-openai-key"
        config.GPT_MODEL = "gpt-4o-mini"
        
        brain = ai_module.AIBrain()
        
        # Mock response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Fallback response content"}}]
        }
        mock_post.return_value = mock_resp
        
        fallback_text = brain._get_chatgpt_fallback("Tell me a story", "History context", "Rules")
        self.assertEqual(fallback_text, "Fallback response content")


class TestJarvisProactive(unittest.TestCase):
    @patch('psutil.sensors_battery')
    @patch('psutil.cpu_percent')
    def test_proactive_health_checks(self, mock_cpu, mock_bat):
        """Test proactive health system sweeps."""
        import proactive_module
        
        # Setup battery info mock
        mock_battery_info = MagicMock()
        mock_battery_info.percent = 15
        mock_battery_info.power_plugged = False
        mock_bat.return_value = mock_battery_info
        
        # Setup CPU usage mock
        mock_cpu.return_value = 90.0
        
        pa = proactive_module.ProactiveAgent()
        
        # Use mocked speaks
        pa.speak = MagicMock()
        pa.check_system_health()
        
        # Assert low battery warning speaks
        pa.speak.assert_any_call("Critical Power. Battery is at 15 percent. Please plug in.")


class TestJarvisAgents(unittest.TestCase):
    def test_document_generation(self):
        """Test DocumentAgent generation of TXT outputs."""
        import agent_module
        doc_agent = agent_module.DocumentAgent()
        
        # Create temp TXT
        path = doc_agent.create_file("TestDoc", "This is some test content.", "txt")
        self.assertTrue(os.path.exists(path))
        
        # Read back and check
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("This is some test content.", content)
        
        # Cleanup
        try:
            os.remove(path)
        except:
            pass


class TestJarvisIntentOrchestration(unittest.TestCase):
    def test_telugu_auto_translation_regex(self):
        """Test that Telugu strings are correctly identified for routing."""
        import jarvis
        
        # Telugu text matches regex
        self.assertTrue(bool(jarvis.TELUGU_SCRIPT_RE.search("జార్విస్ హలో")))
        self.assertFalse(bool(jarvis.TELUGU_SCRIPT_RE.search("Hello Jarvis")))


class TestJarvisSkills(unittest.TestCase):
    def test_skills_triggers(self):
        """Test triggers definitions in skills files."""
        from skills import email_skill, file_management, media_skill, orchestration_skill, recorder_skill, shopper_agent, whatsapp_skill
        
        self.assertGreater(len(email_skill.get_triggers()), 0)
        self.assertGreater(len(file_management.get_triggers()), 0)
        self.assertGreater(len(media_skill.get_triggers()), 0)
        self.assertGreater(len(orchestration_skill.get_triggers()), 0)
        self.assertGreater(len(recorder_skill.get_triggers()), 0)
        self.assertGreater(len(shopper_agent.get_triggers()), 0)
        self.assertGreater(len(whatsapp_skill.get_triggers()), 0)


class TestJarvisScripts(unittest.TestCase):
    def test_dependency_checking(self):
        """Test check_deps logic imports without crash."""
        import check_deps
        self.assertTrue(hasattr(check_deps, "is_stdlib"))


class TestJarvisExtendedAgents(unittest.TestCase):
    @patch('pyautogui.screenshot')
    @patch('PIL.Image.open')
    @patch('agent_module.model.generate_content')
    def test_vision_agent(self, mock_gen, mock_img_open, mock_screenshot):
        """Test VisionAgent taking screenshot and calling model to analyze."""
        import agent_module
        va = agent_module.VisionAgent()
        
        # Setup mocks
        mock_screenshot.return_value = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Visual analysis output."
        mock_gen.return_value = mock_resp
        
        res = va.analyze_screen("test prompt")
        self.assertEqual(res, "Visual analysis output.")
        mock_screenshot.assert_called_once()
        mock_gen.assert_called_once()

    @patch('requests.get')
    def test_memory_agent_offline(self, mock_get):
        """Test MemoryAgent offline fallback behavior when Ollama is offline."""
        import agent_module
        mock_get.side_effect = Exception("Connection Refused")
        
        ma = agent_module.MemoryAgent()
        self.assertFalse(ma.working)
        
        res_rem = ma.remember("test memory")
        res_rec = ma.recall("test query")
        self.assertEqual(res_rem, "Memory Core is offline.")
        self.assertEqual(res_rec, "No relevant past memories found (Core Offline).")

    @patch('requests.get')
    @patch('chromadb.PersistentClient')
    def test_memory_agent_online(self, mock_client, mock_get):
        """Test MemoryAgent remember and recall workflows when online."""
        import agent_module
        
        # Mock requests.get to return 200 OK (online Ollama)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3:latest"}]}
        mock_get.return_value = mock_resp
        
        # Mock collection instance and methods
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"documents": [["past memory 1", "past memory 2"]]}
        
        mock_persistent_client = MagicMock()
        mock_persistent_client.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_persistent_client
        
        ma = agent_module.MemoryAgent()
        self.assertTrue(ma.working)
        
        res_rem = ma.remember("fact content")
        res_rec = ma.recall("query content")
        
        self.assertEqual(res_rem, "Memory stored.")
        self.assertIn("past memory 1", res_rec)
        mock_collection.add.assert_called_once()
        mock_collection.query.assert_called_once()

    @patch('agent_module.model.generate_content')
    def test_iterative_project_agent(self, mock_gen):
        """Test IterativeProjectAgent autonomous coding loop."""
        import agent_module
        ipa = agent_module.IterativeProjectAgent()
        
        mock_resp = MagicMock()
        mock_resp.text = "<DONE>"
        mock_gen.return_value = mock_resp
        
        # Run execution loop and check it exits cleanly on first iteration
        with patch('os.makedirs') as mock_mkdir, patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            ipa.execute_loop("test_project", "instructions content")
            
        mock_gen.assert_called_once()

    @patch('agent_module.model.generate_content')
    def test_orchestrator_agent(self, mock_gen):
        """Test OrchestratorAgent planning and query decomposition."""
        import agent_module
        oa = agent_module.OrchestratorAgent()
        
        mock_resp = MagicMock()
        mock_resp.text = '{"tasks": [{"id": "task_1", "agent": "memory_agent", "query": "recall test", "depends_on": []}]}'
        mock_gen.return_value = mock_resp
        
        plan = oa.decompose_request("Who am I?")
        self.assertIsNotNone(plan)
        self.assertEqual(plan["tasks"][0]["id"], "task_1")

    @patch('subprocess.Popen')
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('time.sleep')
    def test_project_agent_fallback_on_broken_venv(self, mock_sleep, mock_exists, mock_run, mock_popen):
        """Test ProjectAgent server launch falling back to primary python when sandbox fails."""
        import agent_module
        pa = agent_module.ProjectAgent()
        pa.project_path = "dummy_path"
        
        # mock exists for venv files
        mock_exists.side_effect = lambda path: True if ".venv" in path else False
        
        # mock run check: 'from flask import Flask' fails in venv
        mock_val_res = MagicMock()
        mock_val_res.returncode = 1
        mock_run.return_value = mock_val_res
        
        # mock popen to return a running mock process
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        
        # Run environment check & launch setup
        python_to_run = pa.launch_with_autofix()
        
        # Verify it returns local flask server URL
        self.assertEqual(python_to_run, "http://127.0.0.1:5000")
        mock_popen.assert_called_once()
        # Verify it passed sys.executable (primary environment python) to Popen
        called_args = mock_popen.call_args[0][0]
        self.assertEqual(called_args[0], sys.executable)


class TestJarvisCoreClass(unittest.TestCase):
    @patch('jarvis.SpeechRecognizer')
    @patch('jarvis.ApplicationController')
    @patch('jarvis.VisionSystem')
    @patch('jarvis.ContactManager')
    @patch('jarvis.AIBrain')
    @patch('jarvis.start_voice_thread')
    def test_jarvis_initialization(self, mock_voice, mock_brain, mock_cm, mock_vs, mock_ac, mock_sr):
        """Test JARVIS main class instantiation and sub-system connection."""
        import jarvis
        bot = jarvis.JARVIS()
        self.assertIsNotNone(bot.ears)
        self.assertIsNotNone(bot.automation)
        self.assertIsNotNone(bot.vision)
        self.assertIsNotNone(bot.contacts)
        self.assertIsNotNone(bot.brain)

    @patch('os.listdir')
    @patch('importlib.util.spec_from_file_location')
    def test_jarvis_load_skills(self, mock_spec, mock_listdir):
        """Test JARVIS dynamic skills loading logic."""
        import jarvis
        mock_listdir.return_value = ["dummy_skill.py", "__init__.py"]
        
        mock_module = MagicMock()
        mock_module.get_triggers.return_value = ["dummy trigger"]
        mock_module.execute.return_value = "executed dummy skill"
        
        mock_spec.return_value.loader.exec_module = lambda m: setattr(m, "get_triggers", mock_module.get_triggers) or setattr(m, "execute", mock_module.execute)
        
        with patch('jarvis.SpeechRecognizer'), patch('jarvis.ApplicationController'), patch('jarvis.VisionSystem'), patch('jarvis.ContactManager'), patch('jarvis.AIBrain'), patch('jarvis.start_voice_thread'):
            bot = jarvis.JARVIS()
            self.assertGreater(len(bot.skills), 0)


class TestJarvisGUI(unittest.TestCase):
    def test_gui_face_widget_states(self):
        """Test FaceWidget states update internal color values correctly."""
        import jarvis_gui
        widget = jarvis_gui.FaceWidget()
        
        widget.set_state("idle")
        self.assertEqual(widget.color.name(), "#f0f0f0")
        
        widget.set_state("listening")
        self.assertEqual(widget.color.name(), "#00ff64")
        
        widget.set_state("talking")
        self.assertEqual(widget.color.name(), "#ff3232")
        
        widget.set_state("thinking")
        self.assertEqual(widget.color.name(), "#b400ff")


class TestJarvisDashboard(unittest.TestCase):
    def test_dashboard_imports(self):
        """Test that dashboard Streamlit configuration compiles successfully."""
        import dashboard
        self.assertIsNotNone(dashboard.st)


class TestJarvisFallbackRouting(unittest.TestCase):
    @patch('ai_module.AIBrain._get_ollama_fallback')
    @patch('ai_module.AIBrain._call_gemini_api')
    def test_conversational_ollama_primary_fallback(self, mock_gemini, mock_ollama):
        """Test conversation uses Ollama first and falls back to Gemini when Ollama fails."""
        import ai_module
        import config
        
        # Configure conversation provider as ollama
        config.CONVERSATION_PROVIDER = "ollama"
        config.API_KEYS_POOL = ["test_key"]
        
        brain = ai_module.AIBrain()
        brain.api_keys = ["test_key"]
        
        # Mock Ollama fallback to raise an exception
        mock_ollama.side_effect = RuntimeError("Ollama Server Offline")
        
        # Mock Gemini call
        mock_resp = MagicMock()
        mock_resp.text = "Gemini fallback reply."
        mock_gemini.return_value = mock_resp
        
        with patch('google.genai.Client') as mock_client:
            res = brain.get_response("hello")
            
        self.assertEqual(res, "Gemini fallback reply.")
        mock_ollama.assert_called_once()
        mock_gemini.assert_called_once()

    @patch('agent_module.RotatingModel._call_local_ollama')
    def test_coding_ollama_strict(self, mock_ollama):
        """Test coding tasks strictly use Ollama and never fall back to Gemini."""
        import agent_module
        import config
        
        # Configure coding provider as ollama
        config.CODING_PROVIDER = "ollama"
        
        model = agent_module.RotatingModel('gemini-2.5-flash')
        
        mock_ollama.return_value = agent_module.MockResponse("Ollama code output.")
        
        res = model.generate_content("write some python code")
        self.assertEqual(res.text, "Ollama code output.")
        mock_ollama.assert_called_once()


if __name__ == "__main__":
    unittest.main()

