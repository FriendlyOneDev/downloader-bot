"""Instagram fallback that resolves media through snapsave.app.

snapsave fetches the post from its own infrastructure, so it reaches content
the logged-out libraries cannot - notably age-restricted posts, which are
refused for the bot's own account but not for snapsave's.

The service answers with obfuscated JavaScript meant to be eval'd by a browser.
The packer is reimplemented here in plain Python so the container needs no JS
runtime. That format is deliberately obscured and carries no compatibility
promise, so breakage is expected rather than exceptional - keep this method
last in the chain and let the maintained libraries handle the common cases.
"""

import os
import re
import requests

ENDPOINT = "https://snapsave.app/action.php?lang=en"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://snapsave.app/",
    "Origin": "https://snapsave.app",
}

# Digit alphabet used by the payload's base converter.
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"

# Matches the packed call: }("<data>",<u>,"<keys>",<t>,<e>,<f>))
PACKED_RE = re.compile(r'\}\("(.*?)",(\d+),"(.*?)",(\d+),(\d+),(\d+)\)\)', re.S)
URL_RE = re.compile(r'https?:\\?/\\?/[^"\'\\ <>]+')


def _to_base10(digits, base):
    """Read `digits` as a base-`base` number (payload's _0xe98c, f=10)."""
    src = ALPHABET[:base]
    value = 0
    for char in digits:
        if char in src:
            value = value * base + src.index(char)
    return value


def _decode(data, keys, offset, base):
    """Reimplementation of the payload's eval(function(h,u,n,t,e,r){...})."""
    out = []
    i = 0
    separator = keys[base]
    while i < len(data):
        chunk = ""
        while i < len(data) and data[i] != separator:
            chunk += data[i]
            i += 1
        i += 1  # skip the separator
        for index, key in enumerate(keys):
            chunk = chunk.replace(key, str(index))
        out.append(chr(_to_base10(chunk, base) - offset))
    # JS does decodeURIComponent(escape(r)): latin-1 bytes read back as UTF-8.
    return "".join(out).encode("latin-1", "ignore").decode("utf-8", "ignore")


def unpack(payload):
    """Recover the HTML that snapsave's obfuscated response would have injected."""
    match = PACKED_RE.search(payload)
    if not match:
        raise ValueError("snapsave response is not in the expected packed format")
    data, _u, keys, offset, base, _f = match.groups()
    return _decode(data, keys, int(offset), int(base))


def _media_links(html):
    """Pull the download links out of the decoded markup, preserving order."""
    links = []
    for raw in URL_RE.findall(html):
        link = raw.replace("\\", "")
        # Thumbnails share the CDN host but are previews, not the media itself.
        if "/thumb" in link:
            continue
        if "rapidcdn" in link or "cdninstagram" in link or ".mp4" in link:
            if link not in links:
                links.append(link)
    return links


def resolve(url):
    """Ask snapsave for the media links behind an Instagram URL."""
    response = requests.post(ENDPOINT, data={"url": url}, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return _media_links(unpack(response.text))


def _extension(head, content_type):
    if head[4:8] == b"ftyp":
        return "mp4"
    if head[:2] == b"\xff\xd8":
        return "jpg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if "video" in content_type:
        return "mp4"
    if "png" in content_type:
        return "png"
    if "image" in content_type:
        return "jpg"
    raise ValueError(f"unrecognised media type ({content_type or 'unknown'})")


def _save(link, base_name):
    response = requests.get(link, headers=HEADERS, timeout=90, stream=True)
    response.raise_for_status()

    chunks = response.iter_content(chunk_size=65536)
    head = next(chunks, b"")
    path = f"{base_name}.{_extension(head, response.headers.get('Content-Type', ''))}"

    with open(path, "wb") as f:
        f.write(head)
        for chunk in chunks:
            f.write(chunk)

    if os.path.getsize(path) < 1000:
        os.remove(path)
        raise ValueError("downloaded file too small, likely an error response")
    return path


def download(shortcode):
    """Download every media item of a post, named for the file handler's glob."""
    links = resolve(f"https://www.instagram.com/p/{shortcode}/")
    if not links:
        raise RuntimeError("snapsave returned no media links")

    saved = []
    for index, link in enumerate(links, start=1):
        try:
            saved.append(_save(link, f"{shortcode}_{index}"))
        except Exception as e:
            print(f"snapsave: item {index} failed ({e})")

    if not saved:
        raise RuntimeError(f"snapsave resolved {len(links)} link(s) but none downloaded")
    return saved


if __name__ == "__main__":
    import sys

    print(download(sys.argv[1] if len(sys.argv) > 1 else "DbdspR4AL0v"))
