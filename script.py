import json
import base64
import requests
import sys

# Convert Base64URL to Hex
def base64url_to_hex(base64url):
    if not base64url:
        return ""
    base64_str = base64url.replace('-', '+').replace('_', '/')
    remainder = len(base64_str) % 4
    if remainder:
        base64_str += '=' * (4 - remainder)
    try:
        binary = base64.b64decode(base64_str)
        return binary.hex()
    except Exception:
        return ""

def main():
    source_url = "https://raw.githubusercontent.com/appscreator92-coder/index/refs/heads/main/jnew5.json"
    token = "RiYlIZ..." # Your API token
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://game.playindia.fun",
        "Referer": "https://game.playindia.fun/"
    }

    print("Fetching source JSON...")
    try:
        res = requests.get(source_url, headers=headers, timeout=15)
        res.raise_for_status()
        channels = res.json()
    except Exception as e:
        print(f"Failed to fetch source file: {e}")
        sys.exit(1)

    output = []
    total = len(channels)

    for idx, channel in enumerate(channels, start=1):
        # Keeps original fields untouched (id, name, logo, category, url, keyId, key, url1, keyId1, key1)
        item = channel.copy()
        channel_id = str(channel.get("id", ""))

        print(f"[{idx}/{total}] Processing ID: {channel_id}")

        if channel_id:
            api_url = f"https://warm-caverns-48629-92fab798385f.herokuapp.com/https://game.playindia.fun/Jtv/key.php?id={channel_id}&token={token}"
            try:
                key_res = requests.get(api_url, headers=headers, timeout=10)
                if key_res.status_code == 200:
                    data = key_res.json()
                    keys = data.get("base64", {}).get("keys", [])
                    
                    # Dynamically add keyId2, key2, keyId3, key3, keyId4, key4...
                    for k_idx, key_obj in enumerate(keys):
                        key_num = k_idx + 2
                        if "kid" in key_obj:
                            item[f"keyId{key_num}"] = base64url_to_hex(key_obj["kid"])
                        if "k" in key_obj:
                            item[f"key{key_num}"] = base64url_to_hex(key_obj["k"])
            except Exception as e:
                print(f"  Warning: Error fetching key for ID {channel_id}: {e}")

        output.append(item)

    # Save to file
    with open("new.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Successfully generated new.json!")

if __name__ == "__main__":
    main()
