import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

API_KEY = os.environ.get("AI_API_KEY", "")
LOG_FILE = sys.argv[1]

with open(LOG_FILE, errors="ignore") as f:
    lines = f.readlines()
log_tail = "".join(lines[-60:])


def rule_based_hint(text):
    rules = [
        ("No matching distribution found", "A Python package or version in requirements.txt does not exist. Check the name and version."),
        ("permission denied", "Permission problem. Check that the jenkins user is in the docker group and restart Jenkins."),
        ("command not found", "A required tool is missing on the Jenkins server. Install it."),
        ("no basic auth credentials", "ECR login failed. Check the IAM role and the login stage."),
        ("denied: requested access", "ECR push was denied. Check IAM permissions on the repository."),
        ("No space left on device", "Disk full. Run docker system prune -af on the server."),
        ("Could not resolve host", "Network or DNS problem on the server."),
    ]
    for pattern, hint in rules:
        if pattern.lower() in text.lower():
            return f"Rule-based hint: {hint}"
    return "Rule-based hint: no known pattern matched. Read the first ERROR line in the log."


MODELS = ["llama-3.1-8b-instant", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]


def ask_groq(prompt):
    last = ""
    for model in MODELS:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode()
        for attempt in range(3):
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "jenkins-failure-analyzer/1.0",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.load(resp)["choices"][0]["message"]["content"], ""
            except urllib.error.HTTPError as e:
                last = f"{model} -> HTTP {e.code}: {e.read().decode(errors='ignore')[:150]}"
                if e.code in (429, 500, 503):
                    time.sleep(5 * (attempt + 1))
                    continue
                break  # 404/400/401: try the next model
            except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
                last = f"{model} -> network/timeout: {e}"
                time.sleep(5)
    return None, last


prompt = f"""You are a DevOps expert. Below is a failed Jenkins build log.
Reply briefly in this format:
1. Root cause (1 line)
2. Fix (max 3 lines)
3. Command to verify the fix

LOG:
{log_tail}"""

answer, error = (None, "no API key set") if not API_KEY else ask_groq(prompt)

if answer:
    print(answer)
else:
    print(f"AI unavailable ({error})")
    print(rule_based_hint(log_tail))