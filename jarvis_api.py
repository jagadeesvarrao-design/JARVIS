import sys
import os
import json
import threading
import time
import re
from http.server import BaseHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer as HTTPServer_Class
except ImportError:
    from http.server import HTTPServer as HTTPServer_Class
    from socketserver import ThreadingMixIn
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer_Class):
        pass
    HTTPServer_Class = ThreadedHTTPServer

import pythoncom

# Set up paths to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from jarvis import JARVIS, voice_queue, log_to_dashboard

# Whitelist of allowed origins for security hardening
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173"
]

# Global states to track JARVIS's status
global_state = "idle"
last_user_query = ""
last_jarvis_response = ""
current_speech_text = ""
pending_speech_texts = []
state_lock = threading.Lock()

class JarvisApiHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:3000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        global global_state, last_user_query, last_jarvis_response, current_speech_text
        
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            recent_logs = []
            log_file = "jarvis_logs.jsonl"
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines[-10:]:
                            recent_logs.append(json.loads(line.strip()))
                except Exception:
                    pass

            with state_lock:
                response_data = {
                    "status": global_state,
                    "last_query": last_user_query,
                    "last_response": last_jarvis_response,
                    "current_speech_text": current_speech_text,
                    "logs": recent_logs
                }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        elif self.path == '/api/events':
            # SSE Endpoint
            origin = self.headers.get('Origin', '')
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            if origin in ALLOWED_ORIGINS:
                self.send_header('Access-Control-Allow-Origin', origin)
            else:
                self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:3000')
            self.end_headers()

            last_sent_state = None
            last_sent_query = None
            last_sent_response = None
            last_sent_speech = None

            try:
                # Send initial state immediately
                with state_lock:
                    payload = {
                        "status": global_state,
                        "last_query": last_user_query,
                        "last_response": last_jarvis_response,
                        "current_speech_text": current_speech_text
                    }
                self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode('utf-8'))
                self.wfile.flush()

                while True:
                    with state_lock:
                        cur_state = global_state
                        cur_query = last_user_query
                        cur_response = last_jarvis_response
                        cur_speech = current_speech_text

                    if (cur_state != last_sent_state or 
                        cur_query != last_sent_query or 
                        cur_response != last_sent_response or 
                        cur_speech != last_sent_speech):
                        
                        last_sent_state = cur_state
                        last_sent_query = cur_query
                        last_sent_response = cur_response
                        last_sent_speech = cur_speech

                        payload = {
                            "status": cur_state,
                            "last_query": cur_query,
                            "last_response": cur_response,
                            "current_speech_text": cur_speech
                        }
                        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode('utf-8'))
                        self.wfile.flush()

                    time.sleep(0.05)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, Exception):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global global_state, last_user_query, last_jarvis_response
        
        if self.path == '/api/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get('command', '')
            except Exception as e:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
                return

            if not command:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty command"}).encode('utf-8'))
                return

            print(f"🌐 [API Server]: Executing command: {command}")
            with state_lock:
                last_jarvis_response = ""
            
            jarvis_instance.process_command(command)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            with state_lock:
                res_data = {
                    "query": command,
                    "response": last_jarvis_response,
                    "status": global_state,
                    "success": True
                }
            self.wfile.write(json.dumps(res_data).encode('utf-8'))
            
        elif self.path == '/api/listen':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            print("🌐 [API Server]: Listening triggered via API")
            recognized_text = jarvis_instance._listen_for_command()
            
            self.wfile.write(json.dumps({
                "recognized": recognized_text,
                "success": True
            }).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_api_server():
    server_address = ('', 5001)
    httpd = HTTPServer_Class(server_address, JarvisApiHandler)
    print("🚀 [API Server]: JARVIS API server running on http://localhost:5001")
    httpd.serve_forever()

if __name__ == "__main__":
    pythoncom.CoInitialize()
    jarvis_instance = JARVIS()
    
    original_respond = jarvis_instance._respond
    original_listen = jarvis_instance._listen_for_command
    original_process = jarvis_instance.process_command
    
    def api_respond(text, voice=None):
        global last_jarvis_response
        with state_lock:
            last_jarvis_response = text
            pending_speech_texts.append(text)
        original_respond(text, voice=voice)
        
    def api_listen():
        global global_state
        with state_lock:
            global_state = "listening"
        res = original_listen()
        with state_lock:
            global_state = "thinking"
        return res
        
    def api_process(text):
        global last_user_query, global_state
        with state_lock:
            last_user_query = text
            global_state = "thinking"
        log_to_dashboard("user", text)
        res = original_process(text)
        with state_lock:
            global_state = "idle"
        return res
        
    def api_speaking_state_changed(is_speaking):
        global global_state, current_speech_text
        with state_lock:
            if is_speaking:
                global_state = "speaking"
                if pending_speech_texts:
                    current_speech_text = pending_speech_texts.pop(0)
                else:
                    current_speech_text = last_jarvis_response
            else:
                global_state = "idle"
                current_speech_text = ""

    jarvis_instance._respond = api_respond
    jarvis_instance._listen_for_command = api_listen
    jarvis_instance.process_command = api_process
    
    import jarvis
    jarvis.speaking_callback = api_speaking_state_changed

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    try:
        jarvis_instance.run()
    except KeyboardInterrupt:
        print("Stopping JARVIS...")
    finally:
        pythoncom.CoUninitialize()
