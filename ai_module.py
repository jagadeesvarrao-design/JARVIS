import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import config
import identity
import os
import re
import time
import requests 

def is_multilingual_request(text):
    if not text:
        return False
    # Check for non-ASCII characters of Indian languages (Telugu: \u0C00-\u0C7F, Hindi: \u0900-\u097F)
    if any(ord(char) > 127 for char in text):
        if re.search(r'[\u0C00-\u0C7F\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0B00-\u0B7F\u0B80-\u0BFF\u0C80-\u0CFF\u0D00-\u0D7F]', text):
            return True
    
    # Check for language names in the query
    non_english_langs = [
        "telugu", "hindi", "tamil", "kannada", "malayalam", "bengali", "gujarati", 
        "marathi", "punjabi", "urdu", "sanskrit", "spanish", "french", "german", 
        "italian", "japanese", "chinese", "russian", "korean", "portuguese"
    ]
    words = re.findall(r'\b\w+\b', text.lower())
    for lang in non_english_langs:
        if lang in words:
            return True
    return False

class AIBrain:
    def __init__(self):
        self.chat_history = []
        self.client = None
        self.api_keys = config.API_KEYS_POOL
        self.current_key_index = 0
        self.chatgpt_cooldown_until = 0.0
        
        # --- RPM TRACKER ---
        self.request_count = 0 
        self.RPM_THRESHOLD = 18 
        
        try:
            self.models = config.AI_MODELS
        except AttributeError:
            self.models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]
            
        self.current_model_index = 0

    def _get_available_key_index(self):
        """Finds the first key that is not currently in cooldown."""
        now = time.time()
        for idx in range(len(self.api_keys)):
            check_idx = (self.current_key_index + idx) % len(self.api_keys)
            key = self.api_keys[check_idx]
            cooldown_time = config.KEY_COOLDOWNS.get(key, 0.0)
            if now >= cooldown_time:
                return check_idx
        # If all keys are in cooldown, pick the one with the earliest expiry
        earliest_idx = self.current_key_index
        earliest_time = float('inf')
        for idx, key in enumerate(self.api_keys):
            cooldown_time = config.KEY_COOLDOWNS.get(key, 0.0)
            if cooldown_time < earliest_time:
                earliest_time = cooldown_time
                earliest_idx = idx
        return earliest_idx

    def _connect_client(self):
        """Connects the client and resets the counter for the new key"""
        try:
            from google import genai
            if not self.api_keys:
                self.client = None
                print("❌ Connection Error: No active keys in the pool.")
                return
            self.current_key_index = self._get_available_key_index()
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
    # NEW: CHATGPT FALLBACK ENGINE
    # =================================================================
    def _get_chatgpt_fallback(self, user_text, context, system_rules):
        api_key = getattr(config, "OPENAI_API_KEY", None)
        model = getattr(config, "GPT_MODEL", "gpt-4o-mini")
        
        if not api_key:
            return None
            
        now = time.time()
        if now < self.chatgpt_cooldown_until:
            print("⚠️ [AIBRAIN]: ChatGPT fallback is currently on cooldown. Skipping.")
            return None
            
        print(f"🚀 [AIBRAIN]: Attempting ChatGPT fallback using model '{model}'...")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        messages = [
            {"role": "system", "content": system_rules},
            {"role": "user", "content": f"Context: {context}\nUSER: {user_text}"}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 150
        }
        
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=15.0)
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"].strip()
                print("✅ [AIBRAIN]: ChatGPT response retrieved successfully.")
                return answer
            else:
                print(f"⚠️ [AIBRAIN]: ChatGPT API returned code {response.status_code}: {response.text}")
                if response.status_code in [401, 403, 429] or "insufficient_quota" in response.text:
                    print("⚠️ [AIBRAIN]: ChatGPT API has quota or auth issues. Putting ChatGPT fallback on 1-hour cooldown.")
                    self.chatgpt_cooldown_until = time.time() + 3600.0
                return None
        except Exception as e:
            print(f"⚠️ [AIBRAIN]: ChatGPT fallback connection failed: {e}")
            return None

    # =================================================================
    # NEW: OLLAMA FALLBACK ENGINE
    # =================================================================
    def _get_ollama_fallback(self, user_text, context, raise_on_error=False, model_name=None):
        if raise_on_error:
            print("🧠 [AIBRAIN]: Routing conversation directly to local Ollama...")
        else:
            print("⚠️ WARNING: Cloud API unreachable. Rerouting to Local Neural Engine (Ollama)...")
        
        # Self-healing model resolution: check what models are available locally
        url_tags = config.OLLAMA_URL.replace("/api/generate", "/api/tags")
        target_model = model_name if model_name else getattr(config, "OLLAMA_MODEL", "llama")
        resolved_model = target_model
        try:
            tags_resp = requests.get(url_tags, timeout=5.0)
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
                        print(f"⚠️ Configured model '{target_model}' not found. Using installed model '{resolved_model}'.")
                else:
                    if raise_on_error: raise RuntimeError("No local models are installed in Ollama.")
                    return "Sir, no local models are installed in Ollama. Please run 'ollama pull llama3' in your terminal."
            else:
                if raise_on_error: raise RuntimeError("My local neural engine (Ollama) is offline or not responding.")
                return "My local neural engine (Ollama) is offline or not responding, Sir."
        except requests.RequestException as re_err:
            if raise_on_error and "connection refused" in str(re_err).lower():
                raise RuntimeError("Local Ollama server is offline.")
            
            # Check if an Ollama process is already running on the OS
            import psutil
            ollama_running = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        ollama_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if ollama_running:
                print("🚀 [SYSTEM]: Ollama process is already running but not responding yet. Waiting for it to initialize...")
            else:
                print("🚀 [SYSTEM]: Local Ollama server is offline. Attempting to start it in background...")
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
                except Exception as launch_err:
                    print(f"❌ Failed to launch Ollama: {launch_err}")
                    if raise_on_error: raise RuntimeError(f"Ollama server launch failed: {launch_err}")
                    return "Sir, my cloud connection is down and the local Ollama server is not running."

            # Poll port for up to 15 seconds with 3.0s timeout
            server_started = False
            for _ in range(15):
                try:
                    tags_resp = requests.get(url_tags, timeout=3.0)
                    if tags_resp.status_code == 200:
                        server_started = True
                        break
                except Exception:
                    pass
                time.sleep(1.0)
                
            if server_started:
                try:
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
                            print(f"⚠️ Configured model '{target_model}' not found. Using installed model '{resolved_model}'.")
                    else:
                        if raise_on_error: raise RuntimeError("No local models are installed in Ollama.")
                        return "Sir, no local models are installed in Ollama. Please run 'ollama pull llama3' in your terminal."
                except Exception as parse_err:
                    print(f"⚠️ Failed to parse Ollama models list: {parse_err}")
                    if raise_on_error: raise RuntimeError("Ollama returned an invalid models list.")
                    return "Sir, my local neural engine is online but returned an invalid models list."
            else:
                if raise_on_error: raise RuntimeError("Ollama server failed to start.")
                return "Sir, my cloud connection is down and the local Ollama server failed to start."
        except Exception as te:
            print(f"⚠️ Ollama model list check failed: {te}")
            if raise_on_error: raise RuntimeError(f"Ollama check failed: {te}")
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
            response = requests.post(config.OLLAMA_URL, json=payload, timeout=15.0)
            if response.status_code == 200:
                answer = response.json().get("response", "I could not generate a thought, Sir.")
                return answer.strip()
            elif response.status_code == 404:
                if raise_on_error: raise RuntimeError(f"Model '{resolved_model}' not found in Ollama.")
                return f"Sir, the model '{resolved_model}' was not found in Ollama. Please download it using 'ollama pull {resolved_model}'."
            else:
                if raise_on_error: raise RuntimeError(f"Ollama returned error status {response.status_code}")
                return f"My local neural engine returned error status {response.status_code}, Sir."
        except requests.exceptions.ConnectionError as conn_err:
            if raise_on_error: raise RuntimeError("Connection to Ollama server failed.")
            return "Sir, my cloud connection is down and the local Ollama server is not running."
        except Exception as e:
            if raise_on_error: raise RuntimeError(f"Ollama execution error: {e}")
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

    def _call_gemini_api(self, model, system_rules, full_prompt, image_path=None):
        """Calls the Gemini API with transient error retries (503, 504) using exponential backoff."""
        from google.genai import types
        import random
        
        base_delay = 0.5
        max_transient_attempts = 3
        
        for transient_attempt in range(max_transient_attempts):
            try:
                self.request_count += 1
                if image_path:
                    import PIL.Image as PIL_Image
                    img = PIL_Image.open(image_path)
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[img, "Describe this image."],
                        config=types.GenerateContentConfig(system_instruction=system_rules)
                    )
                    img.close()
                else:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(system_instruction=system_rules)
                    )
                return response
            except Exception as e:
                err_str = str(e).lower()
                is_transient = any(x in err_str for x in ["503", "unavailable", "overloaded", "504", "timeout", "deadline exceeded"])
                
                # If it's a transient error, wait and retry on the same key
                if is_transient and transient_attempt < max_transient_attempts - 1:
                    sleep_time = (2 ** transient_attempt) * base_delay + random.uniform(0.05, 0.15)
                    print(f"⚠️ Gemini API returned transient error (503/504). Retrying in {sleep_time:.2f}s... (Attempt {transient_attempt + 1}/{max_transient_attempts})")
                    time.sleep(sleep_time)
                    continue
                
                raise e

    # =================================================================
    # PRIMARY ROUTING LOGIC
    # =================================================================
    def get_response(self, user_text, image_path=None, context=None):
        system_rules = f"You are {identity.BOT_NAME}, created by {config.OWNER_NAME}.\nPersonality: {identity.PERSONALITY}"
        
        # 1. Retrieve Memory & Self-Awareness
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

        full_prompt = f"Context: {context}\nUSER: {user_text}"
        
        is_multilingual = is_multilingual_request(user_text)
        
        def run_gemini():
            primary_models = self.models
            fallback_models = ["gemini-3.1-flash", "gemini-2.5-flash", "gemini-3.1-pro", "gemini-3.1-flashlite", "gemini-2.0-flash"]
            all_models = primary_models + [m for m in fallback_models if m not in primary_models]

            success = False
            response = None
            chosen_model = None
            now = time.time()
            
            for model in all_models:
                if success:
                    break
                keys_to_try = list(self.api_keys)
                start_idx = self._get_available_key_index()
                
                for i in range(len(keys_to_try)):
                    key_idx = (start_idx + i) % len(keys_to_try)
                    key = keys_to_try[key_idx]
                    if now < config.KEY_COOLDOWNS.get(key, 0.0):
                        if len(keys_to_try) > 1:
                            continue
                    self.current_key_index = key_idx
                    try:
                        from google import genai
                        self.client = genai.Client(api_key=key)
                    except Exception as conn_err:
                        print(f"❌ Connection Error for Key #{key_idx + 1}: {conn_err}")
                        continue
                    try:
                        if self.request_count >= self.RPM_THRESHOLD:
                            print(f"🔄 Key #{key_idx + 1} reached 18 RPM safety limit. Rotating key...")
                            config.KEY_COOLDOWNS[key] = time.time() + 5.0
                            continue
                        response = self._call_gemini_api(model, system_rules, full_prompt, image_path)
                        success = True
                        chosen_model = model
                        break
                    except Exception as e:
                        err_str = str(e).lower()
                        if any(x in err_str for x in ["404", "not found"]):
                            print(f"⚠️ Model '{model}' not found or unsupported for Key #{key_idx + 1}. Trying next model...")
                            break
                        if any(x in err_str for x in ["400", "invalid_argument", "403", "permission_denied", "expired", "leaked"]):
                            print(f"❌ Key #{key_idx + 1} is permanently invalid (expired/leaked). Disabling key.")
                            if key in self.api_keys:
                                self.api_keys.remove(key)
                            if key in config.API_KEYS_POOL:
                                config.API_KEYS_POOL.remove(key)
                            continue
                        connection_errors = [
                            "getaddrinfo", "connecterror", "connection error", "dns error", 
                            "no connections available", "network unreachable", "socket.timeout", 
                            "timed out", "connection refused", "failed to establish a new connection",
                            "cannot connect"
                        ]
                        if any(x in err_str for x in connection_errors):
                            print("🌐 [AIBRAIN]: Network connection issue detected. Bypassing cloud API.")
                            success = False
                            break
                        if any(x in err_str for x in ["429", "resource_exhausted", "quota exceeded"]):
                            print(f"⚠️ Quota Exceeded (429) on Key #{key_idx + 1}. Putting key on 45s cooldown.")
                            config.KEY_COOLDOWNS[key] = time.time() + 45.0
                            continue
                        print(f"⚠️ Error on Key #{key_idx + 1} with Model {model}: {e}. Trying next key...")
                        continue
            
            if success and response:
                answer = response.text if response.text else "I'm listening."
                answer = answer.replace("*", "")
                if "MEMORY:" in answer: 
                    answer = answer.split("MEMORY:")[0]
                answer = re.sub(r'\[(?!(?i:IMAGE|SIMPLE_IMAGE_REQUEST|Image of)).*?\]', '', answer).strip()
                answer = self._enforce_line_limits(user_text, answer, chosen_model, system_rules)
                self.chat_history.append(f"User: {user_text}")
                self.chat_history.append(f"Jarvis: {answer}")
                if chosen_model in self.models:
                    self.current_model_index = self.models.index(chosen_model)
                return answer
            return None

        # Routing Flow
        use_ollama = getattr(config, "CONVERSATION_PROVIDER", "gemini") == "ollama"
        fallback_model = getattr(config, "OLLAMA_MULTILINGUAL_MODEL", "gemma") if is_multilingual else getattr(config, "OLLAMA_ENGLISH_MODEL", "llama")
        
        if use_ollama:
            print(f"🧠 [AIBRAIN]: Using local Ollama model '{fallback_model}' as primary conversation brain...")
            try:
                ans = self._get_ollama_fallback(user_text, context, raise_on_error=True, model_name=fallback_model)
                return self._enforce_line_limits(user_text, ans)
            except Exception as e:
                print(f"⚠️ [AIBRAIN]: Local Ollama failed/offline: {e}. Falling back to Gemini...")
                if self.api_keys:
                    ans = run_gemini()
                    if ans:
                        return ans
        else:
            print("🧠 [AIBRAIN]: Using Gemini models as primary conversation brain...")
            if self.api_keys:
                ans = run_gemini()
                if ans:
                    return ans
                    
        # If both primary methods fail, fall back to local Ollama (if not already tried) or other options
        if not use_ollama:
            print(f"⚠️ [AIBRAIN]: Gemini failed or offline. Falling back to local Ollama model '{fallback_model}'...")
            try:
                ans = self._get_ollama_fallback(user_text, context, raise_on_error=True, model_name=fallback_model)
                return self._enforce_line_limits(user_text, ans)
            except Exception as e:
                pass
                
        # ChatGPT / ultimate fallback
        print(f"⚠️ [AIBRAIN]: Primary options failed. Trying ChatGPT fallback...")
        gpt_ans = self._get_chatgpt_fallback(user_text, context, system_rules)
        if gpt_ans:
            return self._enforce_line_limits(user_text, gpt_ans)
            
        # If ChatGPT also fails, final fallback to local Ollama (suppressing raise_on_error to return error message gracefully)
        ans = self._get_ollama_fallback(user_text, context, raise_on_error=False, model_name=fallback_model)
        return self._enforce_line_limits(user_text, ans)