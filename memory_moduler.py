import json
import os
import threading
import re

class MemorySystem:
    def __init__(self, filename="memory.json"):
        self.filename = filename
        self.data = self._load_memory()

    def _load_memory(self):
        if not os.path.exists(self.filename):
            return {"facts": [], "preferences": {}, "custom_rules": []}
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                content = json.load(f)
                if isinstance(content, dict):
                    # Ensure all required structure exists, preserving existing data
                    if "facts" not in content:
                        content["facts"] = []
                    if "preferences" not in content:
                        content["preferences"] = {}
                    if "custom_rules" not in content:
                        content["custom_rules"] = []
                    if "user_profile" not in content:
                        content["user_profile"] = {
                            "conversational_style": "conversational",
                            "frequent_topics": {},
                            "interaction_type": "text"
                        }
                    return content
                return {"facts": [], "preferences": {}, "custom_rules": [], "user_profile": {"conversational_style": "conversational", "frequent_topics": {}, "interaction_type": "text"}}
        except Exception:
            return {"facts": [], "preferences": {}, "custom_rules": [], "user_profile": {"conversational_style": "conversational", "frequent_topics": {}, "interaction_type": "text"}}

    def get_user_profile(self):
        if "user_profile" not in self.data:
            self.data["user_profile"] = {
                "conversational_style": "conversational",
                "frequent_topics": {},
                "interaction_type": "text"
            }
        return self.data["user_profile"]

    def remember_fact(self, text):
        clean_fact = text.replace("remember that", "").replace("remember", "").strip()
        clean_fact = clean_fact.capitalize()
        if not clean_fact:
            return "I didn't catch what to remember."
        
        # Check for duplication
        if clean_fact not in self.data["facts"]:
            self.data["facts"].append(clean_fact)
            self._save_memory()
            return f"Saved fact: '{clean_fact}'"
        return f"I already remember that: '{clean_fact}'"

    def remember_rule(self, text):
        clean_rule = text.strip()
        if not clean_rule:
            return "I cannot remember an empty rule."
        if clean_rule not in self.data["custom_rules"]:
            self.data["custom_rules"].append(clean_rule)
            self._save_memory()
            return f"Saved rule: '{clean_rule}'"
        return "I already have that rule recorded."

    def set_preference(self, key, value):
        self.data["preferences"][key] = value
        self._save_memory()
        return f"Saved preference: {key} = {value}"

    def recall(self):
        # Backward compatibility recall method
        return self.recall_facts()

    def recall_facts(self):
        if not self.data.get("facts"):
            return None
        return " | ".join(self.data["facts"])

    def recall_rules(self):
        return self.data.get("custom_rules", [])

    def recall_preferences(self):
        return self.data.get("preferences", {})

    def forget_fact(self, text_or_idx):
        try:
            idx = int(text_or_idx) - 1
            if 0 <= idx < len(self.data["facts"]):
                removed = self.data["facts"].pop(idx)
                self._save_memory()
                return f"Forgotten fact: '{removed}'"
        except ValueError:
            text_lower = text_or_idx.lower().strip()
            for fact in list(self.data["facts"]):
                if text_lower in fact.lower():
                    self.data["facts"].remove(fact)
                    self._save_memory()
                    return f"Forgotten fact: '{fact}'"
        return "I couldn't find that fact in my memory banks."

    def forget_rule(self, text_or_idx):
        try:
            idx = int(text_or_idx) - 1
            if 0 <= idx < len(self.data["custom_rules"]):
                removed = self.data["custom_rules"].pop(idx)
                self._save_memory()
                return f"Removed behavior rule: '{removed}'"
        except ValueError:
            text_lower = text_or_idx.lower().strip()
            for rule in list(self.data["custom_rules"]):
                if text_lower in rule.lower():
                    self.data["custom_rules"].remove(rule)
                    self._save_memory()
                    return f"Removed behavior rule: '{rule}'"
        return "I couldn't find that rule in my active directives."

    def forget_preference(self, key):
        key_lower = key.lower().strip()
        for k in list(self.data["preferences"].keys()):
            if k.lower() == key_lower:
                val = self.data["preferences"].pop(k)
                self._save_memory()
                return f"Purged preference: '{k}' (was: {val})"
        return "I couldn't find that preference key."

    def _save_memory(self):
        temp_filename = self.filename + ".tmp"
        try:
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            if os.path.exists(temp_filename):
                os.replace(temp_filename, self.filename)
        except Exception as e:
            print(f"Error saving memory file: {e}")

    def analyze_and_learn_from_chat(self, user_text, jarvis_text, run_sync=False):
        """Spawns an asynchronous background thread to analyze conversation turn and extract rules/preferences/facts."""
        # Don't waste API calls on simple greetings, short words, or exit commands
        simple_words = ["exit", "quit", "jarvis", "yes", "no", "ok", "yeah", "thanks", "hello", "hi", "hey"]
        clean_user = user_text.lower().strip()
        if len(clean_user) < 6 or clean_user in simple_words:
            return

        def _bg_worker():
            try:
                from ai_module import AIBrain
                brain = AIBrain()
                
                # Double-check: Make sure the brain client exists and API key is present
                if not brain.client and not brain.api_keys:
                    return

                prompt = (
                    "You are Jarvis's Cognitive Memory Processor.\n"
                    "Analyze this conversation turn between the Operator (User) and Jarvis:\n"
                    f"Operator: \"{user_text}\"\n"
                    f"Jarvis: \"{jarvis_text}\"\n\n"
                    "Identify if the operator has explicitly stated, corrected, or set:\n"
                    "1. A personal fact about themselves, their relationships, or their environment (e.g. 'I like prawns curry', 'my favorite color is black').\n"
                    "2. A personal preference or habit (e.g., preferred programming language, default app views, volume/rate levels).\n"
                    "3. A custom rule or behavioral directive for Jarvis (e.g., 'always speak in english', 'do not write comments in code', 'never reply with more than one sentence').\n\n"
                    "Also, analyze the operator's conversational style and the topic of discussion:\n"
                    "- conversational_style: Choose the best fit from: 'brief', 'detailed', 'technical', 'conversational', 'witty', 'formal'.\n"
                    "- topic: Classify the topic into one of: 'coding', 'shopping', 'system_automation', 'general_info', 'music', 'casual_chat'.\n"
                    "- interaction_type: Classify based on whether the input text looks spoken/conversational ('voice') or concise/direct typed command ('text').\n\n"
                    "Return a valid JSON object matching this schema:\n"
                    "{\n"
                    "  \"new_facts\": [\"extracted fact 1\", ...],\n"
                    "  \"new_preferences\": {\"preference_key\": \"preference_value\", ...},\n"
                    "  \"new_rules\": [\"extracted rule 1\", ...],\n"
                    "  \"conversational_style\": \"brief\" | \"detailed\" | \"technical\" | \"conversational\" | \"witty\" | \"formal\",\n"
                    "  \"topic\": \"coding\" | \"shopping\" | \"system_automation\" | \"general_info\" | \"music\" | \"casual_chat\",\n"
                    "  \"interaction_type\": \"voice\" | \"text\"\n"
                    "}\n"
                    "Extract ONLY items that are clearly stated or corrected by the user. Do not invent or guess. "
                    "If nothing new is found for a field, you MUST return an empty list or object for that field (e.g. \"new_facts\": []). "
                    "Do NOT include any conversational text, formatting, or markdown fences (like ```json). Return the raw JSON string only."
                )

                response_text = brain.get_response(prompt)
                if not response_text:
                    return

                # Robust JSON extraction
                json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', response_text)
                if json_match:
                    raw_json = json_match.group(1)
                else:
                    raw_json = response_text.strip()

                raw_json = re.sub(r'^```json\s*', '', raw_json, flags=re.IGNORECASE)
                raw_json = re.sub(r'\s*```$', '', raw_json, flags=re.IGNORECASE)
                raw_json = raw_json.strip()

                # Self-heal invalid LLM trailing-colon or missing-value syntax (e.g., "key": ,)
                raw_json = re.sub(r':\s*,', ': [],', raw_json)
                raw_json = re.sub(r':\s*([\}\]])', r': null \1', raw_json)

                try:
                    learned = json.loads(raw_json)
                except Exception:
                    import ast
                    try:
                        learned = ast.literal_eval(raw_json)
                    except Exception:
                        return

                if not isinstance(learned, dict):
                    return

                # Reload memory to avoid race conditions with other writes
                self.data = self._load_memory()
                updated = False
                
                # Standalone log function to write directly to jarvis_logs.jsonl (avoiding circular/thread import side effects of jarvis.py)
                def log_to_dashboard(log_type, message):
                    log_file = "jarvis_logs.jsonl"
                    import datetime
                    entry = {
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "type": log_type, 
                        "message": message
                    }
                    try:
                        with open(log_file, "a", encoding="utf-8") as f_log:
                            f_log.write(json.dumps(entry) + "\n")
                    except Exception:
                        pass

                # 1. Facts
                for fact in learned.get("new_facts", []):
                    clean_fact = fact.capitalize().strip()
                    if clean_fact and clean_fact not in self.data["facts"]:
                        self.data["facts"].append(clean_fact)
                        updated = True
                        log_to_dashboard("system", f"🧠 [Self-Learning]: Memorized new fact: '{clean_fact}'")
                        print(f"🧠 [LEARNED FACT]: {clean_fact}")

                # 2. Rules
                for rule in learned.get("new_rules", []):
                    clean_rule = rule.strip()
                    if clean_rule and clean_rule not in self.data["custom_rules"]:
                        self.data["custom_rules"].append(clean_rule)
                        updated = True
                        log_to_dashboard("system", f"🧠 [Self-Learning]: Learned new rule: '{clean_rule}'")
                        print(f"🧠 [LEARNED RULE]: {clean_rule}")

                # 3. Preferences
                for pref_key, pref_val in learned.get("new_preferences", {}).items():
                    k_clean = pref_key.strip().lower().replace(" ", "_")
                    v_clean = str(pref_val).strip()
                    if k_clean and (k_clean not in self.data["preferences"] or self.data["preferences"][k_clean] != v_clean):
                        self.data["preferences"][k_clean] = v_clean
                        updated = True
                        log_to_dashboard("system", f"🧠 [Self-Learning]: Stored preference: {k_clean} = {v_clean}")
                        print(f"🧠 [LEARNED PREFERENCE]: {k_clean} = {v_clean}")

                # 4. User Profile Silent updates
                style = learned.get("conversational_style", "conversational")
                topic = learned.get("topic", "casual_chat")
                interaction = learned.get("interaction_type", "text")
                
                if "user_profile" not in self.data:
                    self.data["user_profile"] = {
                        "conversational_style": "conversational",
                        "frequent_topics": {},
                        "interaction_type": "text"
                    }
                
                self.data["user_profile"]["conversational_style"] = style
                self.data["user_profile"]["interaction_type"] = interaction
                
                topics_dict = self.data["user_profile"].setdefault("frequent_topics", {})
                topics_dict[topic] = topics_dict.get(topic, 0) + 1
                updated = True
                print(f"🧠 [USER PROFILE UPDATED]: style={style}, topic={topic}, interaction={interaction}")

                if updated:
                    self._save_memory()

            except Exception as e:
                print(f"⚠️ [Self-Learning Engine Error]: {e}")

        if run_sync:
            _bg_worker()
        else:
            # Start thread asynchronously
            threading.Thread(target=_bg_worker, daemon=True).start()