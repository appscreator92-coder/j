
import json
import requests
import sys
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_URL = (
    "https://raw.githubusercontent.com/appscreator92-coder/"
    "index/refs/heads/main/jnew5.json"
)

SPORTLINK_URL = "https://sportlink-tv10.pages.dev/jtvplus3.json"

OUTPUT_FILE = "new1.json"

TIMEOUT = 30


# ============================================================
# HTTP SESSION - FRESH DATA
# ============================================================

def create_session():
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache, no-store, max-age=0",
        "Pragma": "no-cache",
    })

    return session


def fetch_json(session, url, label):

    # Add a unique query parameter to reduce CDN caching.
    parts = urlsplit(url)
    params = parse_qsl(parts.query, keep_blank_values=True)
    params.append(("_refresh", str(time.time_ns())))

    fresh_url = urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(params),
        parts.fragment
    ))

    print(f"\nFetching {label}...")

    response = session.get(
        fresh_url,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    print(f"HTTP Status: {response.status_code}")
    print(f"Downloaded: {len(response.content):,} bytes")

    return data


# ============================================================
# NORMALIZE ID AND NAME
# ============================================================

def normalize_id(value):

    if value is None:
        return ""

    return str(value).strip()


def normalize_name(value):

    if value is None:
        return ""

    value = str(value).lower().strip()

    # Remove spaces and punctuation for flexible matching.
    return re.sub(r"[^a-z0-9]", "", value)


# ============================================================
# EXTRACT CHANNEL ARRAYS
# ============================================================

def get_sportlink_channels(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        channels = data.get("channels")

        if isinstance(channels, list):
            return channels

        # Support alternative nested structures.
        for key in ("data", "results"):

            nested = data.get(key)

            if isinstance(nested, list):
                return nested

            if isinstance(nested, dict):
                channels = nested.get("channels")

                if isinstance(channels, list):
                    return channels

    raise ValueError(
        "Unable to locate Sportlink channels array."
    )


# ============================================================
# EXTRACT SPORTLINK KEY PAIRS
# ============================================================

def extract_key_pairs(channel):

    raw_keys = channel.get("sportlink", [])

    if isinstance(raw_keys, str):
        raw_keys = [raw_keys]

    if not isinstance(raw_keys, list):
        return []

    valid_pairs = []

    for entry in raw_keys:

        kid = ""
        key = ""

        # Format: kid:key
        if isinstance(entry, str) and ":" in entry:

            kid, key = entry.split(":", 1)

        # Alternative dictionary format.
        elif isinstance(entry, dict):

            kid = (
                entry.get("keyId")
                or entry.get("key_id")
                or entry.get("kid")
                or ""
            )

            key = (
                entry.get("key")
                or entry.get("value")
                or ""
            )

        kid = str(kid).strip()
        key = str(key).strip()

        # Validate 32-character hexadecimal DRM values.
        if (
            re.fullmatch(r"[0-9a-fA-F]{32}", kid)
            and re.fullmatch(r"[0-9a-fA-F]{32}", key)
        ):

            pair = (kid.lower(), key.lower())

            if pair not in valid_pairs:
                valid_pairs.append(pair)

    return valid_pairs


# ============================================================
# BUILD SPORTLINK LOOKUP
# ============================================================

def build_lookup(channels):

    id_lookup = {}
    name_lookup = {}

    for channel in channels:

        if not isinstance(channel, dict):
            continue

        channel_id = normalize_id(channel.get("id"))
        channel_name = normalize_name(channel.get("name"))

        if channel_id:

            id_lookup.setdefault(channel_id, []).append(channel)

        if channel_name:

            name_lookup.setdefault(channel_name, []).append(channel)

    return id_lookup, name_lookup


# ============================================================
# MATCH CHANNEL
# ============================================================

def find_matching_channel(
    channel,
    id_lookup,
    name_lookup
):

    channel_id = normalize_id(channel.get("id"))
    channel_name = normalize_name(channel.get("name"))

    # First priority: exact channel ID.
    if channel_id and channel_id in id_lookup:

        candidates = id_lookup[channel_id]

        if len(candidates) == 1:
            return candidates[0], "ID"

        # If duplicate IDs exist, prefer matching name.
        for candidate in candidates:

            if (
                normalize_name(candidate.get("name"))
                == channel_name
            ):
                return candidate, "ID + NAME"

    # Second priority: unique normalized name.
    if channel_name and channel_name in name_lookup:

        candidates = name_lookup[channel_name]

        if len(candidates) == 1:
            return candidates[0], "NAME"

    return None, None


# ============================================================
# UPDATE ADDITIONAL KEYS
# ============================================================

def update_channel_keys(item, sportlink_channel):

    pairs = extract_key_pairs(sportlink_channel)

    if not pairs:
        return 0, False

    # Remove obsolete additional keys.
    # Keep original primary keys and keyId1/key1.
    for field in list(item.keys()):

        if re.fullmatch(r"keyId\d+", field):

            if int(field[5:]) >= 2:
                del item[field]

        elif re.fullmatch(r"key\d+", field):

            if int(field[3:]) >= 2:
                del item[field]

    added = 0

    # First valid Sportlink pair becomes keyId2/key2.
    for index, (kid, key) in enumerate(pairs, start=2):

        item[f"keyId{index}"] = kid
        item[f"key{index}"] = key

        added += 1

    return added, True


# ============================================================
# FILE HASH
# ============================================================

def file_hash(data):

    encoded = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SPORTLINK CHANNEL & DRM KEY UPDATER")
    print("=" * 70)

    session = create_session()

    # --------------------------------------------------------
    # FETCH SOURCE JSON
    # --------------------------------------------------------

    try:

        source_data = fetch_json(
            session,
            SOURCE_URL,
            "jnew5.json"
        )

        sportlink_data = fetch_json(
            session,
            SPORTLINK_URL,
            "jtvplus3.json"
        )

    except Exception as error:

        print("\nERROR: Data download failed.")
        print(error)
        sys.exit(1)

    # --------------------------------------------------------
    # VALIDATE JSON
    # --------------------------------------------------------

    if not isinstance(source_data, list):

        print("ERROR: jnew5.json must contain a JSON array.")
        sys.exit(1)

    try:

        sportlink_channels = get_sportlink_channels(
            sportlink_data
        )

    except Exception as error:

        print("ERROR:", error)
        sys.exit(1)

    if not sportlink_channels:

        print("ERROR: Sportlink channel list is empty.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SOURCE INFORMATION")
    print("=" * 70)

    print("Source channels:", len(source_data))
    print("Sportlink channels:", len(sportlink_channels))

    if isinstance(sportlink_data, dict):
        print(
            "Sportlink last updated:",
            sportlink_data.get("last_updated", "Not available")
        )

    # --------------------------------------------------------
    # BUILD LOOKUP
    # --------------------------------------------------------

    id_lookup, name_lookup = build_lookup(
        sportlink_channels
    )

    # --------------------------------------------------------
    # PROCESS CHANNELS
    # --------------------------------------------------------

    output = []

    matched_channels = 0
    unmatched_channels = 0
    updated_channels = 0
    total_keys = 0

    for position, channel in enumerate(
        source_data,
        start=1
    ):

        if not isinstance(channel, dict):

            output.append(channel)
            continue

        item = channel.copy()

        channel_name = channel.get("name", "Unknown")
        channel_id = normalize_id(channel.get("id"))

        print("\n" + "-" * 60)
        print(
            f"[{position}/{len(source_data)}] "
            f"{channel_name} | ID: {channel_id}"
        )

        matched, match_type = find_matching_channel(
            channel,
            id_lookup,
            name_lookup
        )

        if not matched:

            print("NO MATCH FOUND - Original retained.")

            unmatched_channels += 1
            output.append(item)
            continue

        matched_channels += 1

        print(
            f"MATCH FOUND using {match_type}: "
            f"{matched.get('name')} ({matched.get('id')})"
        )

        key_count, changed = update_channel_keys(
            item,
            matched
        )

        if changed:

            total_keys += key_count
            updated_channels += 1

            print(f"Updated additional keys: {key_count}")

            for index in range(2, key_count + 2):

                print(
                    f"  keyId{index}: "
                    f"{item[f'keyId{index}']}"
                )

        else:

            print("No valid Sportlink keys found.")

        output.append(item)

    # --------------------------------------------------------
    # FINAL DIAGNOSTICS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    print("Source channels:", len(source_data))
    print("Sportlink channels:", len(sportlink_channels))
    print("Matched channels:", matched_channels)
    print("Unmatched channels:", unmatched_channels)
    print("Channels with valid keys:", updated_channels)
    print("Total additional key pairs:", total_keys)

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if matched_channels == 0:

        print("\nERROR: No channels matched.")
        print("Existing output file will not be overwritten.")
        sys.exit(1)

    if total_keys == 0:

        print("\nERROR: No valid DRM key pairs extracted.")
        print("Existing output file will not be overwritten.")
        sys.exit(1)

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    output_path = Path(OUTPUT_FILE)

    old_hash = None

    if output_path.exists():

        try:

            with open(
                output_path,
                "r",
                encoding="utf-8"
            ) as file:

                old_data = json.load(file)

            old_hash = file_hash(old_data)

        except Exception:
            old_hash = None

    new_hash = file_hash(output)

    print("\n" + "=" * 70)
    print("SAVING OUTPUT")
    print("=" * 70)

    if old_hash == new_hash:

        print("JSON content is identical to existing output.")

    else:

        temporary_path = output_path.with_suffix(".tmp")

        with open(
            temporary_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output,
                file,
                indent=2,
                ensure_ascii=False
            )

        temporary_path.replace(output_path)

        print("SUCCESS: new1.json updated.")

    print("Output file:", output_path.resolve())
    print("SHA256:", new_hash)
    print("=" * 70)


if __name__ == "__main__":
    main()
