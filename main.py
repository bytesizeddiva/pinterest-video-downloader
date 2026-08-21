"""Pinterest video downloader — CLI. Made by bytesizeddiva."""
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

REQUEST_TIMEOUT = (10, 30)
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
VIDEO_URL_RE = re.compile(r"https?://v1\.pinimg\.com/videos/[^\"'\\\s]+?\.(?:m3u8|mp4)")


def clear_screen():
    """Clear the terminal on Windows/macOS/Linux (only when interactive)."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def find_video_url(soup, html):
    """Locate the Pinterest CDN video URL, tolerating markup changes."""
    video = soup.find("video", class_="hwa kVc MIw L4E")
    if video and "pinimg.com" in (video.get("src") or ""):
        return video["src"]
    for tag in soup.find_all("video"):
        if "pinimg.com" in (tag.get("src") or ""):
            return tag["src"]
    match = VIDEO_URL_RE.search(html) or VIDEO_URL_RE.search(html.replace("\\/", "/"))
    return match.group(0) if match else None


def download_file(url, filename):
    response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": BROWSER_UA})
    response.raise_for_status()
    file_size = int(response.headers.get('Content-Length', 0))

    with open(filename, 'wb') as f:
        with tqdm(total=file_size or None, desc=f'Downloading {filename}',
                  unit='B', unit_scale=True, unit_divisor=1024) as progress:
            for data in response.iter_content(1024):
                f.write(data)
                progress.update(len(data))


def main():
    clear_screen()
    page_url = input("Enter page url : ").strip()

    # checking entered url is correct
    if ("pinterest.com/pin/" not in page_url and "https://pin.it/" not in page_url):
        print("Entered url is invalid")
        sys.exit(1)

    if "https://pin.it/" in page_url:  # pin url short check
        print("extracting original pin link")
        t_body = requests.get(page_url, timeout=REQUEST_TIMEOUT,
                              headers={"User-Agent": BROWSER_UA})
        if t_body.status_code != 200:
            print("Entered URL is invalid or not working.")
            sys.exit(1)
        soup = BeautifulSoup(t_body.content, "html.parser")
        link = soup.find("link", rel="alternate")
        href = link.get("href", "") if link else ""
        target = parse_qs(urlparse(href).query).get("url", [None])[0]
        if not target:
            print("Could not extract the original pin link.")
            sys.exit(1)
        page_url = target  # update page url

    print("fetching content from given url")
    # Pinterest occasionally serves a variant without video data — retry a few times
    extract_url = None
    for _attempt in range(3):
        body = requests.get(page_url, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": BROWSER_UA})
        if body.status_code != 200:  # checks status code
            print("Entered URL is invalid or not working.")
            sys.exit(1)

        soup = BeautifulSoup(body.content, "html.parser")  # parsing the content
        extract_url = find_video_url(soup, body.text)
        if extract_url:
            break
        time.sleep(1.5)

    if not extract_url:
        print("Could not find a video in the given pin.")
        sys.exit(1)

    print("Fetched content Successful.")
    # converting m3u8 to V_720P's url
    convert_url = extract_url.replace("hls", "720p").replace("m3u8", "mp4")
    print("Downloading file now!")
    # downloading the file
    filename = datetime.now().strftime("%d_%m_%H_%M_%S") + ".mp4"
    download_file(convert_url, filename)
    print(f"Saved as {filename}")


if __name__ == "__main__":
    main()
