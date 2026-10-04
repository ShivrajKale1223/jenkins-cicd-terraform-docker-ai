import json
import os
import sys
import urllib.request

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
    "model": "llama-3.3-70b-versatile",  # check Groq docs if rejected
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.2,
}).encode()

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=payload,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
print(data["choices"][0]["message"]["content"])