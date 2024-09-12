from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import requests
import yagmail
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from gtts import gTTS
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import cv2
import os

app = Flask(__name__)

# ------------------- ROUTES -------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/projects')
def projects():
    return render_template('project.html')


@app.route('/projects/menu_project')
def menu_project():
    return render_template('projects/menu_project.html')


# ------------------- GEOLOCATION API -------------------

def get_location():
    """
    Fetches geographical location of the current IP address using ipinfo.io API.
    """
    try:
        response = requests.get('https://ipinfo.io/json')
        response.raise_for_status()
        data = response.json()

        location = data.get('loc').split(',')
        return {
            'ip_address': data.get('ip'),
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country'),
            'latitude': location[0],
            'longitude': location[1]
        }
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}


@app.route('/location', methods=['GET'])
def location():
    return jsonify(get_location())


# ------------------- EMAIL FUNCTIONALITY -------------------

def send_email(subject, body, to_email, from_email="priyankapoonia803@gmail.com", app_password=os.enviro.get('SMTP_PASSWORD')):
    try:
        yag = yagmail.SMTP(from_email, app_password)
        yag.send(to=to_email, subject=subject, contents=body)
        return {"status": "success", "message": "Email sent successfully!"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email: {e}"}


@app.route('/send_email', methods=['POST'])
def send_email_api():
    data = request.json
    subject = data.get('subject')
    body = data.get('body')
    to_email = data.get('to_email')
    from_email = data.get('from_email', "priyankapoonia803@gmail.com")
    app_password = data.get('app_password', os.enviro.get('SMTP_PASSWORD'))

    return jsonify(send_email(subject, body, to_email, from_email, app_password))


def send_bulk_email(sender_email, sender_password, subject, message, recipients):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
            smtp.login(sender_email, sender_password)

            for recipient in recipients:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                smtp.send_message(msg)

        return {"status": "success", "message": f"Emails sent to {len(recipients)} recipients."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route('/send_bulk_email', methods=['POST'])
def send_bulk_email_api():
    data = request.json
    sender_email = data.get('sender_email')
    sender_password = data.get('sender_password')
    subject = data.get('subject')
    message = data.get('message')
    recipients = data.get('recipients')

    if not all([sender_email, sender_password, subject, message, recipients]):
        return jsonify({"status": "error", "message": "All fields are required."}), 400

    return jsonify(send_bulk_email(sender_email, sender_password, subject, message, recipients))


# ------------------- SYSTEM VOLUME CONTROL -------------------

def get_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume.GetMasterVolumeLevelScalar() * 100


@app.route('/get_volume', methods=['GET'])
def get_volume_api():
    try:
        return jsonify({"status": "success", "current_volume": get_volume()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def set_volume(level):
    if 0.0 <= level <= 100.0:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return {"status": "success", "message": f"Volume set to {level:.2f}%"}
    else:
        return {"status": "error", "message": "Volume level must be between 0.0 and 100.0"}


@app.route('/set_volume', methods=['POST'])
def set_volume_api():
    data = request.json
    level = data.get('level')

    if level is None or not isinstance(level, (int, float)):
        return jsonify({"status": "error", "message": "Please provide a valid volume level between 0 and 100."}), 400

    try:
        return jsonify(set_volume(level))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ------------------- TEXT-TO-SPEECH FUNCTIONALITY -------------------

def text_to_speech(text, lang='hi', filename='voice_note.mp3'):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return filename
    except Exception as e:
        return str(e)


@app.route('/text_to_speech', methods=['POST'])
def text_to_speech_api():
    data = request.json
    text = data.get('text')
    lang = data.get('lang', 'hi')
    filename = data.get('filename', 'voice_note.mp3')

    if not text:
        return jsonify({"status": "error", "message": "Text is required."}), 400

    try:
        saved_filename = text_to_speech(text, lang, filename)
        if saved_filename.endswith('.mp3'):
            return send_file(saved_filename, as_attachment=True)
        else:
            return jsonify({"status": "error", "message": saved_filename}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------- DATA PROCESSING AND ANALYSIS -------------------

def load_data(file_path):
    return pd.read_csv(file_path)


def clean_data(df):
    df = df.drop_duplicates()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns

    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    for col in non_numeric_cols:
        df[col] = df[col].fillna(df[col].mode()[0])

    return df


def analyze_data(df):
    analysis = {'summary_statistics': df.describe(include='all').to_dict()}
    if not df.select_dtypes(include=[np.number]).empty:
        analysis['correlation_matrix'] = df.corr().to_dict()
    return analysis


def visualize_data(df):
    buffer = io.BytesIO()
    df.hist(figsize=(10, 8))
    plt.suptitle('Histograms of Numeric Columns')
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    return buffer


@app.route('/process', methods=['POST'])
def process_data():
    try:
        file = request.files['file']
        file_path = f"/tmp/{file.filename}"
        file.save(file_path)

        df = load_data(file_path)
        df = clean_data(df)
        analysis = analyze_data(df)
        buffer = visualize_data(df)

        return jsonify({
            'summary_statistics': analysis['summary_statistics'],
            'correlation_matrix': analysis.get('correlation_matrix', {})
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/download-plot', methods=['GET'])
def download_plot():
    try:
        buffer = io.BytesIO()
        df = pd.read_csv('/tmp/data.csv')  # Replace with actual path where data is saved
        buffer = visualize_data(df)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, attachment_filename='plot.png', mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ------------------- IMAGE FILTERS -------------------

def apply_filters(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    blur = cv2.GaussianBlur(image, (15, 15), 0)
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(image, 100, 200)

    return blur, grayscale, edges


@app.route('/image_filter', methods=['POST'])
def image_filter():
    try:
        file = request.files['file']
        file_path = f"/tmp/{file.filename}"
        file.save(file_path)

        filters = apply_filters(file_path)
        if not filters:
            return jsonify({'error': 'Invalid image format.'}), 400

        response_data = []
        for i, filter_image in enumerate(filters):
            buffer = io.BytesIO()
            _, img_encoded = cv2.imencode('.png', filter_image)
            buffer.write(img_encoded.tobytes())
            buffer.seek(0)
            response_data.append(buffer.getvalue())

        return jsonify({'filtered_images': [data for data in response_data]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
