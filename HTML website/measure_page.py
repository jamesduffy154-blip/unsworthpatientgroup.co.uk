import time
import urllib.request

start = time.time()
with urllib.request.urlopen('http://localhost:5050/upcoming-events.html') as r:
    data = r.read()
    print('STATUS', r.status)
    print('BYTES', len(data))
    print('MS', round((time.time() - start) * 1000, 2))
