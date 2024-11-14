import streamlit as st
import boto3
import yt_dlp
import os
from datetime import datetime
import uuid

class YouTubeAudioProcessor:
    def __init__(self):
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id = st.secrets["aws"]["aws_access_key_id"],
            aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"]
        )
        self.bucket_name = 'erman-demo-1'

    def download_and_convert_to_audio(self, url, output_path):
        """Download YouTube video and convert directly to audio"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path,
            'progress_hooks': [self._progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                return info.get('title', 'Unknown Title')
            except Exception as e:
                raise Exception(f"Error downloading audio: {str(e)}")

    def _progress_hook(self, d):
        """Hook to track download progress"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                progress = (downloaded_bytes / total_bytes) * 100
                st.session_state.progress = progress
        elif d['status'] == 'finished':
            st.session_state.progress = 100

    def upload_to_s3(self, file_path, s3_key):
        """Upload file to S3"""
        try:
            # Create progress bar for upload
            with st.progress(0) as progress_bar:
                def callback(bytes_transferred):
                    file_size = os.path.getsize(file_path)
                    progress = (bytes_transferred / file_size) * 100
                    progress_bar.progress(int(progress))

                self.s3_client.upload_file(
                    file_path, 
                    self.bucket_name, 
                    s3_key,
                    Callback=callback
                )
            return f"s3://{self.bucket_name}/{s3_key}"
        except Exception as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

def main():
    st.title("YouTube to Audio Converter")
    st.write("Enter a YouTube URL to convert to audio and upload to S3")

    # Initialize processor
    processor = YouTubeAudioProcessor()

    # Initialize progress in session state
    if 'progress' not in st.session_state:
        st.session_state.progress = 0

    # Get YouTube URL from user
    youtube_url = st.text_input("Enter YouTube URL:")

    # Add audio quality selection
    audio_quality = st.select_slider(
        "Select Audio Quality (kbps)",
        options=['64', '128', '192', '256', '320'],
        value='192'
    )

    if st.button("Convert and Upload"):
        if youtube_url:
            try:
                with st.spinner("Processing..."):
                    # Create temporary directory
                    temp_dir = "temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())[:8]
                    audio_filename = f"audio_{timestamp}_{unique_id}.mp3"
                    audio_path = os.path.join(temp_dir, audio_filename)

                    # Progress bar for download and conversion
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Step 1: Download and convert to audio
                    status_text.text("Downloading and converting to audio...")
                    video_title = processor.download_and_convert_to_audio(youtube_url, audio_path)
                    
                    # Update progress based on session state
                    progress_bar.progress(st.session_state.progress)
                    
                    # Step 2: Upload to S3
                    status_text.text("Uploading to S3...")
                    s3_audio_key = f"audio/{video_title}_{unique_id}.mp3"
                    s3_url = processor.upload_to_s3(audio_path, s3_audio_key)

                    # Success message
                    st.success("Audio processed and uploaded successfully!")
                    st.write(f"Title: {video_title}")
                    st.write(f"S3 URL: {s3_url}")

                    # Clean up
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Reset progress
                st.session_state.progress = 0
        else:
            st.warning("Please enter a YouTube URL")

if __name__ == "__main__":
    main()
