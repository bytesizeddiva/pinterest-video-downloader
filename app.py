"""
Pinterest Video Downloader
Created and maintained by bytesizeddiva
A modern web application for downloading Pinterest videos
"""

from flask import Flask, render_template, request, send_file, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import threading
import queue

app = Flask(__name__)

# Store active downloads
active_downloads = {}
download_results = {}

def download_pinterest_video(page_url, download_id):
    try:
        if "pinterest.com/pin/" not in page_url and "https://pin.it/" not in page_url:
            download_results[download_id] = {"error": "Invalid Pinterest URL"}
            return

        if active_downloads[download_id].get('cancelled', False):
            download_results[download_id] = {"error": "Download cancelled"}
            return

        if "https://pin.it/" in page_url:
            t_body = requests.get(page_url)
            if t_body.status_code != 200:
                download_results[download_id] = {"error": "Invalid URL or not working"}
                return
            soup = BeautifulSoup(t_body.content, "html.parser")
            href_link = (soup.find("link", rel="alternate"))['href']
            match = re.search('url=(.*?)&', href_link)
            page_url = match.group(1)

        body = requests.get(page_url)
        if body.status_code != 200:
            download_results[download_id] = {"error": "URL is invalid or not working"}
            return

        if active_downloads[download_id].get('cancelled', False):
            download_results[download_id] = {"error": "Download cancelled"}
            return

        soup = BeautifulSoup(body.content, "html.parser")
        extract_url = (soup.find("video", class_="hwa kVc MIw L4E"))['src']
        convert_url = extract_url.replace("hls", "720p").replace("m3u8", "mp4")
        
        # Download the video
        video_response = requests.get(convert_url, stream=True)
        if video_response.status_code == 200:
            filename = datetime.now().strftime("%d_%m_%H_%M_%S_") + ".mp4"
            filepath = os.path.join("downloads", filename)
            os.makedirs("downloads", exist_ok=True)
            
            if active_downloads[download_id].get('cancelled', False):
                download_results[download_id] = {"error": "Download cancelled"}
                return

            with open(filepath, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if active_downloads[download_id].get('cancelled', False):
                        # Delete partially downloaded file
                        f.close()
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        download_results[download_id] = {"error": "Download cancelled"}
                        return
                    if chunk:
                        f.write(chunk)
            
            download_results[download_id] = {"success": True, "filename": filename}
            return
    except Exception as e:
        download_results[download_id] = {"error": str(e)}
        return

    download_results[download_id] = {"error": "Could not find video in the Pinterest post"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "No URL provided"})
    
    # Generate unique download ID
    download_id = datetime.now().strftime("%Y%m%d%H%M%S")
    active_downloads[download_id] = {'cancelled': False}
    
    # Start download in background thread
    thread = threading.Thread(target=download_pinterest_video, args=(url, download_id))
    thread.daemon = True
    thread.start()
    
    # Return the download ID immediately
    return jsonify({"pending": True, "download_id": download_id})

@app.route('/status/<download_id>')
def check_status(download_id):
    if download_id in download_results:
        result = download_results[download_id]
        # Cleanup
        del download_results[download_id]
        if download_id in active_downloads:
            del active_downloads[download_id]
        return jsonify(result)
    elif download_id in active_downloads:
        return jsonify({"pending": True})
    return jsonify({"error": "Download not found"})

@app.route('/cancel/<download_id>', methods=['POST'])
def cancel_download(download_id):
    if download_id in active_downloads:
        active_downloads[download_id]['cancelled'] = True
        return jsonify({"success": True})
    return jsonify({"error": "Download not found"})

@app.route('/get-video/<filename>')
def get_video(filename):
    try:
        return send_file(f"downloads/{filename}", as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True) 