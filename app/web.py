"""Flask app: token endpoint, health, static frontend. Bind 0.0.0.0:PORT for Render."""
import os
import uuid

from flask import Flask, jsonify, request, send_from_directory

from config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL

app = Flask(__name__, static_folder="static", static_url_path="")


def _create_token(room_name: str, participant_identity: str, participant_name: str) -> str:
    from livekit.api import AccessToken, VideoGrants
    token = AccessToken(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    token.with_identity(participant_identity)
    token.with_name(participant_name or "Caller")
    token.with_grants(VideoGrants(room_join=True, room=room_name))
    return token.to_jwt()


@app.route("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.route("/token", methods=["POST"])
def token() -> tuple:
    """Issue LiveKit token. Body: room_name (optional), participant_identity (optional), participant_name (optional)."""
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return jsonify({"error": "LiveKit not configured"}), 500
    data = request.get_json() or {}
    room_name = data.get("room_name") or f"ist-call-{uuid.uuid4().hex[:12]}"
    participant_identity = data.get("participant_identity") or f"user-{uuid.uuid4().hex[:8]}"
    participant_name = data.get("participant_name") or "Caller"
    jwt_token = _create_token(room_name, participant_identity, participant_name)
    return jsonify({
        "server_url": LIVEKIT_URL,
        "participant_token": jwt_token,
        "room_name": room_name,
    }), 201


@app.route("/")
def index() -> tuple:
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path: str) -> tuple:
    return send_from_directory(app.static_folder, path)


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
