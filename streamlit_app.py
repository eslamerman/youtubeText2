import streamlit as st
import boto3
import yt_dlp
import os
from datetime import datetime
import uuid

class YouTubeProcessor:
    def __init__(self):
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id = st.secrets["aws"]["aws_access_key_id"],
            aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"]
        )
        self.bucket_name = 'erman-demo-1'
        
    def download_youtube_video(self, url, output_path):
    """Download YouTube video as MP3"""
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio stream
        'outtmpl': output_path,      # Specify output path
        'postprocessors': [{
            'key': 'FFmpegAudioConvertor',
            'preferredformat': 'mp3',  # Convert audio to MP3
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info = ydl.extract_info(url, download=False)
        return info['title']


    def convert_to_audio(self, video_path, audio_path):
        """Convert video to audio using yt-dlp"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"file://{video_path}"])

    def upload_to_s3(self, file_path, s3_key):
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            return f"s3://{self.bucket_name}/{s3_key}"
        except Exception as e:
            st.error(f"Error uploading to S3: {str(e)}")
            return None

def main():
    st.title("YouTube Video Processor")
    st.write("Enter a YouTube URL to download, upload to S3, and convert to audio")

    # Initialize processor
    processor = YouTubeProcessor()

    # Get YouTube URL from user
    youtube_url = st.text_input("Enter YouTube URL:")

    if st.button("Process Video"):
        if youtube_url:
            try:
                with st.spinner("Processing..."):
                    # Create temporary file paths
                    temp_dir = "temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate unique identifiers for files
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())[:8]
                    
                    video_filename = f"video_{timestamp}_{unique_id}.mp4"
                    audio_filename = f"audio_{timestamp}_{unique_id}.mp3"
                    
                    video_path = os.path.join(temp_dir, video_filename)
                    audio_path = os.path.join(temp_dir, audio_filename)

                    # Step 1: Download YouTube video
                    st.write("Downloading video...")
                    video_title = processor.download_youtube_video(youtube_url, video_path)
                    st.success("Video downloaded successfully!")

                    # Step 2: Upload video to S3
                    st.write("Uploading video to S3...")
                    s3_video_key = f"videos/{video_filename}"
                    s3_video_url = processor.upload_to_s3(video_path, s3_video_key)
                    if s3_video_url:
                        st.success("Video uploaded to S3!")
                        st.write(f"S3 Video URL: {s3_video_url}")

                    # Step 3: Convert to audio
                    st.write("Converting to audio...")
                    processor.convert_to_audio(video_path, audio_path)
                    
                    # Step 4: Upload audio to S3
                    s3_audio_key = f"audio/{audio_filename}"
                    s3_audio_url = processor.upload_to_s3(audio_path, s3_audio_key)
                    if s3_audio_url:
                        st.success("Audio uploaded to S3!")
                        st.write(f"S3 Audio URL: {s3_audio_url}")

                    # Clean up temporary files
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a YouTube URL")

if __name__ == "__main__":
    main()
