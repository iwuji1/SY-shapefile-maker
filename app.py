from flask import Flask, request, render_template, send_file
import os
import uuid
from postcodes import process_data

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def process():
    file = request.files.get("file")
    if not file:
        return {"error": "No file uploaded"}, 400
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.csv")
    output_zip = os.path.join(OUTPUT_FOLDER, "South_Yorkshire_shape.zip")
    file.save(input_path)
    process_data(input_path)
    return send_file(output_zip, mimetype="application/zip")