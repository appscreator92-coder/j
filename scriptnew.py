import json
import requests
import sys


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "appscreator92-coder/index/refs/heads/main/jnew5.json"
)

SPORTLINK_URL = "https://sportlink-tv10.pages.dev/jtvplus.json"


# ============================================================
# FETCH JSON
# ============================================================

def fetch_json(url, headers, timeout=20):
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


# ============================================================
# MAIN
# ============================================================

def main():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }

    print("=" * 70)
    print("Fetching jnew5.json and sportlink data...")
    print("=" * 70)

    try:
        jnew5_data = fetch_json(SOURCE_URL, headers, timeout=30)
    except Exception as e:
        print(f"ERROR: Failed to fetch jnew5.json: {e}")
        sys.exit(1)

    try:
        sportlink_response = fetch_json(SPORTLINK_URL, headers, timeout=30)
        # Handle if channels are nested under a "channels" key
        if isinstance(sportlink_response, dict):
            sportlink_channels = sportlink_response.get("channels", [])
        elif isinstance(sportlink_response, list):
            sportlink_channels = sportlink_response
        else:
            sportlink_channels = []
    except Exception as e:
        print(f"ERROR: Failed to fetch sportlink data: {e}")
        sys.exit(1)

    if not isinstance(jnew5_data, list):
        print("ERROR: jnew5.json does not contain a JSON array.")
        sys.exit(1)

    # Build a lookup map from sportlink channels using ID and Name
    # Key: (str(id), str(name).strip()) -> list of sportlink entries
    sportlink_map = {}
    for sch in sportlink_channels:
        s_id = str(sch.get("id", "")).strip()
        s_name = str(sch.get("name", "")).strip()
        if s_id and s_name:
            sportlink_map[(s_id, s_name)] = sch.get("sportlink", [])

    total_channels = len(jnew5_data)
    print(f"Total channels found in jnew5.json: {total_channels}")

    output = []

    for index, channel in enumerate(jnew5_data, start=1):
        print()
        print("=" * 70)

        channel_id = str(channel.get("id", "")).strip()
        channel_name = str(channel.get("name", "")).strip()

        print(f"[{index}/{total_channels}] {channel_name} (ID: {channel_id})")
        print("=" * 70)

        item = channel.copy()

        if not channel_id or not channel_name:
            print("WARNING: Channel missing ID or Name. Keeping original.")
            output.append(item)
            continue

        # Look up matching sportlink entry using both ID and Name
        lookup_key = (channel_id, channel_name)
        sportlink_keys = sportlink_map.get(lookup_key, [])

        if not sportlink_keys:
            print("No matching sportlink keys found for this ID & Name combo.")
            output.append(item)
            continue

        print(f"Found {len(sportlink_keys)} sportlink key(s).")

        added_count = 0
        # Map starting from index 2 -> keyId2 / key2
        for key_idx, key_pair in enumerate(sportlink_keys, start=2):
            if not isinstance(key_pair, str) or ":" not in key_pair:
                continue

            kid_hex, k_hex = key_pair.split(":", 1)
            kid_hex = kid_hex.strip()
            k_hex = k_hex.strip()

            if not kid_hex or not k_hex:
                continue

            key_id_field = f"keyId{key_idx}"
            key_field = f"key{key_idx}"

            item[key_id_field] = kid_hex
            item[key_field] = k_hex
            added_count += 1

            print(f"  Added {key_id_field}: {kid_hex}")
            print(f"  Added {key_field}: {k_hex}")

        if added_count:
            print(f"Successfully added {added_count} additional key pair(s).")
        else:
            print("No valid key pairs could be parsed.")

        output.append(item)

    # ========================================================
    # SAVE new.json
    # ========================================================
    print()
    print("=" * 70)
    print("Writing new1.json...")
    print("=" * 70)

    try:
        with open("new1.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Failed to write new1.json: {e}")
        sys.exit(1)

    print()
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print(f"Channels processed: {len(output)}")
    print("Output file: new1.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
