import requests
import json
import time

# LM Studio API endpoint
url = "http://127.0.0.1:1234/v1/chat/completions"

# Request payload
payload = {
    "model": "qwen3-4b",
    "messages": [
        {"role": "system", "content": "You are a helpful legal assistant."},
        {"role": "user", "content": "Explain the key components of a legal case management system"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

# Headers
headers = {
    "Content-Type": "application/json"
}

# Print the request
print(f"Sending request to: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

# Send the request
start_time = time.time()
try:
    print("Sending request... (this may take a while without GPU)")
    # Increase timeout to 5 minutes (300 seconds)
    response = requests.post(url, json=payload, headers=headers, timeout=300)

    # Print the response
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")

except Exception as e:
    print(f"Error: {str(e)}")

end_time = time.time()
print(f"Request took {end_time - start_time:.2f} seconds")
