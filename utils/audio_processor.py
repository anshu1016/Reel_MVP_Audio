import os
import requests
from pydub import AudioSegment
import tempfile
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')
SARVAM_API_ENDPOINT = 'https://api.sarvam.ai/speech-to-text'
CHUNK_DURATION = 30 * 1000  # 30 seconds in milliseconds
print(SARVAM_API_KEY)
def split_audio(audio_path):
    """Split audio file into 30-second chunks."""
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    
    for i in range(0, len(audio), CHUNK_DURATION):
        chunk = audio[i:i + CHUNK_DURATION]
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            chunk.export(temp_file.name, format='wav')
            chunks.append(temp_file.name)
    
    return chunks

def transcribe_chunk(chunk_path, language):
    """Transcribe a single audio chunk using Sarvam AI API."""
    headers = {
        'api-subscription-key': SARVAM_API_KEY,
        'Content-Type': 'multipart/form-data'
    }

    try:
        with open(chunk_path, 'rb') as audio_file:
            # Note: API expects 'file' not 'audio_file'
            files = {
                'file': ('audio.wav', audio_file, 'audio/wav')
            }
            
            # Optional parameters
            data = {}
            if language != 'unknown':
                data['language_code'] = language
            data['model'] = 'saarika:v2'  # Optional, this is default anyway

            print("=== Debug Information ===")
            print(f"API Endpoint: {SARVAM_API_ENDPOINT}")
            print(f"Headers: {headers}")
            print(f"Data parameters: {data}")
            print(f"File being sent: {chunk_path}")
            
            response = requests.post(
                SARVAM_API_ENDPOINT,
                headers=headers,
                files=files,
                data=data
            )

            print(f"Response Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")
            print("=====================")

            if response.status_code != 200:
                error_detail = f"API request failed: {response.text}"
                raise Exception(error_detail)

            # API returns 'transcript' field in response
            return response.json().get('transcript', '')

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        raise

def process_audio_file(audio_path, language):
    """Process audio file and return complete transcript."""
    try:
        # Get audio file information
        audio = AudioSegment.from_wav(audio_path)
        print("\n=== Audio File Information ===")
        print(f"Duration: {len(audio)/1000:.2f} seconds")
        print(f"Channels: {audio.channels}")
        print(f"Sample Width: {audio.sample_width * 8} bits")
        print(f"Frame Rate: {audio.frame_rate} Hz")
        print("===========================\n")
        
        duration_ms = len(audio)
        
        if duration_ms <= CHUNK_DURATION:
            # If audio is shorter than 30 seconds, process it directly
            transcript = transcribe_chunk(audio_path, language)
        else:
            # Split audio into chunks and process each chunk
            chunks = split_audio(audio_path)
            transcripts = []
            
            for chunk_path in chunks:
                try:
                    chunk_transcript = transcribe_chunk(chunk_path, language)
                    transcripts.append(chunk_transcript)
                finally:
                    # Clean up temporary chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
            
            transcript = ' '.join(transcripts)
        
        return transcript
        
    except Exception as e:
        raise Exception(f"Error processing audio file: {str(e)}") 