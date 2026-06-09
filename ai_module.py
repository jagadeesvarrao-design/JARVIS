from google import genai
from google.genai import types
import config
import identity
import os
import PIL.Image
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
            self.models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
            
        self.current_model_index = 0
        self._connect_client()

    def _connect_client(self):
        """Connects the client and resets the counter for the new key"""
        try:
            current_key = self.api_keys[self.current_key_index]
            self.client = genai.Client(api_key=current_key)
            self.request_count = 0
            print(f"🧠 AI BRAIN CONNECTED (Key #{self.current_key_index + 1} | Model: {self.models[self.current_model_index]})")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    def _rotate_key(self):
        """Standard rotation for errors or RPM limits"""
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
        except requests.exceptions.ConnectionError:
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
            response = requests.post(config.OLLAMA_URL, json=payload, timeout=30)
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

    # =================================================================
    # PRIMARY ROUTING LOGIC
    # =================================================================
    def get_response(self, user_text, image_path=None, context=None):
        if not self.client: 
            # If completely failed to connect to Gemini at boot, force local
            return self._get_ollama_fallback(user_text, context)

        if self.request_count >= self.RPM_THRESHOLD:
            print(f"🔄 Key #{self.current_key_index + 1} reached 18 RPM safety limit. Rotating...")
            self._rotate_key()

        max_retries = len(self.api_keys) * 2
        attempt = 0

        while attempt < max_retries:
            current_model = self.models[self.current_model_index]
            
            try:
                # 1. Retrieve Memory
                if attempt == 0:
                    try:
                        from memory_moduler import MemorySystem 
                        mem = MemorySystem()
                        user_facts = mem.recall() or "No facts."
                    except: user_facts = "Unavailable"
                
                # 2. System Rules
                system_rules = (
                    f"You are {identity.BOT_NAME}, created by {config.OWNER_NAME}. "
                    f"Personality: Witty, loyal, helpful. "
                    f"CRITICAL RULE: "
                    f"   - If the user asks for an image, you MUST end your response with this EXACT tag: [IMAGE: <search_query>]"
                    f"SILENCE: Do NOT read the memory block."
                    f"MEMORY: [{user_facts}]"
                )
                
                # 3. Request Execution
                self.request_count += 1
                
                if image_path:
                    img = PIL.Image.open(image_path)
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=[img, "Describe this image."],
                        config=types.GenerateContentConfig(system_instruction=system_rules)
                    )
                    img.close()
                else:
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
                answer = re.sub(r'\[(?!Image).*?\]', '', answer).strip()

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

                # 3. Other errors (429 Quota, 503 Overload, 504 Timeout, Connection/Network) -> Rotate Key and retry
                print(f"⚠️ API Error on Key #{self.current_key_index + 1} ({current_model}): {e}. Rotating to next key...")
                self._rotate_key()
                attempt += 1
                continue

        # If all keys and retries exhaust, trigger Ollama as the absolute last resort
        return self._get_ollama_fallback(user_text, context)