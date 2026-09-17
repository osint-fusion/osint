import csv
import io
import json
import logging
import os
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from core.database import Database
from core.scanner import ScanEngine
from core.validator import TargetValidator

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/osint_fusion.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__, static_folder="static")
CORS(app)

db = Database()
engine = ScanEngine(db)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "OSINT FUSION Backend"})

@app.route("/api/tools", methods=["GET"])
def get_tools():
    return jsonify({"tools": engine.get_tool_statuses()})

@app.route("/api/scan", methods=["POST"])
def create_scan():
    data = request.json or {}
    target_type = data.get("type")
    target = data.get("target")

    if target_type in ["email", "phone"]:
        return jsonify({
            "error": "تجنب إجراء Reverse Identity Lookup لحماية الخصوصية."
        }), 400

    is_valid, validated_target = TargetValidator.validate(target_type, target)
    if not is_valid:
        return jsonify({"error": validated_target}), 400

    logging.info(f"بدء الفحص: {target_type} -> {validated_target}")
    scan_id = engine.start_scan(target_type, validated_target)
    return jsonify({"scan_id": scan_id, "status": "running", "target": validated_target})

@app.route("/api/scan/<scan_id>", methods=["GET"])
def get_scan_status(scan_id):
    scan_data = db.get_scan(scan_id)
    if not scan_data:
        return jsonify({"error": "الفحص غير موجود"}), 404
    return jsonify(scan_data)

@app.route("/api/scan/<scan_id>/cancel", methods=["POST"])
def cancel_scan(scan_id):
    success = engine.cancel_scan(scan_id)
    if success:
        return jsonify({"message": "تم إلغاء الفحص بنجاح"})
    return jsonify({"error": "تعذر إلغاء الفحص"}), 400

@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify({"history": db.get_history()})

@app.route("/api/scan/<scan_id>/delete", methods=["DELETE"])
def delete_scan(scan_id):
    db.delete_scan(scan_id)
    return jsonify({"message": "تم الحذف بنجاح"})

@app.route("/api/scan/<scan_id>/export", methods=["GET"])
def export_scan(scan_id):
    fmt = request.args.get("format", "json").lower()
    scan_data = db.get_scan(scan_id)
    if not scan_data:
        return jsonify({"error": "Not found"}), 404

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Tool", "Source", "Type", "Value", "Confidence"])
        for tool_res in scan_data.get("results", []):
            for item in tool_res.get("parsed_results", []):
                writer.writerow([
                    tool_res["tool_name"],
                    item.get("source", ""),
                    item.get("type", ""),
                    item.get("value", ""),
                    item.get("confidence", "")
                ])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=scan_{scan_id}.csv"}
        )

    return jsonify(scan_data)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8787, debug=False)