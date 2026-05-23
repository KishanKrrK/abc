import requests

import os
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "re_KnsbyW3t_ERF9txWhNyGUsmr3USY8LpFF")
try:
    response = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {BREVO_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'from': 'Smart Lost & Found <onboarding@resend.dev>',
            'to': ['kishan.sk225@gmail.com'],
            'subject': 'Test OTP - Smart Lost & Found',
            'html': '<h2>Test Email</h2><p>Your OTP is: <strong>123456</strong></p>'
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
