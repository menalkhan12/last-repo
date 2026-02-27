"""IST AI Voice Agent - Flask web server to serve the frontend."""
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)