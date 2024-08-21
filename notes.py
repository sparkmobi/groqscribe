"""
notes.py

This file contains the functions for the notes section of the app.

Modules:
- streamlit: A Python library for building interactive apps.
- io: A built-in module for working with input/output operations.
- md2pdf: A Python library for converting Markdown to PDF.

Classes:
- GenerationStatistics: A class to represent and calculate statistics for generation tasks.
- NoteSection: A class to represent and manage the notes section of the app.

Functions:
- create_markdown_file():
- create_pdf_file():
- transcribe_audio():
- generate_notes_structure():
- generate_section():
- generate_transcript_structure():
"""

import streamlit as st
from io import BytesIO
from md2pdf.core import md2pdf
from google.generativeai.types import HarmCategory, HarmBlockThreshold

CUSTOM_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
    HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
    HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
}


class GenerationStatistics:
    """
    A class to represent and calculate statistics for generation tasks.

    Attributes:
        input_time (float): The time taken to process the input text.
        output_time (float): The time taken to process the output text.
        input_tokens (int): The number of input tokens.
        output_tokens (int): The number of output tokens.
        total_time (float): The total time taken to process the task.
        model_name (str): The name of the model used for generation.

    Methods:
        get_input_speed(): Calculates and returns the input speed in tokens per second.
        get_output_speed(): Calculates and returns the output speed in tokens per second.
        add(other): Adds the statistics of another instance to this instance.
        __str__(): Returns a string representation of the statistics.
    """

    def __init__(self, input_tokens=0, output_tokens=0, model_name="gemini"):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model_name = model_name

    def add(self, other):
        """
        Add statistics from another GenerationStatistics object to this one.
        """
        if not isinstance(other, GenerationStatistics):
            raise TypeError("Can only add GenerationStatistics objects")
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens

    def __str__(self):
        return (
            f"\n## Model: {self.model_name}\n\n"
            f"| Metric          | Input          | Output          | Total          |\n"
            f"|-----------------|----------------|-----------------|----------------|\n"
            f"| Tokens          | {self.input_tokens}            | {self.output_tokens}            | {self.input_tokens + self.output_tokens}            |\n"
        )


class NoteSection:
    """
    A class to manage and display structured notes with markdown formatting.

    Attributes:
        structure (dict): A nested dictionary representing the notes structure.
        contents (dict): A dictionary to store the contents of each note.
        placeholders (dict): A dictionary to store placeholders for each note.

    Methods:
        flatten_structure(): Flattens the notes structure into a list of section titles.
        update_content(): Updates the content of a given section.
        display_content(): Displays the content of a given section if it is not empty.
        return_existing_contents(): Returns the existing contents as a markdown string.
        display_structure(): Displays the structure and content of the notes.
        display_toc(): Displays the table of contents for the notes.
        get_markdown_content(): Returns the markdown formatted content of the notes.
        get_transcript_markdown_content(): Returns the markdown formatted content of the transcript.
    """

    def __init__(self, structure, transcript):
        self.structure = structure
        self.contents = {
            title: ""
            for title in self.flatten_structure(structure)
        }
        self.placeholders = {
            title: st.empty()
            for title in self.flatten_structure(structure)
        }

    def flatten_structure(self, structure):
        sections = []
        for title, content in structure.items():
            sections.append(title)
            if isinstance(content, dict):
                sections.extend(self.flatten_structure(content))
        return sections

    def update_content(self, title, new_content):
        try:
            self.contents[title] += new_content
            self.display_content(title)
        except TypeError as e:
            pass

    def display_content(self, title):
        if self.contents[title].strip():
            self.placeholders[title].markdown(
                f"## {title}\n{self.contents[title]}")

    def return_existing_contents(self, level=1) -> str:
        existing_content = ""
        for title, content in self.structure.items():
            if self.contents[title].strip(
            ):  # Only include title if there is content
                existing_content += f"{'#' * level} {title}\n{self.contents[title]}.\n\n"
            if isinstance(content, dict):
                existing_content += self.get_markdown_content(
                    content, level + 1)
        return existing_content

    def display_structure(self, structure=None, level=1):
        if structure is None:
            structure = self.structure

        for title, content in structure.items():
            if self.contents[title].strip(
            ):  # Only display title if there is content
                st.markdown(f"{'#' * level} {title}")
                self.placeholders[title].markdown(self.contents[title])
            if isinstance(content, dict):
                self.display_structure(content, level + 1)

    def display_toc(self, structure, columns, level=1, col_index=0):
        for title, content in structure.items():
            with columns[col_index % len(columns)]:
                st.markdown(f"{' ' * (level-1) * 2}- {title}")
            col_index += 1
            if isinstance(content, dict):
                col_index = self.display_toc(content, columns, level + 1,
                                             col_index)
        return col_index

    def get_markdown_content(self, structure=None, level=1):
        """
        Returns the markdown styled pure string with the contents.
        """
        if structure is None:
            structure = self.structure

        markdown_content = ""
        for title, content in structure.items():
            if self.contents[title].strip(
            ):  # Only include title if there is content
                markdown_content += f"{'#' * level} {self.contents[title]}.\n\n"
            if isinstance(content, dict):
                markdown_content += self.get_markdown_content(
                    content, level + 1)
        return markdown_content

    def get_transcript_markdown_content(self, structure=None, level=1):
        """
        Returns the markdown styled pure string with the contents.
        """
        if structure is None:
            structure = self.structure

        markdown_content = ""
        for title, content in structure.items(
        ):  # Iterate directly over the list of titles
            markdown_content += f"{'#' * level} {title}\n{content}.\n\n"

        return markdown_content


