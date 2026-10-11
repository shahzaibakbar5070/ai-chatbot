import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            self.send_json(500, {"error": "AI service is not configured"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            message = body.get("message", "")

            if not isinstance(message, str) or not message.strip():
                self.send_json(400, {"error": "Enter a message"})
                return

            if len(message) > 4000:
                self.send_json(400, {"error": "Message is too long"})
                return

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly, natural conversational "
                            "chatbot. Respond clearly and conversationally. "
                            "Never claim to be human."
                        )
                    },
                    {"role": "user", "content": message}
                ],
                "temperature": 0.8,
                "max_tokens": 500
            }

            request = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            reply = result["choices"][0]["message"]["content"]
            self.send_json(200, {"reply": reply})

        except urllib.error.HTTPError as error:
            print("AI provider returned HTTP error:", error.code)
            self.send_json(502, {"error": "AI provider request failed"})

        except Exception as error:
            print("Chat endpoint error:", str(error))
            self.send_json(500, {"error": "Could not generate a reply"})

    def do_GET(self):
        self.send_json(200, {"status": "Chat endpoint is online"})

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
