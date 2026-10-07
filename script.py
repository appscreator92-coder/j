import json
import base64
import requests
import sys


# ============================================================
# Convert Base64URL to Hex
# ============================================================
def base64url_to_hex(value):
    if not value:
        return ""

    value = str(value).strip()

    # Base64URL -> standard Base64
    value = value.replace("-", "+").replace("_", "/")

    while len(value) % 4:
        value += "="

    try:
        binary = base64.b64decode(value)
        return binary.hex()
    except Exception:
        return ""


# ============================================================
# Extract keys from API response
# ============================================================
def extract_keys(data):

    keys = []

    if not isinstance(data, dict):
        return keys

    # Main expected format:
    #
    # {
    #   "base64": {
    #       "keys": [
    #           {"kid": "...", "k": "..."},
    #           {"kid": "...", "k": "..."}
    #       ]
    #   }
    # }
    base64_data = data.get("base64")

    if isinstance(base64_data, dict):
        base64_keys = base64_data.get("keys")

        if isinstance(base64_keys, list):
            keys.extend(base64_keys)

    # Also support direct:
    #
    # {
    #   "keys": [...]
    # }
    direct_keys = data.get("keys")

    if isinstance(direct_keys, list):
        keys.extend(direct_keys)

    # Remove duplicates
    result = []
    seen = set()

    for key in keys:

        if not isinstance(key, dict):
            continue

        kid = key.get("kid")
        k = key.get("k")

        if not kid or not k:
            continue

        unique = (str(kid), str(k))

        if unique in seen:
            continue

        seen.add(unique)

        result.append({
            "kid": kid,
            "k": k
        })

    return result


# ============================================================
# MAIN
# ============================================================
def main():

    source_url = (
        "https://raw.githubusercontent.com/"
        "appscreator92-coder/index/refs/heads/main/jnew5.json"
    )

    # ========================================================
    # ORIGINAL TOKEN
    # ========================================================
    token = "RiYlIZ..."

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://game.playindia.fun",
        "Referer": "https://game.playindia.fun/"
    }

    # ========================================================
    # FETCH SOURCE JSON
    # ========================================================
    print("Fetching source JSON...")

    try:
        response = requests.get(
            source_url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        channels = response.json()

    except Exception as e:
        print(f"Failed to fetch source file: {e}")
        sys.exit(1)

    if not isinstance(channels, list):
        print("ERROR: Source JSON is not an array.")
        sys.exit(1)

    print(f"Total channels: {len(channels)}")

    output = []

    total = len(channels)

    # ========================================================
    # PROCESS CHANNELS
    # ========================================================
    for index, channel in enumerate(channels, start=1):

        # Keep original jnew5.json fields unchanged
        item = channel.copy()

        channel_id = str(
            channel.get("id", "")
        ).strip()

        print("")
        print("=" * 70)
        print(
            f"[{index}/{total}] "
            f"ID: {channel_id}"
        )
        print(
            f"Name: {channel.get('name', '')}"
        )

        if not channel_id:
            print("WARNING: Channel has no ID.")
            output.append(item)
            continue

        # ====================================================
        # KEY API
        # ====================================================
        api_url = (
            "https://warm-caverns-48629-92fab798385f.herokuapp.com/"
            "https://game.playindia.fun/Jtv/key.php"
            f"?id={channel_id}&token={token}"
        )

        try:

            key_response = requests.get(
                api_url,
                headers=headers,
                timeout=20
            )

            print(
                f"Key API status: "
                f"{key_response.status_code}"
            )

            if key_response.status_code != 200:

                print(
                    f"WARNING: Key API failed "
                    f"for ID {channel_id}"
                )

            else:

                try:
                    data = key_response.json()

                except Exception as e:

                    print(
                        f"WARNING: Invalid JSON response: {e}"
                    )

                    print(
                        key_response.text[:1000]
                    )

                    data = None

                if data is not None:

                    # ----------------------------------------
                    # Extract API keys
                    # ----------------------------------------
                    keys = extract_keys(data)

                    print(
                        f"API keys found: {len(keys)}"
                    )

                    # ----------------------------------------
                    # Add additional keys starting from 2
                    # ----------------------------------------
                    for key_index, key_obj in enumerate(
                        keys,
                        start=2
                    ):

                        kid_hex = base64url_to_hex(
                            key_obj["kid"]
                        )

                        key_hex = base64url_to_hex(
                            key_obj["k"]
                        )

                        if not kid_hex or not key_hex:

                            print(
                                f"  key {key_index}: "
                                f"conversion failed"
                            )

                            continue

                        item[
                            f"keyId{key_index}"
                        ] = kid_hex

                        item[
                            f"key{key_index}"
                        ] = key_hex

                        print(
                            f"  Added keyId{key_index}: "
                            f"{kid_hex}"
                        )

                        print(
                            f"  Added key{key_index}: "
                            f"{key_hex}"
                        )

        except Exception as e:

            print(
                f"WARNING: Error fetching keys "
                f"for ID {channel_id}: {e}"
            )

        output.append(item)

    # ========================================================
    # SAVE new.json
    # ========================================================
    with open(
        "new.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("")
    print("=" * 70)
    print("Successfully generated new.json!")
    print(
        f"Channels processed: {len(output)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
