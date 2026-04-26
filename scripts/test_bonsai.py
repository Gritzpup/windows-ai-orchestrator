import urllib.request, json, sys

def test_bonsai():
    url = "http://localhost:8080/v1/chat/completions"
    data = {
        "model": "Bonsai-8B.gguf",
        "messages": [{"role": "user", "content": "Provide the Riemann Hypothesis as a JSON object with keys 'name' and 'formula'. Output ONLY valid JSON."}],
        "max_tokens": 50
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            content = result['choices'][0]['message']['content']
            print(f"--- BONSAI OUTPUT START ---")
            print(content)
            print(f"--- BONSAI OUTPUT END ---")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_bonsai()
