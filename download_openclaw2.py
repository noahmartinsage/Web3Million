import urllib.request
import os

url = 'https://github.com/openclaw/openclaw/archive/refs/tags/v2026.2.22.tar.gz'
dst = 'D:/AI/openclaw/openclaw-2026.2.22.tar.gz'

print(f"Downloading {url}...")
print(f"Destination: {dst}")

try:
    urllib.request.urlretrieve(url, dst)
    size = os.path.getsize(dst)
    print(f"Download complete! Size: {size / 1024 / 1024:.2f} MB")
except Exception as e:
    print(f"Error: {e}")
