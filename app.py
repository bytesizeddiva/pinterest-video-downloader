"""
Pinterest Video Downloader
Created and maintained by bytesizeddiva
A modern web application for downloading Pinterest videos
"""

import os
import re
import time
import uuid
from datetime import datetime
from html import escape as html_escape
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from flask import (Flask, Response, jsonify, render_template, request,
                   stream_with_context)

app = Flask(__name__)

# Short-lived references to resolved video files — nothing is written to disk;
# bytes are proxied straight through to the browser's own download manager.
download_tokens = {}

TOKEN_TTL = 600            # seconds a prepared download link stays valid
MAX_PAGE_ATTEMPTS = 4      # Pinterest sometimes serves variants without video data
MAX_PROBES = 4             # most candidate renditions to probe

REQUEST_TIMEOUT = (10, 30)   # (connect, read) seconds for every outbound request
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CDN_HEADERS = {"User-Agent": BROWSER_UA, "Accept": "*/*"}

# Strict host checks so /download cannot be pointed at arbitrary servers (SSRF)
PIN_HOST_RE = re.compile(
    r"^(?:[\w-]+\.)*pinterest\.(?:com|[a-z]{2}|co\.[a-z]{2}|com\.[a-z]{2})$", re.I)
SHORT_HOST_RE = re.compile(r"^(?:[\w-]+\.)*pin\.it$", re.I)
VIDEO_URL_RE = re.compile(r"https?://v1\.pinimg\.com/videos/[^\"'\\\s]+?\.(?:m3u8|mp4)")


class InvalidPinterestURL(ValueError):
    """Raised when the submitted URL is not a Pinterest pin page or pin.it link."""


class VideoUnavailable(Exception):
    """Raised when the pin exists but no usable MP4 could be fetched."""


