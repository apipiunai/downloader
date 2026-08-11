from flask import Flask, send_file, request, jsonify, render_template
from flask_cors import CORS
from io import BytesIO
from tempfile import TemporaryDirectory
import os
import yt_dlp

app = Flask(__name__)
CORS(app)

class MediaDownloader:
    def download_audio(self, url):
        with TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "audio.%(ext)s")
            options = {
                "format": "bestaudio/best",
                "outtmpl": output,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            file_path = os.path.join(temp_dir, "audio.mp3")
            with open(file_path, "rb") as f:
                return BytesIO(f.read())

    def download_video(self, url):
        with TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "video.%(ext)s")
            options = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": output,
                "merge_output_format": "mp4",
                "quiet": True,
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
            download_name="audio.mp3"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            download_name="video.mp4"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)