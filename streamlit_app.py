import streamlit as st
import yt_dlp
import os
import boto3
import tempfile

# Function to initialize S3 client
def initialize_s3():
    return boto3.client(
        's3',
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"]
    )

# Function to download YouTube audio
def download_youtube_audio(url, output_path):
    """Download YouTube video audio as MP3"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            audio_filename = ydl.prepare_filename(info)
            audio_filename = os.path.splitext(audio_filename)[0] + '.mp3'
            return info.get('title', 'Unknown Title'), audio_filename
        except Exception as e:
            raise Exception(f"Error downloading audio: {str(e)}")

# Function to upload to S3
def upload_to_s3(file_path, bucket_name, s3_key):
    """Upload file to S3"""
    s3 = initialize_s3()
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        raise Exception(f"Error uploading to S3: {str(e)}")

# Streamlit App
def main():
    st.title("YouTube Audio Downloader and S3 Uploader")
    st.write("Enter a YouTube URL to download the audio and upload it to an S3 bucket.")

    # Input YouTube URL
    youtube_url = st.text_input("YouTube URL:")
    bucket_name = st.text_input("S3 Bucket Name:", value="erman-demo-1")

    if st.button("Download and Upload"):
        if youtube_url and bucket_name:
            try:
                with st.spinner("Processing..."):
                    # Create a temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Step 1: Download the YouTube audio
                        title, audio_path = download_youtube_audio(youtube_url, temp_dir)
                        st.success(f"Downloaded audio: {title}")

                        # Step 2: Upload to S3
                        s3_audio_key = f"audio/{title}.mp3"
                        s3_url = upload_to_s3(audio_path, bucket_name, s3_audio_key)
                        st.success("Uploaded to S3 successfully!")
                        st.write(f"S3 URL: {s3_url}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter both a YouTube URL and an S3 bucket name.")

if __name__ == "__main__":
    main()
