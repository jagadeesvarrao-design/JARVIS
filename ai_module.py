import config
import identity
import os
import re
import time
import requests # NEW: Required for Ollama API calls

class AIBrain:
    def __init__(self):
        self.chat_history = []
        self.client = None
        self.api_keys = config.API_KEYS_POOL
        self.current_key_index = 0
        
        # --- RPM TRACKER ---
        self.request_count = 0 
        self.RPM_THRESHOLD = 18 
        
        try:
            self.models = config.AI_MODELS
        except AttributeError:
            self.models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
            
        self.current_model_index = 0

    def _connect_client(self):
        """Connects the client and resets the counter for the new key"""
        try:
            from google import genai
            if not self.api_keys:
                self.client = None
                print("❌ Connection Error: No active keys in the pool.")
                return
            current_key = self.api_keys[self.current_key_index]
            self.client = genai.Client(api_key=current_key)
            self.request_count = 0
            print(f"🧠 AI BRAIN CONNECTED (Key #{self.current_key_index + 1} | Model: {self.models[self.current_model_index]})")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    def _rotate_key(self):
        """Standard rotation for errors or RPM limits"""
        if not self.api_keys:
            self.client = None
            return
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._connect_client()

    # =================================================================
    # NEW: OLLAMA FALLBACK ENGINE
    # =================================================================
    def _get_ollama_fallback(self, user_text, context):
        print("⚠️ WARNING: Cloud API unreachable. Rerouting to Local Neural Engine (Ollama)...")
        
        # Self-healing model resolution: check what models are available locally
        url_tags = config.OLLAMA_URL.replace("/api/generate", "/api/tags")
        resolved_model = config.OLLAMA_MODEL
        try:
            tags_resp = requests.get(url_tags, timeout=3.0)
            if tags_resp.status_code == 200:
                available_models = [m["name"] for m in tags_resp.json().get("models", [])]
                if available_models:
                    model_found = False
                    for am in available_models:
                        if resolved_model.lower() in am.lower():
                            resolved_model = am
                            model_found = True
                            break
                    if not model_found:
                        resolved_model = available_models[0]
                        print(f"⚠️ Configured model '{config.OLLAMA_MODEL}' not found. Using installed model '{resolved_model}'.")
                else:
                    return "Sir, no local models are installed in Ollama. Please run 'ollama pull llama3' in your terminal."
            else:
                return "My local neural engine (Ollama) is offline or not responding, Sir."
        except requests.RequestException:
            print("🚀 Local Ollama server is offline. Attempting to start it...")
            import subprocess
            try:
                ollama_bin = "ollama"
                default_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Ollama\ollama.exe")
                if os.path.exists(default_path):
                    ollama_bin = default_path
                subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Poll port for up to 10 seconds
                server_started = False
                for _ in range(10):
                    try:
                        tags_resp = requests.get(url_tags, timeout=1.0)
                        if tags_resp.status_code == 200:
                            server_started = True
                            break
                    except Exception:
                        pass
                    time.sleep(1.0)
                
                if server_started:
                    available_models = [m["name"] for m in tags_resp.json().get("models", [])]
                    if available_models:
                        model_found = False
                        for am in available_models:
                            if resolved_model.lower() in am.lower():
                                resolved_model = am
                                model_found = True
                                break
                        if not model_found:
                            resolved_model = available_models[0]
                            print(f"⚠️ Configured model '{config.OLLAMA_MODEL}' not found. Using installed model '{resolved_model}'.")
                    else:
                        return "Sir, no local models are installed in Ollama. Please run 'ollama pull llama3' in your terminal."
                else:
                    return "Sir, my cloud connection is down and the local Ollama server failed to start."
            except Exception as launch_err:
                print(f"❌ Failed to launch Ollama: {launch_err}")
                return "Sir, my cloud connection is down and the local Ollama server is not running."
        except Exception as te:
            print(f"⚠️ Ollama model list check failed: {te}")
            pass

        full_prompt = (
            f"You are {identity.BOT_NAME}, created by {config.OWNER_NAME}. "
            f"Personality: Witty, loyal, helpful.\n\n"
            f"Context: {context}\n"
            f"USER: {user_text}"
        )
        
        payload = {
            "model": resolved_model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(config.OLLAMA_URL, json=payload, timeout=120)
            if response.status_code == 200:
                answer = response.json().get("response", "I could not generate a thought, Sir.")
                return answer.strip()
            elif response.status_code == 404:
                return f"Sir, the model '{resolved_model}' was not found in Ollama. Please download it using 'ollama pull {resolved_model}'."
            else:
                return f"My local neural engine returned error status {response.status_code}, Sir."
        except requests.exceptions.ConnectionError:
            return "Sir, my cloud connection is down and the local Ollama server is not running."
        except Exception as e:
            return f"Local Engine Error: {e}"

    def _compress_response(self, original_prompt, long_response, max_lines, current_model, system_rules):
        """Uses the AI model to compress a response to fit within a strict line limit."""
        compression_prompt = (
            f"The previous response to the user's prompt was too long. It had {len([l for l in long_response.splitlines() if l.strip()])} lines.\n"
            f"You MUST compress/rewrite this response so that it is strictly {max_lines} lines or fewer (excluding blank lines).\n"
            f"For coding tasks, write the code in a highly compact/dense format (using single-line definitions, ternary operators, semicolons, and no empty lines within the code block).\n"
            f"Ensure the rewritten response is complete, correct, and answers the user's request: '{original_prompt}'.\n"
            f"Previous response to compress:\n{long_response}"
        )
        if self.client and current_model and system_rules:
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=compression_prompt,
                    config=types.GenerateContentConfig(system_instruction=system_rules)
                )
                answer = response.text if response.text else long_response
                answer = answer.replace("*", "")
                if "MEMORY:" in answer: answer = answer.split("MEMORY:")[0]
                answer = re.sub(r'\[(?!(?i:IMAGE|SIMPLE_IMAGE_REQUEST|Image of)).*?\]', '', answer).strip()
                return answer
            except Exception as e:
                print(f"⚠️ Compression error via Gemini: {e}")
        
        # Fallback manual compression: try to clean up lines, or truncate
        lines = long_response.splitlines()
        non_empty = [l for l in lines if l.strip()]
        if len(non_empty) > max_lines:
            return "\n".join(non_empty[:max_lines])
        return long_response

    def _enforce_line_limits(self, user_text, answer, current_model=None, system_rules=None):
        is_complex = False
        if "```" in answer or any(kw in user_text.lower() for kw in ["code", "python", "function", "program", "script", "regex", "develop", "system design"]):
            is_complex = True

        non_empty_lines = [l for l in answer.splitlines() if l.strip()]
        line_count = len(non_empty_lines)

        if is_complex:
            if line_count >= 12:
                print(f"⚠️ Complex response is too long ({line_count} lines). Compressing...")
                answer = self._compress_response(user_text, answer, 11, current_model, system_rules)
        else:
            if line_count > 6:
                print(f"⚠️ Simple response is too long ({line_count} lines). Compressing...")
                answer = self._compress_response(user_text, answer, 6, current_model, system_rules)
        return answer

    # =================================================================
    # PRIMARY ROUTING LOGIC
    # =================================================================
    def get_response(self, user_text, image_path=None, context=None):
        use_ollama = False
        if hasattr(config, "CONVERSATION_PROVIDER") and config.CONVERSATION_PROVIDER == "ollama":
            use_ollama = True
            
        # Lazy client initialization on first active API query
        if not use_ollama and self.client is None and self.api_keys:
            self._connect_client()
            
        if use_ollama or not self.client or not self.api_keys: 
            # If completely failed to connect to Gemini at boot, force local
            raw_answer = self._get_ollama_fallback(user_text, context)
            return self._enforce_line_limits(user_text, raw_answer)

        if self.request_count >= self.RPM_THRESHOLD:
            print(f"🔄 Key #{self.current_key_index + 1} reached 18 RPM safety limit. Rotating...")
            self._rotate_key()

        max_retries = len(self.api_keys) * 2
        attempt = 0

        while attempt < max_retries:
            current_model = self.models[self.current_model_index]
            
            try:
                # 1. Retrieve Memory & Self-Awareness
                if attempt == 0:
                    try:
                        from memory_moduler import MemorySystem 
                        mem = MemorySystem()
                        user_facts = mem.recall_facts() or "No facts."
                        custom_rules = mem.recall_rules()
                        user_prefs = mem.recall_preferences()
                        user_profile = mem.get_user_profile()
                    except:
                        user_facts = "Unavailable"
                        custom_rules = []
                        user_prefs = {}
                        user_profile = {}
                        
                    try:
                        self_awareness = identity.get_self_awareness_context()
                    except:
                        self_awareness = ""
                
                # 2. Answering length and complexity rules
                style = user_profile.get("conversational_style", "conversational")
                interaction = user_profile.get("interaction_type", "text")
                frequent_topics = user_profile.get("frequent_topics", {})
                top_topics = sorted(frequent_topics.items(), key=lambda x: x[1], reverse=True)
                fav_topic = top_topics[0][0] if top_topics else "general_info"

                complexity_rules = (
                    f"COMPLEXITY & ANSWER LENGTH RULES:\n"
                    f"   - You MUST dynamically assess the complexity of the Operator's request.\n"
                    f"   - For simple topics (e.g. general knowledge facts, country details, basic definitions, greeting chit-chat, simple conversions), write a response that spans exactly 3 to 6 lines of text (separate key ideas or sentences onto newlines). Do NOT output a single long line or exceed 6 lines.\n"
                    f"   - For complex topics (e.g. coding, programming logic, code debugging, complex system design, research requests), your entire response (including all code blocks, markdown tags, and explanations) MUST be strictly less than 12 lines of text (maximum 11 lines total, excluding empty lines). For programming queries, make code blocks extremely compact (e.g., use single-line solutions, ternary operators, avoid empty lines inside code blocks) and limit explanations to at most 1-2 short sentences. NEVER exceed 11 lines of text total.\n"
                    f"   - Always keep answers brief, clear, and direct. Focus purely on helping the Operator understand the topic clearly and quickly, with absolutely no fluff or filler.\n"
                    f"   - Dynamically adapt to the Operator's style: '{style}' (e.g., if 'technical', favor code blocks; if 'witty', add dry humor; if 'brief', favor concise answers).\n"
                    f"   - Tailor explanations considering the Operator's interest in the topic '{fav_topic}'.\n"
                )

                # 3. System Rules
                system_rules = (
                    f"You are {identity.BOT_NAME}, created by {config.OWNER_NAME}.\n"
                    f"Personality: {identity.PERSONALITY}\n"
                    f"{complexity_rules}\n"
                    f"CRITICAL RULES:\n"
                    f"   - If the operator asks you to greet someone (e.g., 'greet my mother', 'say hello to my father', 'greet them'), you must speak the greeting directly to that person in the first person as JARVIS (using the target language if specified), rather than explaining how the operator should greet them or translating the greeting.\n"
                    f"   - If the user asks for an image, you MUST end your response with this EXACT tag: [IMAGE: <search_query>]\n"
                    f"   - If the user asks about a person who is not a well-known historical or public figure, and there is no information about them in the MEMORY block, do not hallucinate or make up details. Instead, politely state that you do not have information about them, or ask the user to tell you more about them so you can remember.\n"
                )
                
                if self_awareness:
                    system_rules += f"\n{self_awareness}\n"
                    
                if custom_rules:
                    system_rules += "\nDYNAMIC RULES LEARNED FROM CONVERSATIONS (YOU MUST OBEY THESE):\n"
                    for rule in custom_rules:
                        system_rules += f"   - {rule}\n"
                        
                if user_prefs:
                    system_rules += "\nUSER PREFERENCES LEARNED (YOU MUST ADAPT TO THESE):\n"
                    for k, v in user_prefs.items():
                        system_rules += f"   - Preferred {k}: {v}\n"
                        
                system_rules += (
                    f"\nSILENCE: Do NOT read the memory block.\n"
                    f"MEMORY OF FACTS: [{user_facts}]"
                )
                
                # 3. Request Execution
                self.request_count += 1
                
                if image_path:
                    import PIL.Image as PIL_Image
                    from google.genai import types
                    img = PIL_Image.open(image_path)
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=[img, "Describe this image."],
                        config=types.GenerateContentConfig(system_instruction=system_rules)
                    )
                    img.close()
                else:
                    from google.genai import types
                    full_prompt = f"Context: {context}\nUSER: {user_text}"
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(system_instruction=system_rules)
                    )
                
                # 4. Cleaning
                answer = response.text if response.text else "I'm listening."
                answer = answer.replace("*", "")
                if "MEMORY:" in answer: answer = answer.split("MEMORY:")[0]
                answer = re.sub(r'\[(?!(?i:IMAGE|SIMPLE_IMAGE_REQUEST|Image of)).*?\]', '', answer).strip()

                # 5. Enforce line limits
                answer = self._enforce_line_limits(user_text, answer, current_model, system_rules)

                self.chat_history.append(f"User: {user_text}")
                self.chat_history.append(f"Jarvis: {answer}")

                return answer

            # --- THE FALLBACK ROUTER ---
            except Exception as e:
                error_msg = str(e).lower()
                
                # 1. 404 Errors (Model Not Found) -> Rotate Model and retry
                if any(x in error_msg for x in ["404", "not found"]):
                    self.current_model_index = (self.current_model_index + 1) % len(self.models)
                    attempt += 1
                    continue
                
                # 2. Terminal Key Errors (400 Expired, 403 Leaked/Blocked) -> Remove key from pool, rotate, and retry
                if any(x in error_msg for x in ["400", "invalid_argument", "403", "permission_denied", "expired", "leaked"]):
                    bad_key = self.api_keys[self.current_key_index]
                    print(f"❌ Key #{self.current_key_index + 1} is permanently invalid (expired/leaked). Disabling key.")
                    if bad_key in config.API_KEYS_POOL:
                        config.API_KEYS_POOL.remove(bad_key)
                    # Refresh active keys list from pool
                    self.api_keys = config.API_KEYS_POOL
                    if self.api_keys:
                        self.current_key_index = self.current_key_index % len(self.api_keys)
                    else:
                        self.client = None
                    self._connect_client()
                    attempt += 1
                    continue

                # 2.5 Network/DNS Connection Errors -> Do not rotate, immediately fallback to local Ollama
                connection_errors = [
                    "getaddrinfo", "connecterror", "connection error", "dns error", 
                    "no connections available", "network unreachable", "socket.timeout", 
                    "timed out", "connection refused", "failed to establish a new connection",
                    "cannot connect"
                ]
                if any(x in error_msg for x in connection_errors):
                    print("🌐 [AIBRAIN]: Network connection issue detected. Bypassing cloud API retries.")
                    break

                # 3. Other errors (429 Quota, 503 Overload, 504 Timeout, Connection/Network) -> Rotate Key and Model and retry
                print(f"⚠️ API Error on Key #{self.current_key_index + 1} ({current_model}): {e}. Rotating key and model...")
                self._rotate_key()
                self.current_model_index = (self.current_model_index + 1) % len(self.models)
                attempt += 1
                continue

        # If all keys and retries exhaust, trigger Ollama as the absolute last resort
        raw_answer = self._get_ollama_fallback(user_text, context)
        return self._enforce_line_limits(user_text, raw_answer)