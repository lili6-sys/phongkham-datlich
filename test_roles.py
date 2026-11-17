
import json
import secrets
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8080"

def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)

username = "test_" + secrets.token_hex(4)
password = secrets.token_urlsafe(12)

status, _ = call("POST", "/api/auth/register", {
    "username": username,
    "password": password,
    "full_name": "Test Patient"
})
print("Dang ky:", status)

status, result = call("POST", "/api/auth/login", {
    "username": username,
    "password": password
})
print("Dang nhap:", status)

if status != 200:
    raise SystemExit("Dang nhap that bai")

token = result["access_token"]

checks = [
    ("/api/auth/patient-area", 200),
    ("/api/auth/admin-area", 403),
    ("/api/appointments/", 403),
    ("/api/appointments/2", 403),
    ("/api/history/" + username, 200),
    ("/api/history/benhnhan02", 403),
]

for path, expected in checks:
    status, _ = call("GET", path, token=token)
    outcome = "PASS" if status == expected else "FAIL"
    print(f"{outcome}: {path} -> {status} (can {expected})")
