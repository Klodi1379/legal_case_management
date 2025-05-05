import requests
import json

# LM Studio API endpoint for models
url = "http://127.0.0.1:1234/v1/models"

# Headers
headers = {
    "Content-Type": "application/json"
}

# Print the request
print(f"Sending request to: {url}")

# Send the request
try:
    response = requests.get(url, headers=headers)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
    
except Exception as e:
    print(f"Error: {str(e)}")
