from flask import request, jsonify
import os
from detector import analyze_video

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "video" not in request.files:
            return jsonify({"success": False, "error": "No video uploaded"}), 400

        video = request.files["video"]
        if video.filename == "":
            return jsonify({"success": False, "error": "Empty filename"}), 400

        save_path = os.path.join("uploads", video.filename)
        os.makedirs("uploads", exist_ok=True)
        video.save(save_path)

        results = analyze_video(save_path)

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
