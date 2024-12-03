# Pinterest Video Downloader

A modern web application for downloading Pinterest videos, featuring a clean interface and multiple theme options. Created and maintained by bytesizeddiva.

![Themes Preview](themes.png)

## Features

- 🎨 Multiple themes (Light, Tokyo, Matrix)
- 🌐 Web-based interface
- ⚡ Real-time download progress
- 🎯 Support for both Pinterest and pin.it URLs
- 🔄 Download cancellation support
- 📱 Responsive design

## Technology Stack

- **Backend**: Python with Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Dependencies**:
  - Flask
  - Requests
  - BeautifulSoup4
  - Threading support for concurrent downloads

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PinterestVideoDownloader.git
   cd PinterestVideoDownloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Paste a Pinterest video URL and click Download

## Supported URLs

- Direct Pinterest URLs (https://pinterest.com/pin/...)
- Short URLs (https://pin.it/...)

## Features in Detail

### Theme System
- **Light Mode**: Clean, minimal design
- **Tokyo Mode**: Dark theme with cyberpunk-inspired colors
- **Matrix Mode**: Classic matrix theme with green accents

### Download Management
- Real-time progress tracking
- Ability to cancel ongoing downloads
- Chunked downloading for better performance
- Automatic cleanup of cancelled downloads

## Technical Details

The application uses a threaded download system to handle concurrent requests efficiently. Downloads are processed in the background, allowing for proper cancellation and progress tracking.

### Architecture
- Frontend: Modern HTML5 with vanilla JavaScript
- Backend: Flask with threading support
- File handling: Chunked downloads with cancellation support

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