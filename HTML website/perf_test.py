#!/usr/bin/env python3
import time
import urllib.request
import urllib.error

BASE = 'http://localhost:5050'

print("Testing page load performance...")
print("-" * 60)

# Test different pages
test_pages = [
    'index.html',
    'calendar.html',
    'upcoming-events.html',
    'join-the-ppg.html',
    'help-us-help-you.html',
]

for page in test_pages:
    times = []
    for i in range(3):
        try:
            start = time.time()
            req = urllib.request.Request(f'{BASE}/{page}')
            with urllib.request.urlopen(req, timeout=10) as r:
                size = len(r.read())
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                print(f"  Attempt {i+1}: {elapsed:.2f}ms ({size} bytes)")
        except Exception as e:
            print(f"  ERROR: {e}")
            break
    
    if times:
        avg = sum(times) / len(times)
        print(f"  {page:<30} AVG: {avg:7.2f}ms")
    print()

print("-" * 60)
print("Analysis: If pages take >250ms, they will cause lag")
