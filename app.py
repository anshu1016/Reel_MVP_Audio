import os
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from utils.audio_processor import process_audio_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
print("Pushing to github    ")
# Configuration
UPLOAD_FOLDER = 'uploads'
TRANSCRIPTS_FOLDER = 'transcripts'
ALLOWED_EXTENSIONS = {'wav'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        language = request.form.get('language', 'en-IN')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Only WAV files are allowed'}), 400

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{secure_filename(file.filename)}"
        
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Process audio and get transcript
        transcript = process_audio_file(filepath, language)
        
        # Save transcript
        transcript_filename = f"{filename.rsplit('.', 1)[0]}.txt"
        transcript_path = os.path.join(TRANSCRIPTS_FOLDER, transcript_filename)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'transcript_filename': transcript_filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_transcript(filename):
    try:
        return send_file(
            os.path.join(TRANSCRIPTS_FOLDER, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404
        
@app.route('/transcripts', methods=['GET'])
def list_transcripts():
    files = []
    for filename in os.listdir(TRANSCRIPTS_FOLDER):
        if filename.endswith('.txt'):
            files.append(filename)
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True) 