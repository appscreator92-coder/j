import json
import base64
import requests
import sys
import os


# ============================================================
# BASE64URL -> HEX
# ============================================================
def base64url_to_hex(value):
    if not value:
        return ""

    value = str(value).strip()

    # Already hexadecimal?
    if len(value) % 2 == 0:
        try:
            int(value, 16)
            return value.lower()
        except ValueError:
            pass

    value = value.replace("-", "+").replace("_", "/")

    while len(value) % 4:
        value += "="

    try:
        decoded = base64.b64decode(value)
        return decoded.hex()
    except Exception:
        return ""


# ============================================================
# EXTRACT KEYS FROM API RESPONSE
# ============================================================
def extract_keys(data):

    # Possible locations of the keys
    possible = []

    # Format:
    # {
    #   "base64": {
    #       "keys": [...]
    #   }
    # }
    if isinstance(data, dict):

        base64_data = data.get("base64")

        if isinstance(base64_data, dict):
            keys = base64_data.get("keys")

            if isinstance(keys, list):
                possible.extend(keys)

        # Format:
        # {
        #   "keys": [...]
        # }
        keys = data.get("keys")

        if isinstance(keys, list):
            possible.extend(keys)

        # Sometimes:
        # {
        #   "base64": [...]
        # }
        if isinstance(base64_data, list):
            possible.extend(base64_data)

    # Remove duplicates while preserving order
    result = []

    seen = set()

    for key in possible:

        if not isinstance(key, dict):
            continue

        kid = key.get("kid") or key.get("keyId") or key.get("keyid")
        kval = key.get("k") or key.get("key")

        if not kid or not kval:
            continue

        unique = (str(kid), str(kval))

        if unique in seen:
            continue

        seen.add(unique)

        result.append({
            "kid": kid,
            "k": kval
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

    # --------------------------------------------------------
    # IMPORTANT:
    # Put the real token in GitHub Actions Secret:
    # KEY_API_TOKEN
    # --------------------------------------------------------
    token = os.environ.get("KEY_API_TOKEN")

    if not token:
        print("ERROR: KEY_API_TOKEN is not configured.")
        sys.exit(1)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
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

        # Keep EVERYTHING from original jnew5.json
        item = channel.copy()

        channel_id = str(channel.get("id", "")).strip()

        print("")
        print("=" * 70)
        print(f"[{index}/{total}] ID: {channel_id}")
        print(f"Name: {channel.get('name', '')}")

        if channel_id:

            api_url = (
                "https://warm-caverns-48629-92fab798385f/"
                "https://game.playindia.fun/Jtv/key.php"
                f"?id={channel_id}&token={token}"
            )

            # NOTE:
            # Use your actual Heroku URL here.
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
                    f"Key API HTTP status: "
                    f"{key_response.status_code}"
                )

                if key_response.status_code != 200:

                    print(
                        f"WARNING: Key API failed for ID "
                        f"{channel_id}"
                    )

                else:

                    # ----------------------------------------
                    # Decode JSON
                    # ----------------------------------------
                    try:
                        data = key_response.json()
                    except Exception as e:

                        print(
                            f"WARNING: API did not return JSON: {e}"
                        )

                        print(
                            "Response:",
                            key_response.text[:1000]
                        )

                        data = None

                    if data is not None:

                        # ------------------------------------
                        # Extract keys
                        # ------------------------------------
                        keys = extract_keys(data)

                        print(
                            f"Additional keys received: "
                            f"{len(keys)}"
                        )

                        # ------------------------------------
                        # ADD AS keyId2/key2, keyId3/key3...
                        # ------------------------------------
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
                                    f"  Key {key_index}: "
                                    f"INVALID"
                                )
                                continue

                            item[f"keyId{key_index}"] = kid_hex
                            item[f"key{key_index}"] = key_hex

                            print(
                                f"  Added keyId{key_index}: "
                                f"{kid_hex}"
                            )

                            print(
                                f"  Added key{key_index}: "
                                f"{key_hex}"
                            )

            except requests.RequestException as e:

                print(
                    f"WARNING: Request error for ID "
                    f"{channel_id}: {e}"
                )

            except Exception as e:

                print(
                    f"WARNING: Error processing ID "
                    f"{channel_id}: {e}"
                )

        else:

            print("WARNING: Channel has no ID.")

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
    print(f"Channels processed: {len(output)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
