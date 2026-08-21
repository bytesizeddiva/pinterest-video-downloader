# Pinterest Video Downloader

A modern web application for downloading Pinterest videos, featuring a clean interface and multiple theme options. Created and maintained by bytesizeddiva.

## Features

- 🎨 Multiple themes (Light, Tokyo, Matrix)
- 📥 Browser-native downloads — the file lands wherever *your* browser is configured to save it
- 🌐 Web-based interface
- 🎯 Support for both Pinterest and pin.it URLs
- 🛑 One-click cancel while the video is being prepared
- 📱 Responsive design

## Technology Stack

- **Backend**: Python with Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Dependencies**:
  - Flask
  - Requests
  - BeautifulSoup4
  - Threading support for concurrent downloads

## Prerequisites

- **Node.js** 18+ (used to orchestrate setup and dev commands)
- **Python** 3.10+ (the app itself is Flask/Python)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bytesizeddiva/PinterestVideoDownloader.git
   cd PinterestVideoDownloader
   ```

2. Install everything (creates a Python virtualenv and installs pinned dependencies automatically):
   ```bash
   npm install
   ```

## Usage

| Command | Description |
|---|---|
| `npm run dev` | Start the server with Flask debug/reloader mode |
| `npm start` | Start the server without debug mode |
| `npm run cli` | Run the classic CLI downloader |
| `npm run setup` | (Re)create the `.venv` from `requirements.txt` |
| `npm run audit` | Run `pip-audit` against installed packages (CVE check) |

1. Start the server:
   ```bash
   npm run dev
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Paste a Pinterest video URL and click Download

Configuration via environment variables: `PORT` (default `5000`), `HOST` (default `127.0.0.1`), `FLASK_DEBUG=1` to enable debug mode.

### Running without npm (pure Python)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Dependencies & security

All Python dependencies are pinned to exact versions in `requirements.txt` (including transitive ones) and verified clean against known CVEs with `npm run audit` (`pip-audit` + OSV/PyPI advisory data).

## Supported URLs

- Direct Pinterest URLs (https://pinterest.com/pin/...)
- Short URLs (https://pin.it/...)

## Features in Detail

### Theme System
- **Light Mode**: Clean, minimal design
- **Tokyo Mode**: Dark theme with cyberpunk-inspired colors
- **Matrix Mode**: Classic matrix theme with green accents
- **Neon Mode**: Vibrant neon colors with glowing effects
- **Cyber Mode**: Futuristic cyan theme with sleek design
- **Catppuccin Mode**: Soothing pastel theme with modern aesthetics
- **Synthwave Mode**: Retro-futuristic 80s inspired theme with neon pink and purple
- **Nordic Mode**: Minimalist frost-inspired theme with arctic colors
- **Dracula Mode**: Rich, vibrant colors on a dark background

### Theme Details

#### Recent Additions
- **Neon**: Electric neon colors with pink and cyan accents
- **Cyber**: Futuristic design with cyan as primary color
- **Catppuccin**: Modern pastel theme with soft, eye-friendly colors
- **Synthwave**: 80s retro aesthetic with glowing effects and gradients
- **Nordic**: Scandinavian-inspired minimalist design with frost effects
- **Dracula**: Popular dark theme with vibrant accents and smooth transitions

Each theme features:
- Custom color palettes
- Unique visual effects
- Responsive design elements
- Smooth transitions
- Hover animations
- Consistent styling across all components

To change themes:
1. Click the theme dropdown in the top-right corner
2. Select your preferred theme
3. The change applies instantly with no page reload

### Download Management
- Browser-native downloads with real progress in the browser's downloads bar
- Respects your browser's save settings (e.g. "Ask where to save each file")
- Nothing is written to the server's disk — video bytes are streamed straight through
- Short-lived (10-minute) prepared links with automatic cleanup
- One-click cancel while the video is being prepared

## Technical Details

The app prepares a download in one step (validate → resolve short links → find every MP4 rendition Pinterest offers → probe until one actually streams), then hands a short-lived token to the browser. The browser pulls the file through the streaming endpoint, so **no video is ever stored on the server** and the browser's own downloader handles progress and save location.

### Architecture
- Frontend: Modern HTML5 with vanilla JavaScript
- Backend: Flask with a streaming proxy endpoint (`/file/<token>`)
- File handling: streamed end-to-end with `Content-Disposition: attachment` (chunked, no disk writes)

## Limitations

- Works with Pinterest's current HTML structure (as of 2024)
- Requires active internet connection
- Supports only video content from Pinterest

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- Original CLI version: bytesizeddiva
- Web Interface & Enhancements: bytesizeddiva

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Made with ❤️ by bytesizeddiva
