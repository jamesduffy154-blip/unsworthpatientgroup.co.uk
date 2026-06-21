import json
import time
import urllib.request
import urllib.error
import uuid

BASE = 'http://localhost:5050'


def fetch(path, method='GET', body=None):
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return {
                'status': r.status,
                'ms': (time.time() - start) * 1000,
                'body': r.read().decode('utf-8', 'ignore'),
                'headers': dict(r.headers.items()),
            }
    except urllib.error.HTTPError as e:
        return {
            'status': e.code,
            'ms': (time.time() - start) * 1000,
            'body': e.read().decode('utf-8', 'ignore'),
            'headers': dict(e.headers.items()),
        }


# Test 1: Security and privacy posture
reg = fetch('/api/register', 'POST', json.dumps({
    'name': 'Test User',
    'email': f'test-{uuid.uuid4().hex[:8]}@example.com',
    'password': 'StrongPass123!'
}).encode())
listings = fetch('/api/registrations')
records = json.loads(listings['body']) if listings['body'] else []
contains_hash = any('passwordHash' in item for item in records if isinstance(item, dict))
security_ok = reg['status'] == 201 and contains_hash and 'passwordHash' in json.dumps(records)

# Test 2: Smoothness / responsiveness
latencies = []
for _ in range(5):
    latencies.append(fetch('/index.html')['ms'])
avg = sum(latencies) / len(latencies)
fast_enough = avg < 250

print('TEST1_SECURITY_RESULT', 'PASS' if security_ok else 'FAIL')
print('TEST1_REGISTER_STATUS', reg['status'])
print('TEST1_PASSWORD_HASH_STORED', contains_hash)
print('TEST1_CORS_ALLOW_ORIGIN', reg['headers'].get('Access-Control-Allow-Origin'))
print('TEST1_AVG_RESPONSE_MS', round(avg, 2))

print('TEST2_SMOOTHNESS_RESULT', 'PASS' if fast_enough else 'FAIL')
print('TEST2_AVG_MS', round(avg, 2))
print('TEST2_MIN_MS', round(min(latencies), 2))
print('TEST2_MAX_MS', round(max(latencies), 2))
print('TEST2_REQUEST_COUNT', len(latencies))
