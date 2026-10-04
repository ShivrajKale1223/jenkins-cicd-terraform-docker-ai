import os
import sys
import requests

API_KEY = os.environ["AI_API_KEY"]
LOG_FILE = sys.argv[1]

# Send only the last 150 lines (errors are usually at the end)
with open(LOG_FILE, errors="ignore") as f:
    log_tail = "".join(f.readlines()[-150:])

prompt = f"""You are a DevOps expert. Below is a failed Jenkins build log.
Reply in this format:
1. Root cause (1 line)
2. Fix (max 3 lines)
3. Command to verify the fix

LOG:
{log_tail}"""

resp = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": "llama-3.3-70b-versatile",  # check Groq docs if this name is rejected
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    },
    timeout=30,
)
resp.raise_for_status()
print(resp.json()["choices"][0]["message"]["content"])