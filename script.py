import json
import base64
import requests
import sys


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "appscreator92-coder/index/refs/heads/main/jnew5.json"
)

# Original token
TOKEN = "RiYlIZ"


# ============================================================
# BASE64URL -> HEX
# ============================================================

def base64url_to_hex(value):
    """
    Convert Base64URL string to hexadecimal.

    Example:
        QAExmUtEXYyIFyAiSHYP2g
        ->
        400131994b445d8c8817202248760fda
    """

    if not value:
        return ""

    try:
        value = str(value).strip()

        # Convert Base64URL characters to normal Base64
        value = value.replace("-", "+")
        value = value.replace("_", "/")

        # Add Base64 padding
        value += "=" * (-len(value) % 4)

        decoded = base64.b64decode(value)

        return decoded.hex()

    except Exception as e:
        print(f"    Base64 conversion error: {e}")
        return ""


# ============================================================
# FETCH JSON
# ============================================================

def fetch_json(url, headers, timeout=20):

    response = requests.get(
        url,
        headers=headers,
        timeout=timeout
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# MAIN
# ============================================================

def main():

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
    # FETCH jnew5.json
    # ========================================================

    print("=" * 70)
    print("Fetching jnew5.json...")
    print("=" * 70)

    try:

        channels = fetch_json(
            SOURCE_URL,
            headers,
            timeout=30
        )

    except Exception as e:

        print(
            f"ERROR: Failed to fetch jnew5.json: {e}"
        )

        sys.exit(1)


    if not isinstance(channels, list):

        print(
            "ERROR: jnew5.json does not contain a JSON array."
        )

        sys.exit(1)


    total_channels = len(channels)

    print(
        f"Total channels found: {total_channels}"
    )


    output = []


    # ========================================================
    # PROCESS EACH CHANNEL
    # ========================================================

    for index, channel in enumerate(
        channels,
        start=1
    ):

        print()
        print("=" * 70)

        channel_id = str(
            channel.get("id", "")
        ).strip()

        channel_name = str(
            channel.get("name", "")
        )

        print(
            f"[{index}/{total_channels}] "
            f"{channel_name}"
        )

        print(
            f"ID: {channel_id}"
        )

        print("=" * 70)


        # ====================================================
        # COPY ORIGINAL CHANNEL
        #
        # NOTHING from jnew5.json is modified.
        # ====================================================

        item = channel.copy()


        # ====================================================
        # NO ID
        # ====================================================

        if not channel_id:

            print(
                "WARNING: Channel has no ID."
            )

            output.append(item)

            continue


        # ====================================================
        # API URL
        #
        # Example:
        #
        # https://game.playindia.fun/Jtv/key.php?id=1108&token=RiYlIZ
        # ====================================================

        api_url = (
            "https://game.playindia.fun/Jtv/key.php"
            f"?id={channel_id}"
            f"&token={TOKEN}"
        )


        print(
            "Fetching additional keys..."
        )


        # ====================================================
        # CALL KEY API
        # ====================================================

        try:

            response = requests.get(
                api_url,
                headers=headers,
                timeout=20
            )

            print(
                f"API HTTP status: "
                f"{response.status_code}"
            )

            response.raise_for_status()


        except requests.RequestException as e:

            print(
                f"WARNING: API request failed: {e}"
            )

            # Keep original channel unchanged
            output.append(item)

            continue


        # ====================================================
        # PARSE API JSON
        # ====================================================

        try:

            data = response.json()

        except Exception as e:

            print(
                f"WARNING: API returned invalid JSON: {e}"
            )

            output.append(item)

            continue


        # ====================================================
        # GET:
        #
        # data["base64"]["keys"]
        # ====================================================

        base64_data = data.get(
            "base64",
            {}
        )


        if not isinstance(
            base64_data,
            dict
        ):

            print(
                "WARNING: 'base64' is not an object."
            )

            output.append(item)

            continue


        keys = base64_data.get(
            "keys",
            []
        )


        if not isinstance(
            keys,
            list
        ):

            print(
                "WARNING: 'base64.keys' is not a list."
            )

            output.append(item)

            continue


        print(
            f"API returned {len(keys)} key(s)."
        )


        # ====================================================
        # ADD API KEYS
        #
        # API KEY #1 -> keyId2 / key2
        # API KEY #2 -> keyId3 / key3
        # API KEY #3 -> keyId4 / key4
        #
        # Existing keyId/key and keyId1/key1 are untouched.
        # ====================================================

        added_count = 0


        for api_key_number, key_object in enumerate(
            keys,
            start=2
        ):


            if not isinstance(
                key_object,
                dict
            ):

                print(
                    f"  API key #{api_key_number}: "
                    f"invalid object"
                )

                continue


            # ------------------------------------------------
            # API:
            #
            # kid = Key ID
            # k   = Key
            # ------------------------------------------------

            kid = key_object.get(
                "kid",
                ""
            )

            key = key_object.get(
                "k",
                ""
            )


            if not kid:

                print(
                    f"  API key #{api_key_number}: "
                    f"missing kid"
                )

                continue


            if not key:

                print(
                    f"  API key #{api_key_number}: "
                    f"missing k"
                )

                continue


            # ------------------------------------------------
            # Convert Base64URL -> HEX
            # ------------------------------------------------

            key_id_hex = base64url_to_hex(
                kid
            )

            key_hex = base64url_to_hex(
                key
            )


            if not key_id_hex:

                print(
                    f"  API key #{api_key_number}: "
                    f"kid conversion failed"
                )

                continue


            if not key_hex:

                print(
                    f"  API key #{api_key_number}: "
                    f"k conversion failed"
                )

                continue


            # ------------------------------------------------
            # IMPORTANT
            #
            # API key #1 -> keyId2/key2
            # API key #2 -> keyId3/key3
            # etc.
            # ------------------------------------------------

            key_id_field = (
                f"keyId{api_key_number}"
            )

            key_field = (
                f"key{api_key_number}"
            )


            # ------------------------------------------------
            # ADD ONLY
            #
            # Existing fields are NOT modified.
            # ------------------------------------------------

            item[key_id_field] = key_id_hex

            item[key_field] = key_hex


            added_count += 1


            print(
                f"  Added {key_id_field}: "
                f"{key_id_hex}"
            )

            print(
                f"  Added {key_field}: "
                f"{key_hex}"
            )


        # ====================================================
        # RESULT FOR CHANNEL
        # ====================================================

        if added_count:

            print(
                f"Successfully added "
                f"{added_count} additional key(s)."
            )

        else:

            print(
                "No additional keys were added."
            )


        # ====================================================
        # ADD CHANNEL TO OUTPUT
        # ====================================================

        output.append(item)


    # ========================================================
    # SAVE new.json
    # ========================================================

    print()
    print("=" * 70)
    print("Writing new.json...")
    print("=" * 70)


    try:

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


    except Exception as e:

        print(
            f"ERROR: Failed to write new.json: {e}"
        )

        sys.exit(1)


    # ========================================================
    # DONE
    # ========================================================

    print()
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)

    print(
        f"Channels processed: {len(output)}"
    )

    print(
        "Output file: new.json"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
