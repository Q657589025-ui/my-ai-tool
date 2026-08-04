import os
import hashlib
import base64
import requests
from config.settings import OUTPUT_DIR

def file_to_data_uri(file_obj):
    if file_obj is None:
        return None
    with open(file_obj.name, "rb") as f:
        data = f.read()
        ext = os.path.splitext(file_obj.name)[1].lower()
        mime = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp",
            ".mp4": "video/mp4", ".mov": "video/quicktime"
        }.get(ext, "application/octet-stream")
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"

def download_image(url, filename=None):
    if not url or not url.startswith("http"):
        return None
    if not filename:
        filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    local_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
            else:
                return None
        except:
            return None
    return local_path