def validate_pinterest_url(url):
    """Return 'short' for pin.it links, 'pin' for pin pages; raise otherwise."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise InvalidPinterestURL("Invalid Pinterest URL")
    host = parsed.hostname.lower()
    if SHORT_HOST_RE.match(host):
        return "short"
    if PIN_HOST_RE.match(host) and "/pin/" in parsed.path:
        return "pin"
    raise InvalidPinterestURL("Invalid Pinterest URL")


def _cleanup_tokens():
    """Drop expired download references."""
    now = time.time()
    for token in [t for t, e in download_tokens.items() if e["expires"] < now]:
        del download_tokens[token]


def resolve_short_url(page_url):
    """Follow a pin.it short link to the real Pinterest pin URL."""
    response = requests.get(page_url, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": BROWSER_UA})
    if response.status_code != 200:
        raise InvalidPinterestURL("Invalid URL or not working")
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all("link", rel="alternate"):
        target = parse_qs(urlparse(link.get("href", "")).query).get("url", [None])[0]
        if target:
            return target
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        return canonical["href"]
    raise InvalidPinterestURL("Could not resolve the pin.it short link")


def _rendition_rank(url):
    """Prefer universally playable H.264 renditions first (return tuple)."""
    if "/expMp4/" in url:
        tier = 0
    elif "/720p/" in url:
        tier = 1
    elif "/480p/" in url:
        tier = 2
    elif "/hevcMp4V3/" in url:
        tier = 3
    elif "h265-pt-mp4" in url:
        tier = 4
    else:
        tier = 5
    # Within a tier, prefer the 720-wide file over smaller ones
    return (tier, 0 if "720w" in url else 1)


def collect_candidates(page_html):
    """Every downloadable MP4 (plus legacy HLS→MP4 guesses) on a pin page."""
    raw = list(dict.fromkeys(VIDEO_URL_RE.findall(page_html.replace("\\/", "/"))))
    candidates = []
    for url in raw:
        if url.endswith(".mp4"):
            if re.search(r"_t\d+\.mp4$", url):  # multi-part segments can't stand alone
                continue
            candidates.append(url)
        elif url.endswith(".m3u8"):
            candidates.append(url.replace("hls", "720p").replace("m3u8", "mp4"))
            candidates.append(url.replace("hls", "480p").replace("m3u8", "mp4"))
    ordered, seen = [], set()
    for url in sorted(candidates, key=_rendition_rank):
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def probe_rendition(url, referer):
    """True if the CDN actually serves this rendition (missing ones 403)."""
    try:
        resp = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT,
                            headers={**CDN_HEADERS, "Referer": referer})
        status = resp.status_code
        resp.close()
        return status in (200, 206)
    except requests.exceptions.RequestException:
        return False


def prepare_download(page_url):
    """Resolve a Pinterest URL to a working direct-MP4 URL. Raises on failure.

    Returns (video_url, referer) — the referer is needed later when the
    browser pulls the file through /file/<token>.
    """
    kind = validate_pinterest_url(page_url)
    if kind == "short":
        page_url = resolve_short_url(page_url)

    # Pinterest occasionally serves a page variant without any video data
    # — retry a few times before giving up.
    candidates = []
    for _attempt in range(MAX_PAGE_ATTEMPTS):
        body = requests.get(page_url, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": BROWSER_UA})
        if body.status_code != 200:
            raise InvalidPinterestURL("URL is invalid or not working")
        candidates = collect_candidates(body.text)
        if candidates:
            break
        time.sleep(1.2)

    if not candidates:
        raise VideoUnavailable("Could not find video in the Pinterest post")

    for url in candidates[:MAX_PROBES]:
        if probe_rendition(url, page_url):
            return url, page_url
    raise VideoUnavailable("Could not download the video file")





@app.route('/')
def home():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    """Validate + resolve the pin to a direct MP4 and hand out a short-lived
    reference. No file is stored — bytes stream straight to the browser."""
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        video_url, referer = prepare_download(url)
    except InvalidPinterestURL as exc:
        return jsonify({"error": str(exc)}), 400
    except VideoUnavailable as exc:
        return jsonify({"error": str(exc)}), 422
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach Pinterest, please try again"}), 502
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    _cleanup_tokens()
    token = uuid.uuid4().hex[:20]
    download_tokens[token] = {
        "url": video_url,
        "referer": referer,
        "expires": time.time() + TOKEN_TTL,
    }
    return jsonify({"download_id": token})


def _file_error_page(message):
    """HTML page for failures after the browser already navigated to /file —
    sends the user back to the app automatically."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>Download failed</title>'
        '<meta http-equiv="refresh" content="4;url=/">'
        '<style>body{font-family:system-ui,sans-serif;display:grid;place-items:center;'
        'min-height:100vh;margin:0;background:#111;color:#eee;text-align:center}'
        'a{color:#8ab4f8}</style></head><body><div>'
        f'<p>{html_escape(message)}</p>'
        '<p><a href="/">Back to the app</a> — redirecting…</p>'
        '</div></body></html>'
    ), 502


@app.route('/file/<token>')
def serve_file(token):
    """Stream the video through to the browser as a normal download — the
    browser's own downloader decides where to save it ('Ask where to save',
    default folder, downloads bar, etc.)."""
    _cleanup_tokens()
    entry = download_tokens.get(token)
    if entry is None:
        return _file_error_page("This download link has expired. Please start again.")

    try:
        upstream = requests.get(entry["url"], stream=True,
                                timeout=REQUEST_TIMEOUT,
                                headers={**CDN_HEADERS, "Referer": entry["referer"]})
    except requests.exceptions.RequestException:
        return _file_error_page("Could not reach the video server. Please try again.")

    if upstream.status_code not in (200, 206):
        upstream.close()
        return _file_error_page("The video file is no longer available. Please try again.")

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    filename = "pinterest_video_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".mp4"
    return Response(
        stream_with_context(generate()),
        mimetype="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


if __name__ == '__main__':
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
