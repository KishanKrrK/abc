import requests

import os
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "your_api_key_here")
try:
    response = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={
            'api-key': BREVO_API_KEY,
            'Content-Type': 'application/json'
        },
        json={
            'sender': {'name': 'Smart Lost & Found', 'email': 'shashishe2160@gmail.com'},
            'to': [{'email': 'kishan.sk225@gmail.com'}],
            'subject': 'Test OTP - Smart Lost & Found',
            'htmlContent': '<h2>Test Email</h2><p>Your OTP is: <strong>123456</strong></p>'
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
