import json
import os
import sys
import urllib.request
import urllib.error

API_KEY = os.environ["AI_API_KEY"]
LOG_FILE = sys.argv[1]

with open(LOG_FILE, errors="ignore") as f:
    log_tail = "".join(f.readlines()[-150:])

prompt = f"""You are a DevOps expert. Below is a failed Jenkins build log.
Reply in this format:
1. Root cause (1 line)
2. Fix (max 3 lines)
3. Command to verify the fix

LOG:
{log_tail}"""

payload = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}]
}).encode()

req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
    data=payload,
    headers={
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "jenkins-failure-analyzer/1.0",
    },
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    print(data["candidates"][0]["content"]["parts"][0]["text"])
except urllib.error.HTTPError as e:
    print(f"API error {e.code}: {e.read().decode(errors='ignore')[:300]}")
    sys.exit(1)