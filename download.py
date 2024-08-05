from __future__ import unicode_literals
import yt_dlp as youtube_dl
import streamlit as st
import os
import time
import re
import shutil
import subprocess
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
FILE_TOO_LARGE_MESSAGE = "The audio file is too large for the current size and rate limits using Whisper. If you used a YouTube link, please try a shorter video clip. If you uploaded an audio file, try trimming or compressing the audio to under 25 MB."
max_retries = 3
delay = 2


class MyLogger(object):

    def __init__(self, external_logger=lambda x: None):
        self.external_logger = external_logger

    def debug(self, msg):
        print("[debug]: ", msg)
        self.external_logger(msg)

    def warning(self, msg):
        print("[warning]: ", msg)

    def error(self, msg):
        print("[error]: ", msg)


# def preprocess_audio(input_file):
#     """
#     """
#     with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
#         output_file = temp_file.name

#     ffmpeg_cmd = [
#         'ffmpeg', '-i', input_file, '-vn', '-map_metadata', '-1', '-ac', '1',
#         '-c:a', 'libopus', '-b:a', '12k', '-application', 'voip', output_file
#     ]

#     try:
#         subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
#         return output_file
#     except subprocess.CalledProcessError as e:
#         st.error(f"Error preprocessing audo: {e.stderr.decode('utf-8')}")
#         return None


def move_to_new_path(input_file):
    # Define the new directory and file name
    new_directory = "./downloads/audio/"
    print(f"This is the basename: {os.path.basename(input_file)}")
    new_file_path = os.path.join(new_directory, os.path.basename(input_file))

    # Ensure the new directory exists
    os.makedirs(new_directory, exist_ok=True)

    # Move the temporary file to the new directory
    shutil.move(input_file, new_file_path)
    return new_file_path


def preprocess_audio(input_file):

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
        output_file = move_to_new_path(temp_file.name)

    ffmpeg_command = [
        'ffmpeg', '-i', input_file, '-vn', '-map_metadata', '-1', '-ac', '1',
        '-c:a', 'libopus', '-b:a', '128k', '-application', 'voip', '-y',
        output_file
    ]

    try:
        process = subprocess.Popen(ffmpeg_command,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

        # for output in process.stderr:
        #     print(output.strip())

        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode,
                                                ffmpeg_command)

        stderr_output = process.stderr.read()
        lines = stderr_output.splitlines()

        for line in lines:
            print(line)

        print("Preprocessing complete!")
        time.sleep(0.5)  # Give user a moment to see 100%
        # os.remove(input_file)
        # output_file = "./downloads/audio/" + output_file
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error preprocessing audio: {e}")
        return None


def my_hook(d):
    print("hook", d["status"])
    if d["status"] == "finished":
        print("Done downloading, now converting ...")


def get_ydl_opts(external_logger=lambda x: None):
    return {
        "format":
        "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",  # set the preferred bitrate to 192kbps
        }],
        "logger":
        MyLogger(external_logger),
        "outtmpl":
        "./downloads/audio/%(title)s.%(ext)s",  # Set the output filename directly
        "progress_hooks": [my_hook],
    }


def handle_large_file(filesize, MAX_FILE_SIZE, ydl, info):
    input_file = ydl.prepare_filename(info)
    input_file_name = os.path.splitext(input_file)[0] + '.mp3'
    filename = preprocess_audio(input_file_name)
    return filename
    # if 'large_file_handled' not in st.session_state:
    #     st.session_state.large_file_handled = False

    # if 'proceed' not in st.session_state:
    #     st.session_state.proceed = False

    # if not st.session_state.large_file_handled:
    #     st.warning(
    #         "File size is {:.2f} MB which exceeds the maximum allowed size of {:.2f} MB. Processing will take longer. Proceed?"
    #         .format(filesize / (1024 * 1024), MAX_FILE_SIZE / (1024 * 1024)))
    #     proceed = st.radio("Do you want to proceed?", ('Yes', 'No'))
    #     if proceed == 'Yes':
    #         # if st.button("Proceed", key="proceed_button"):
    #         st.session_state.large_file_handled = True
    #         st.session_state.proceed = True
    #     elif proceed == 'No':
    #         # if st.button("Cancel", key="cancel_button"):
    #         st.session_state.large_file_handled = True
    #         st.session_state.proceed = False
    #     else:
    #         st.stop()

    # if st.session_state.large_file_handled:
    #     if st.session_state.proceed:
    #         input_file = ydl.prepare_filename(info)
    #         input_file_name = os.path.splitext(input_file)[0] + '.mp3'
    #         filename = preprocess_audio(input_file_name)
    #         return filename
    #     else:
    #         st.info("Operation cancelled by user.")
    #         st.stop()


def download_video_audio(url, external_logger=lambda x: None):
    retries = 0
    # while retries < max_retries:
    try:
        ydl_opts = get_ydl_opts(external_logger)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Going to download ", url)
            info = ydl.extract_info(url, download=False)
            filesize = info.get("filesize", 0)
            filename = ydl.prepare_filename(info)
            res = ydl.download([url])
            logger.info(f"youtube-dl result :{res}")
            filetitle = info.get('title',
                                 'Video with ID: ' + info.get('id', 'unknown'))
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
            mp3_filetitle = re.sub(r'[\\/:*?"<>|]', '', filetitle)
            if filesize > MAX_FILE_SIZE:
                mp3_filename = handle_large_file(filesize, MAX_FILE_SIZE, ydl,
                                                 info)
            print('File name - ', mp3_filename)
            return mp3_filename, mp3_filetitle
    except Exception as e:
        retries += 1
        print(
            f"An error occurred during downloading (Attempt {retries}/{max_retries}):",
            str(e),
        )
        if retries >= max_retries:
            raise e
        time.sleep(delay)


def delete_download(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"File {path} has been deleted.")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Directory {path} and its contents have been deleted.")
        else:
            print(f"The path {path} is neither a file nor a directory.")
    except PermissionError:
        print(f"Permission denied: Unable to delete {path}.")
    except FileNotFoundError:
        print(f"File or directory not found: {path}")
    except Exception as e:
        print(f"An error occurred while trying to delete {path}: {str(e)}")
