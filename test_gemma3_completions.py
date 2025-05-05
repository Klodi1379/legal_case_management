import requests
import json
import time

# LM Studio API endpoint for completions
url = "http://127.0.0.1:1234/v1/completions"

# Request payload with the exact model name from LM Studio
payload = {
    "model": "gemma-3-12b-it-qat",  # Exact model name from LM Studio
    "prompt": "You are a helpful legal assistant. What are the key components of a legal case management system?",
    "temperature": 0.7,
    "max_tokens": 500  # Reduced token count for faster response
}

# Headers
headers = {
    "Content-Type": "application/json"
}

# Print the request
print(f"Sending request to: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

# Send the request
print("Sending request... (this may take a while without GPU)")
start_time = time.time()
try:
    # Increase timeout to 5 minutes (300 seconds)
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
    
except Exception as e:
    print(f"Error: {str(e)}")

end_time = time.time()
print(f"Request took {end_time - start_time:.2f} seconds")
