import tarfile
import os

src = 'D:/AI/openclaw/openclaw-2026.2.22.tar.gz'
dst = 'D:/AI/openclaw/'

print(f"Extracting {src} to {dst}...")
try:
    with tarfile.open(src, 'r:gz') as tar:
        tar.extractall(path=dst)
    print("Extraction complete!")
    
    # List extracted contents
    for item in os.listdir(dst):
        print(f"  - {item}")
except Exception as e:
    print(f"Error: {e}")
