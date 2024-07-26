import streamlit as st
from groq import Groq
import json
import os
from io import BytesIO
from md2pdf.core import md2pdf
from dotenv import load_dotenv
from download import download_video_audio, delete_download
from notes import GenerationStatistics, NoteSection, generate_notes_structure, generate_section, create_markdown_file, create_pdf_file, transcribe_audio

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
FILE_TOO_LARGE_MESSAGE = "The audio file is too large for the current size and rate limits using Whisper. If you used a YouTube link, please try a shorter video clip. If you uploaded an audio file, try trimming or compressing the audio to under 25 MB."

audio_file_path = None

if 'api_key' not in st.session_state:
    st.session_state.api_key = GROQ_API_KEY

if 'groq' not in st.session_state:
    if GROQ_API_KEY:
        st.session_state.groq = Groq()

st.set_page_config(
    page_title="GroqNotes",
    page_icon="🗒️",
)

# Initialize
if 'button_disabled' not in st.session_state:
    st.session_state.button_disabled = False

if 'button_text' not in st.session_state:
    st.session_state.button_text = "Generate Notes"

if 'statistics_text' not in st.session_state:
    st.session_state.statistics_text = ""

if 'notes_title' not in st.session_state:
    st.session_state.notes_title = "generate"

st.write("""
# GroqNotes: Create structured notes from audio 🗒️⚡
""")


def disable():
    st.session_state.button_disabled = True


def enable():
    st.session_state.button_disabled = False


def empty_st():
    st.empty()