def create_markdown_file(content: str) -> BytesIO:
    """
    Create a Markdown file from the provided content.
    """
    markdown_file = BytesIO()
    markdown_file.write(content.encode('utf-8'))
    markdown_file.seek(0)
    return markdown_file


def create_pdf_file(content: str):
    """
    Create a PDF file from the provided content.
    """
    pdf_buffer = BytesIO()
    md2pdf(pdf_buffer, md_content=content)
    pdf_buffer.seek(0)
    return pdf_buffer


def transcribe_audio(audio_file):
    """
    Transcribes audio using Gemini's API.
    """
    ai_audio_file = st.session_state.genai.upload_file(path=audio_file)
    prompt = "Can you transcribe this interview?"

    model = st.session_state.genai.GenerativeModel(
        'models/gemini-1.0-pro',
        generation_config=st.session_state.genai.GenerationConfig(
            temperature=0.1))

    results = model.generate_content([prompt, ai_audio_file],
                                     safety_settings=CUSTOM_SAFETY_SETTINGS)
    if not results.text:
        print(f"Results: {results}")
    return results.text


def generate_notes_structure(transcript: str):
    """
    Returns notes structure content as well as total tokens and total time for generation.
    """

    shot_example = """
"Introduction": "Introduction to the AMA session, including the topic of Groq scaling architecture and the panelists",
"Panelist Introductions": "Brief introductions from Igor, Andrew, and Omar, covering their backgrounds and roles at Groq",
"Groq Scaling Architecture Overview": "High-level overview of Groq's scaling architecture, covering hardware, software, and cloud components",
"Hardware Perspective": "Igor's overview of Groq's hardware approach, using an analogy of city traffic management to explain the traditional compute approach and Groq's innovative approach",
"Traditional Compute": "Description of traditional compute approach, including asynchronous nature, queues, and poor utilization of infrastructure",
"Groq's Approach": "Description of Groq's approach, including pre-orchestrated movement of data, low latency, high energy efficiency, and high utilization of resources",
"Hardware Implementation": "Igor's explanation of the hardware implementation, including a comparison of GPU and LPU architectures"
"""
    model = st.session_state.genai.GenerativeModel(
        'models/gemini-1.5-pro',
        system_instruction=
        "Write in JSON format:\n\n{\"Title of section goes here\":\"Description of section goes here\",\"Title of section goes here\":\"Description of section goes here\",\"Title of section goes here\":\"Description of section goes here\"}",
        generation_config=st.session_state.genai.GenerationConfig(
            temperature=0.3))

    prompt = f"### Transcript:\n\n{transcript}\n\n### Example:\n\n{shot_example}\n\n### Instructions:\n\nCreate a structure for comprehensive notes on the above transcribed audio. Section titles and content descriptions must be comprehensive. Quality over quantity. Don't include any additional information."

    completion = model.generate_content(prompt,
                                        safety_settings=CUSTOM_SAFETY_SETTINGS)
    usage = completion.usage_metadata
    statistics_to_return = GenerationStatistics(
        input_tokens=usage.prompt_token_count,
        output_tokens=usage.candidates_token_count)

    return statistics_to_return, completion.text


def generate_section(transcript: str, existing_notes: str, section: str):
    """
    Returns notes structure content as well as total tokens and total time for generation.
    """
    model = st.session_state.genai.GenerativeModel(
        'models/gemini-1.5-pro',
        system_instruction=
        "You are an expert writer. Generate a comprehensive note for the section provided based factually on the transcript provided. Do not repeat any content from previous sections. Avoid giving a premise before the section. Don't repeat section titles.",
        generation_config=st.session_state.genai.GenerationConfig(
            temperature=0.3))

    prompt = f"### Transcript:\n\n{transcript}\n\n### Existing Notes:\n\n{existing_notes}\n\n### Instructions:\n\nGenerate comprehensive notes for this section only based on this section of the transcript: \n\n{section}."

    stream = model.generate_content(prompt,
                                    safety_settings=CUSTOM_SAFETY_SETTINGS,
                                    stream=True)

    for chunk in stream:
        tokens = chunk.text
        if tokens:
            yield tokens
        if chunk.usage_metadata:
            usage = chunk.usage_metadata
            statistics_to_return = GenerationStatistics(
                input_tokens=usage.prompt_token_count,
                output_tokens=usage.candidates_token_count)
            yield statistics_to_return


def generate_transcript_structure(transcript: str, sections: list):
    """
    Returns transcript structure content segmented into sections using a model to identify section boundaries.
    """
    structured_transcript = {}

    # Use the model to identify section boundaries in the transcript.
    model = st.session_state.genai.GenerativeModel(
        'models/gemini-1.5-pro',
        system_instruction=
        "You are a transcript editor. Identify the sections in the following transcript, preserving the original text.  Output a JSON object where each key is a section title from the provided list, and the value is the content of that section.",
        generation_config=st.session_state.genai.GenerationConfig(
            temperature=0.3))

    prompt = f"### Transcript\n\n{transcript}\n\n### Sections\n\n{sections}\n\n### Instructions\n\nIdentify the sections in the transcript and insert a separator (---) between them. Preserve the original text and do not add any additional information.  Output the structured transcript as a JSON object with the format:\n\n```json\n{{\n  \"{sections[0]}\": \"Content of section 1\",\n  \"{sections[1]}\": \"Content of section 2\",\n  ...\n}}\n```"

    completion = model.generate_content(prompt,
                                        safety_settings=CUSTOM_SAFETY_SETTINGS)

    # Extract the structured transcript from the model's response.
    structured_transcript = completion.text

    return structured_transcript
