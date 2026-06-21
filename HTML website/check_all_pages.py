import time
import urllib.request
import urllib.error
from pathlib import Path
import os

BASE = 'http://localhost:5050'

# Get all HTML files
html_files = [f.name for f in Path(__file__).parent.glob('*.html')]
html_files.sort()

print("=" * 80)
print("PAGE LOAD PERFORMANCE AND ERROR CHECK")
print("=" * 80)

results = []

for html_file in html_files:
    try:
        start = time.time()
        req = urllib.request.Request(f'{BASE}/{html_file}')
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8', 'ignore')
            elapsed_ms = (time.time() - start) * 1000
            
            # Check for common errors
            errors = []
            
            # Check for 404 references
            if 'favicon.ico' in content and 'favicon.ico' not in [f.name for f in Path(__file__).parent.glob('favicon.ico')]:
                errors.append("Missing favicon.ico referenced")
            
            # Check for broken img tags
            import re
            img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            for src in img_srcs:
                if src.startswith('http') or src.startswith('//'):
                    # External image - skip check
                    pass
                else:
                    # Local image - check if exists
                    local_path = Path(__file__).parent / src
                    if not local_path.exists():
                        errors.append(f"Missing local image: {src}")
            
            # Check for broken script tags
            script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
            for src in script_srcs:
                if not src.startswith('http') and not src.startswith('//'):
                    local_path = Path(__file__).parent / src
                    if not local_path.exists():
                        errors.append(f"Missing script: {src}")
            
            # Check for broken link tags
            link_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)
            for href in link_hrefs:
                if not href.startswith('http') and not href.startswith('//') and href != 'favicon.ico':
                    local_path = Path(__file__).parent / href
                    if not local_path.exists():
                        errors.append(f"Missing resource: {href}")
            
            # Performance check
            performance = "OK" if elapsed_ms < 250 else "SLOW"
            if elapsed_ms >= 1000:
                performance = "VERY SLOW"
            
            results.append({
                'file': html_file,
                'ms': elapsed_ms,
                'performance': performance,
                'errors': errors
            })
            
    except Exception as e:
        results.append({
            'file': html_file,
            'ms': None,
            'performance': 'ERROR',
            'errors': [str(e)]
        })

# Print results
print("\n1. ERROR LIST:\n")
all_errors = []
for result in results:
    if result['errors']:
        print(f"\n{result['file']}:")
        for error in result['errors']:
            print(f"  - {error}")
            all_errors.append({'file': result['file'], 'error': error})

if not all_errors:
    print("No errors found!")

# Print performance summary
print("\n" + "=" * 80)
print("2. PERFORMANCE ANALYSIS:\n")
for result in results:
    status = "✓" if result['performance'] == 'OK' else "✗"
    print(f"{status} {result['file']:<40} {result['ms']:>8.2f} ms  [{result['performance']}]")

avg_time = sum(r['ms'] for r in results if r['ms']) / len([r for r in results if r['ms']])
print(f"\nAverage load time: {avg_time:.2f} ms")
print(f"Expected: < 250 ms")
if avg_time > 250:
    print(f"Status: SLOW - {avg_time - 250:.2f} ms over target")

print("\n" + "=" * 80)
print("3. LAG ANALYSIS:\n")
slow_pages = [r for r in results if r['ms'] and r['ms'] > 250]
if slow_pages:
    print(f"Found {len(slow_pages)} slow pages (>250ms):")
    for r in slow_pages:
        print(f"  - {r['file']}: {r['ms']:.2f} ms (will cause lag)")
else:
    print("No slow pages found!")
