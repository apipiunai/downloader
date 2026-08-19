from flask import Flask, send_file, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
from tempfile import TemporaryDirectory
import os
import yt_dlp

app = Flask(__name__)
CORS(app)


class MediaDownloader:
    def __init__(self):
        # Headers más realistas
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        # Opciones base comunes
        self.base_opts = {
            "quiet": False,
            "no_warnings": False,
            "http_headers": self.headers,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "extractor_args": {
                "youtube": {
                    # android suele ser el más estable actualmente contra SABR/403
                    "player_client": ["android", "web"],
                }
            },
            # Descomenta UNA de estas dos líneas si tienes cookies:
            # "cookiesfrombrowser": ("chrome",),          # más fácil
            # "cookiefile": "cookies.txt",                # más controlado
        }

    def download_audio(self, url: str) -> BytesIO:
        with TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "audio.%(ext)s")

            options = {
                **self.base_opts,
                "format": "bestaudio/best",
                "outtmpl": output,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            file_path = os.path.join(temp_dir, "audio.mp3")
            with open(file_path, "rb") as f:
                return BytesIO(f.read())

    def download_video(self, url: str) -> BytesIO:
        with TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "video.%(ext)s")

            options = {
                **self.base_opts,
                "format": "bestvideo+bestaudio/best",
                "outtmpl": output,
                "merge_output_format": "mp4",
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            file_path = os.path.join(temp_dir, "video.mp4")
            with open(file_path, "rb") as f:
                return BytesIO(f.read())


downloader = MediaDownloader()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download/audio", methods=["GET", "POST"])
def download_audio():
    url = request.args.get("url") or (request.json.get("url") if request.is_json else None)
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        audio_bytes = downloader.download_audio(url)
        audio_bytes.seek(0)
        return send_file(
            audio_bytes,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="audio.mp3",
        )
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "Video bloqueado por YouTube (403). Prueba con cookies o actualiza yt-dlp."
        elif "deno" in error_msg.lower() or "javascript" in error_msg.lower():
            error_msg = "Falta runtime de JavaScript. Instala Deno o Node.js."
        print(f"Download error: {e}")
        return jsonify({"error": error_msg}), 500


@app.route("/download/video", methods=["GET", "POST"])
def download_video():
    url = request.args.get("url") or (request.json.get("url") if request.is_json else None)
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        video_bytes = downloader.download_video(url)
        video_bytes.seek(0)
        return send_file(
            video_bytes,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="video.mp4",
        )
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "Video bloqueado por YouTube (403). Prueba con cookies o actualiza yt-dlp."
        elif "deno" in error_msg.lower() or "javascript" in error_msg.lower():
            error_msg = "Falta runtime de JavaScript. Instala Deno o Node.js."
        print(f"Download error: {e}")
        return jsonify({"error": error_msg}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)