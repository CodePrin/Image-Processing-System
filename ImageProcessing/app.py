# app.py
import os
import pandas as pd
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import uuid

app = Flask(__name__)

# Folder Setup
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed_images'
OUTPUT_CSV = 'output.csv'
DB_FILE = 'image_data.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


# URL Regex
URL_REGEX = re.compile(
    r'^(https?://)?([a-zA-Z0-9.-]+)(\.[a-zA-Z]{2,})(/[\w./?%&=+-]*)?$'
)


# Database Setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id TEXT PRIMARY KEY,
                        serial_number TEXT,
                        product_name TEXT,
                        input_image_urls TEXT,
                        output_image_urls TEXT,
                        status TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
                        request_id TEXT PRIMARY KEY,
                        status TEXT,
                        message TEXT,
                        total_rows INTEGER
                    )''')
    conn.commit()
    conn.close()

init_db()


# Helper Functions
def is_valid_url(url):
    return bool(URL_REGEX.match(url.strip()))

def get_valid_image_url(url):
    """Convert GitHub/Drive links to direct links if needed."""
    url = str(url).strip()
    if 'drive.google.com' in url:
        file_id = re.findall(r'/d/([a-zA-Z0-9_-]+)', url)
        if file_id:
            return f'https://drive.google.com/uc?export=download&id={file_id[0]}'
    if 'github.com' in url and 'raw.githubusercontent.com' not in url:
        return url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    return url

def download_and_process_image(url, serial_number):
    try:
        url = get_valid_image_url(url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((300, 300))
        filename = f"{uuid.uuid4().hex}_{serial_number}.jpg"
        save_path = os.path.join(PROCESSED_FOLDER, filename)
        img.save(save_path, optimize=True, quality=50)
        return filename  # Return filename for Output URL
    except Exception as e:
        return f"Error: {str(e)}"

def insert_request(request_id, status="Pending", message="", total_rows=0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO requests (request_id, status, message, total_rows) VALUES (?, ?, ?, ?)',
                   (request_id, status, message, total_rows))
    conn.commit()
    conn.close()

def update_request(request_id, status, message, total_rows):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE requests SET status=?, message=?, total_rows=? WHERE request_id=?',
                   (status, message, total_rows, request_id))
    conn.commit()
    conn.close()

def save_output_csv(results):
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)


# CSV Processing
def process_csv(file_path, request_id, host_url):
    try:
        df = pd.read_csv(file_path)
        required_cols = ['Serial Number', 'Product Name', 'Input Image Urls']
        if not all(col in df.columns for col in required_cols):
            update_request(request_id, "Failed", "CSV missing required columns", 0)
            return

        total_rows = len(df)
        results = []

        for idx, row in df.iterrows():
            serial_number = str(row['Serial Number'])
            product_name = str(row['Product Name'])
            input_urls_raw = str(row['Input Image Urls'])
            input_urls = [url.strip() for url in input_urls_raw.split(',') if url.strip()]
            output_urls = []

            for url in input_urls:
                if not is_valid_url(url):
                    output_urls.append(f"Invalid URL")
                    continue
                filename = download_and_process_image(url, serial_number)
                if filename.startswith("Error"):
                    output_urls.append(filename)
                else:
                    output_urls.append(f"{host_url}processed_images/{filename}")

            # Store in DB
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO products (id, serial_number, product_name, input_image_urls, output_image_urls, status) VALUES (?, ?, ?, ?, ?, ?)',
                           (str(uuid.uuid4()), serial_number, product_name, ','.join(input_urls), ','.join(output_urls), 'Processed'))
            conn.commit()
            conn.close()

            results.append({
                "Serial Number": serial_number,
                "Product Name": product_name,
                "Input Image Urls": ','.join(input_urls),
                "Output Image Urls": ','.join(output_urls)
            })

        save_output_csv(results)
        update_request(request_id, "Completed", f"CSV processed successfully, total rows: {total_rows}", total_rows)

        # Trigger webhook if needed
        try:
            webhook_url = request.args.get('webhook_url')
            if webhook_url:
                requests.post(webhook_url, json={"request_id": request_id, "status": "Completed", "total_rows": total_rows})
        except:
            pass

    except Exception as e:
        update_request(request_id, "Failed", f"Error processing CSV: {str(e)}", 0)


# Flask Routes
@app.route('/')
def home():
    return "CSV Image Processing API Running!"

@app.route('/upload_csv', methods=['POST'])
def upload_csv_api():
    if 'file' not in request.files:
        return jsonify({"error": "No CSV file uploaded"}), 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be CSV"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    request_id = str(uuid.uuid4())
    insert_request(request_id)

    host_url = request.host_url
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(process_csv, file_path, request_id, host_url)

    return jsonify({"message": "CSV received. Processing started.", "request_id": request_id}), 202

@app.route('/request_status/<request_id>', methods=['GET'])
def request_status(request_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT status, message, total_rows FROM requests WHERE request_id=?', (request_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        status, message, total_rows = row
        return jsonify({"request_id": request_id, "status": status, "message": message, "total_rows": total_rows})
    else:
        return jsonify({"error": "Request ID not found"}), 404


# Serve processed images
@app.route('/processed_images/<filename>')
def serve_image(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)


# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Webhook triggered:", data)
    return jsonify({"message": "Webhook received", "data": data}), 200

if __name__ == '__main__':
    app.run(debug=True)
