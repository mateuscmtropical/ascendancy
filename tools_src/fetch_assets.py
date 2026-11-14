"""Download the CC0 source packs into tools/vendor/ (gitignored).

Every pack is CC0 (License.txt inside each zip, checked 2026-11-14).
Usage: python tools_src/fetch_assets.py [pack_name ...]
"""

import http.cookiejar
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent.parent / "tools" / "vendor"

PACKS = {
    "ubc": ("quaternius", "universal-base-characters", "Universal Base Characters[Standard].zip"),
    "outfits": ("quaternius", "modular-character-outfits-fantasy", "Modular Character Outfits - Fantasy[Standard].zip"),
    "ual1": ("quaternius", "universal-animation-library", "Universal Animation Library[Standard].zip"),
    "ual2": ("quaternius", "universal-animation-library-2", "Universal Animation Library 2[Standard].zip"),
    "nature": ("quaternius", "stylized-nature-megakit", "Stylized Nature MegaKit[Standard].zip"),
    "village": ("quaternius", "medieval-village-megakit", "Medieval Village MegaKit[Standard].zip"),
    "props": ("quaternius", "fantasy-props-megakit", "Fantasy Props MegaKit[Standard].zip"),
    "kaykit": ("kaylousberg", "kaykit-character-animations", "Free 1.1"),
}


def build_opener() -> urllib.request.OpenerDirector:
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    opener.addheaders = [("User-Agent", "Mozilla/5.0")]

    return opener


def read_csrf_token(page_html: str) -> str:
    match = re.search(r'csrf_token" value="([^"]+)"', page_html)

    return match.group(1)


def find_upload_id(download_page_html: str, file_title: str) -> str:
    for match in re.finditer(r'data-upload_id="(\d+)"', download_page_html):
        following_html = download_page_html[match.end():match.end() + 1500]

        if f'title="{file_title}"' in following_html:
            return match.group(1)

    raise LookupError(f"upload not found: {file_title}")


def download_pack_bytes(user: str, game: str, file_title: str) -> bytes:
    opener = build_opener()
    game_url = f"https://{user}.itch.io/{game}"
    game_page = opener.open(game_url).read().decode()
    csrf_token = read_csrf_token(game_page)
    form_body = urllib.parse.urlencode({"csrf_token": csrf_token}).encode()

    download_url = json.loads(opener.open(game_url + "/download_url", form_body).read())["url"]
    download_page = opener.open(download_url).read().decode()
    upload_id = find_upload_id(download_page, file_title)

    query = urllib.parse.urlencode({"source": "view_game", "as_props": 1, "after_download_lightbox": "true"})
    file_response = json.loads(opener.open(f"{game_url}/file/{upload_id}?{query}", form_body).read())

    return opener.open(file_response["url"]).read()


def fetch_pack(pack_name: str) -> None:
    user, game, file_title = PACKS[pack_name]
    target_dir = VENDOR_DIR / pack_name

    if target_dir.exists():
        print(f"{pack_name}: already present")

        return

    archive_bytes = download_pack_bytes(user, game, file_title)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive.extractall(target_dir)

    print(f"{pack_name}: extracted to {target_dir}")


if __name__ == "__main__":
    requested_packs = sys.argv[1:] or list(PACKS)

    for requested_pack in requested_packs:
        fetch_pack(requested_pack)
