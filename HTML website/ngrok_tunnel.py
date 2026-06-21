from pyngrok import ngrok
import time

# Start ngrok tunnel to port 5050
# This should match the local server port used by server.py.
tunnel = ngrok.connect(5050, "http")
print(f"\n{'='*60}")
print(f"✓ Ngrok tunnel is ACTIVE!")
print(f"{'='*60}")
print(f"\nPublic URL: {tunnel.public_url}")
print(f"\nShare this link with testers:\n{tunnel.public_url}\n")
print(f"{'='*60}")

# Keep tunnel running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTunnel closed.")
    ngrok.kill()