try:
    with st.sidebar:
        audio_files = {
            "Transformers Explained by Google Cloud Tech": {
                "file_path": "assets/audio/transformers_explained.m4a",
                "youtube_link": "https://www.youtube.com/watch?v=SZorAJ4I-sA"
            },
            "The Essence of Calculus by 3Blue1Brown": {
                "file_path": "assets/audio/essence_calculus.m4a",
                "youtube_link": "https://www.youtube.com/watch?v=WUvTyaaNkzM"
            },
            "First 20 minutes of Groq's AMA": {
                "file_path": "assets/audio/groq_ama_trimmed_20min.m4a",
                "youtube_link": "https://www.youtube.com/watch?v=UztfweS-7MU"
            }
        }

        st.write(
            f"# 🗒️ GroqTranscribe \n## Generate notes from audio in seconds using Groq"
        )
        # st.markdown(
        #     f"[Github Repository](https://github.com/bklieger/groqnotes)\n\nAs with all generative AI, content may include inaccurate or placeholder information. GroqNotes is in beta and all feedback is welcome!"
        # )

        st.write(f"---")

        st.write(f"# Sample Audio Files")

        for audio_name, audio_info in audio_files.items():

            st.write(f"### {audio_name}")

            # Read audio file as binary
            with open(audio_info['file_path'], 'rb') as audio_file:
                audio_bytes = audio_file.read()

            # Create download button
            st.download_button(label=f"Download audio",
                               data=audio_bytes,
                               file_name=audio_info['file_path'],
                               mime='audio/m4a')

            st.markdown(f"[Credit Youtube Link]({audio_info['youtube_link']})")
            st.write(f"\n\n")

        st.write(f"---")

        st.write(
            "# Customization Settings\n🧪 These settings are experimental.\n")
        st.write(
            f"By default, GroqNotes uses Llama3-70b for generating the notes outline and Llama3-8b for the content. This balances quality with speed and rate limit usage. You can customize these selections below."
        )
        outline_model_options = [
            "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        outline_selected_model = st.selectbox("Outline generation:",
                                              outline_model_options)
        content_model_options = [
            "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768",
            "gemma-7b-it", "gemma2-9b-it"
        ]
        content_selected_model = st.selectbox("Content generation:",
                                              content_model_options)

        # Add note about rate limits
        st.info(
            "Important: Different models have different token and rate limits which may cause runtime errors."
        )

    if st.button('End Generation and Download Notes'):
        if "notes" in st.session_state:

            # Create markdown file
            markdown_file = create_markdown_file(
                st.session_state.notes.get_markdown_content())
            st.download_button(
                label='Download Text',
                data=markdown_file,
                file_name=f'{st.session_state.notes_title}_notes.txt',
                mime='text/plain')

            # Create pdf file (styled)
            pdf_file = create_pdf_file(
                st.session_state.notes.get_markdown_content())
            st.download_button(
                label='Download PDF',
                data=pdf_file,
                file_name=f'{st.session_state.notes_title}_notes.pdf',
                mime='application/pdf')
            st.session_state.button_disabled = False
        else:
            raise ValueError(
                "Please generate content first before downloading the notes.")

    input_method = st.radio("Choose input method:",
                            ["Upload audio file", "YouTube link"])

    audio_file = None
    youtube_link = None
    groq_input_key = None
    with st.form("groqform"):
        if not GROQ_API_KEY:
            groq_input_key = st.text_input(
                "Enter your Groq API Key (gsk_yA...):", "", type="password")

        # Add radio button to choose between file upload and YouTube link

        if input_method == "Upload audio file":
            audio_file = st.file_uploader("Upload an audio file",
                                          type=["mp3", "wav",
                                                "m4a"])  # TODO: Add a max size
        else:
            youtube_link = st.text_input("Enter YouTube link:", "")

        # Generate button
        submitted = st.form_submit_button(
            st.session_state.button_text,
            on_click=disable,
            disabled=st.session_state.button_disabled)

        #processing status
        status_text = st.empty()

        def display_status(text):
            status_text.write(text)

        def clear_status():
            status_text.empty()

        download_status_text = st.empty()

        def display_download_status(text: str):
            download_status_text.write(text)

        def clear_download_status():
            download_status_text.empty()

        # Statistics
        placeholder = st.empty()

        def display_statistics():
            with placeholder.container():
                if st.session_state.statistics_text:
                    if "Transcribing audio in background" not in st.session_state.statistics_text:
                        st.markdown(st.session_state.statistics_text +
                                    "\n\n---\n"
                                    )  # Format with line if showing statistics
                    else:
                        st.markdown(st.session_state.statistics_text)
                else:
                    placeholder.empty()

        if submitted:
            if input_method == "Upload audio file" and audio_file is None:
                st.error("Please upload an audio file")
            elif input_method == "YouTube link" and not youtube_link:
                st.error("Please enter a YouTube link")
            else:
                st.session_state.button_disabled = True
                # Show temporary message before transcription is generated and statistics show

            audio_file_path = None

            if input_method == "YouTube link":
                display_status("Downloading audio from YouTube link ....")
                audio_file_path, audio_title = download_video_audio(
                    youtube_link, display_download_status)
                if audio_file_path is None:
                    st.error(
                        "Failed to download audio from YouTube link. Please try again."
                    )
                    enable()
                    clear_status()
                else:
                    # Read the downloaded file and create a file-like objec
                    display_status("Processing Youtube audio ....")
                    with open(audio_file_path, 'rb') as f:
                        file_contents = f.read()
                    audio_file = BytesIO(file_contents)

                    # Check size first to ensure will work with Whisper
                    if os.path.getsize(audio_file_path) > MAX_FILE_SIZE:
                        raise ValueError(FILE_TOO_LARGE_MESSAGE)

                    audio_file.name = os.path.basename(
                        audio_file_path)  # Set the file name
                    st.session_state.notes_title = str(audio_title)
                    delete_download(audio_file_path)
                clear_download_status()

            if not GROQ_API_KEY:
                st.session_state.groq = Groq(api_key=groq_input_key)

            display_status("Transcribing audio in background....")
            transcription_text = transcribe_audio(audio_file)

            display_statistics()

            display_status("Generating notes structure....")
            large_model_generation_statistics, notes_structure = generate_notes_structure(
                transcription_text, model=str(outline_selected_model))
            print("Structure: ", notes_structure)

            display_status("Generating notes ...")
            total_generation_statistics = GenerationStatistics(
                model_name=str(content_selected_model))
            clear_status()

            try:
                notes_structure_json = json.loads(notes_structure)
                notes = NoteSection(structure=notes_structure_json,
                                    transcript=transcription_text)

                if 'notes' not in st.session_state:
                    st.session_state.notes = notes

                st.session_state.notes.display_structure()

                def stream_section_content(sections):
                    for title, content in sections.items():
                        if isinstance(content, str):
                            content_stream = generate_section(
                                transcript=transcription_text,
                                existing_notes=notes.return_existing_contents(
                                ),
                                section=(title + ": " + content),
                                model=str(content_selected_model))
                            for chunk in content_stream:
                                # Check if GenerationStatistics data is returned instead of str tokens
                                chunk_data = chunk
                                if type(chunk_data) == GenerationStatistics:
                                    total_generation_statistics.add(chunk_data)

                                    st.session_state.statistics_text = str(
                                        total_generation_statistics)
                                    display_statistics()
                                elif chunk is not None:
                                    st.session_state.notes.update_content(
                                        title, chunk)
                        elif isinstance(content, dict):
                            stream_section_content(content)

                stream_section_content(notes_structure_json)
            except json.JSONDecodeError:
                st.error(
                    "Failed to decode the notes structure. Please try again.")

            enable()

except Exception as e:
    st.session_state.button_disabled = False

    if hasattr(e, 'status_code') and e.status_code == 413:
        # In the future, this limitation will be fixed as GroqNotes will automatically split the audio file and transcribe each part.
        st.error(FILE_TOO_LARGE_MESSAGE)
    else:
        st.error(e)

    if st.button("Clear"):
        st.rerun()

    # Remove audio after exception to prevent data storage leak
    if audio_file_path is not None:
        delete_download(audio_file_path)
