#!/usr/bin/env python3
"""
More robust Apache index recursive downloader.

Requires:
    pip install requests beautifulsoup4
"""
import argparse
import os
import sys
import time
import pprint
import requests
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup

from versions import UrbanAirData

# ---------- CONFIG ----------
MAX_RETRIES = 3
RETRY_DELAY = 1.0
SMALL_GET_BYTES = 2048  # bytes to request for detection
# ----------------------------

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117 Safari/537.36"
    }
)


def ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def canonical_base(url: str) -> str:
    p = urlparse(url)
    path = p.path if p.path.endswith("/") else p.path + "/"
    return f"{p.scheme}://{p.netloc}{path}"


def safe_request(method, url, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.request(
                method, url, timeout=20, allow_redirects=True, **kwargs
            )
            return resp
        except requests.RequestException as e:
            print(
                f"⚠ Request error ({method}) {url}: {e} (attempt {attempt}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise


def looks_like_apache_index(text: str) -> bool:
    # simple heuristics: "Index of" title or typical <pre> listing present
    head = text[:2000].lower()
    return (
        ("index of" in head)
        or ("<pre" in head)
        or ("name                    last modified" in head)
    )


def is_directory(full_url: str, href: str) -> bool:
    # If the link text/path ends with '/', treat as directory
    if href.endswith("/"):
        return True

    # Try a small GET (safer than HEAD which is often blocked)
    try:
        # Range header to limit downloaded bytes
        resp = safe_request(
            "GET",
            full_url,
            stream=True,
            headers={"Range": f"bytes=0-{SMALL_GET_BYTES-1}"},
        )
        ct = resp.headers.get("Content-Type", "").lower()
        # if server redirected and final URL ends with '/', treat as dir
        if resp.url.endswith("/"):
            return True
        if "text/html" in ct:
            # check for index-like HTML
            # read small chunk of text safely
            try:
                snippet = resp.content.decode(errors="ignore")
            except Exception:
                snippet = ""
            if looks_like_apache_index(snippet):
                return True
    except Exception:
        # Could not fetch/detect — assume file (safer)
        return False

    return False


def sanitize_local_path_from_url(full_url: str, base_root: str) -> str:
    # remove query/fragment and map path relative to base_root
    p_full = urlparse(full_url)
    # build absolute path (path only)
    path = p_full.path
    # relative to base root path
    p_base = urlparse(base_root)
    rel = path[len(p_base.path) :].lstrip("/")
    # decode percent-encoding
    rel = unquote(rel)
    return rel


def download_file(full_url: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if os.path.exists(local_path):
        print(f" Skipping existing: {local_path}")
        return
    print(f"Downloading: {full_url} -> {local_path}")
    resp = safe_request("GET", full_url, stream=True)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def crawl_dir(url: str, outdir: str, base_root: str, visited=set()):
    url = ensure_trailing_slash(url)
    if url in visited:
        return
    visited.add(url)
    try:
        resp = safe_request("GET", url)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    if resp.status_code >= 400:
        print(f"HTTP {resp.status_code} for {url}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    anchors = soup.find_all("a")
    if not anchors:
        # sometimes directory listings live in <pre> with raw lines — try to parse them
        text = resp.text
        for line in text.splitlines():
            # very simple heuristic: if line contains href-like text, skip complicated parsing here
            pass

    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        # skip parent references
        if href in ("../", "..", "/"):
            continue
        if href.startswith("?"):
            continue

        full = urljoin(url, href)
        # ensure we stay under base_root (same scheme+netloc+path prefix)
        if not full.startswith(base_root):
            # skip external or up-tree links
            continue

        # determine local path (strip query/fragment)
        rel_local = sanitize_local_path_from_url(full, base_root)
        if not rel_local:
            # it refers to the base directory itself
            continue
        local_path = os.path.join(outdir, rel_local)

        try:
            if is_directory(full, href):
                # ensure dir exists locally and recurse
                os.makedirs(local_path, exist_ok=True)
                # Some servers require requesting the slash-terminated URL; enforce it
                next_url = ensure_trailing_slash(full)
                crawl_dir(next_url, outdir, base_root, visited)
            else:
                # file: ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                download_file(full, local_path)
        except Exception as e:
            print(f"Error with {full}: {e}")


def main(argv):
    parser = argparse.ArgumentParser(description="Downdloads UrbanAir test data")
    parser.add_argument(
        "-v", dest="version", help="Version", required=False, default=None
    )
    parser.add_argument(
        "-l",
        dest="list",
        action="store_true",
        help="List version",
        required=False,
        default=False,
    )

    if len(argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    uad = UrbanAirData()
    if args.list:
        for url in uad.urls:
            if 'exporter.nsc.liu.se' in uad.urls[url]['url']:
                print("\t\t -- Data versions available for direct (url) download  --\n")
                print(f" ========================")
                print(f"      version : {url}    ")
                print(f" ========================\n")
                pprint.pprint(uad.urls[url])
        sys.exit()

    # Target URL
    version = UrbanAirData().url_version(args.version)
    if version is None:
        sys.exit(1)
    base = ensure_trailing_slash(version)
    print(f"Download UrbanAir data v{args.version} from {base}")
    base_root = canonical_base(base)

    output_dir = f"data/{version}"
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    crawl_dir(base_root, output_dir, base_root)
    print("\n Done.")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
