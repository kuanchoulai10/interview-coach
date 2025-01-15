import os
import re
from tempfile import NamedTemporaryFile
from typing import Optional

import openai
import streamlit as st
# from dotenv import load_dotenv
from pydantic import BaseModel
from pydub import AudioSegment

from prompts import prompt, prompt2, prompt3


class Suggestion(BaseModel):
    original: str
    revised: str
    explanation: str

class ResponseModel(BaseModel):
    suggestions: list[Suggestion]
    revised_response: str

# Load environment variables
# load_dotenv()

# Configure OpenAI
# openai.api_key = os.getenv('OPENAI_API_KEY')

def get_transcription(audio):
    try:
        with NamedTemporaryFile(suffix='.mp3') as temp:
            AudioSegment.from_file(audio).export(temp.name, format='mp3')
            with open(temp.name, "rb") as mp3:
                transcription = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=mp3
                )
        return transcription.text
    except Exception as e:
        return f"Error: {str(e)}"

def get_revised_response(question: str, response: str):
    try:
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": f"""Question: {question} \nOriginal Response: {response}"""
                }
            ],
            temperature=0.7,
            response_format=ResponseModel
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        return f"Error: {str(e)}"

class ImprovedResponseModel(BaseModel):
    improved_response: str

def get_improved_response(question: str, response: str):
    try:
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt2
                },
                {
                    "role": "user",
                    "content": f"""Question: {question} \nResponse: {response}"""
                }
            ],
            temperature=0.7,
            response_format=ImprovedResponseModel
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        return f"Error: {str(e)}"

def format_string_to_slug(input_string):
    """
    Converts a string into a slug by:
    1. Lowercasing all characters.
    2. Removing punctuation.
    3. Replacing spaces with hyphens.

    Args:
        input_string (str): The input string to format.

    Returns:
        str: The formatted slug string.
    """
    # Convert to lowercase
    lowercased = input_string.lower()
    # Remove punctuation
    no_punctuation = re.sub(r'[^\w\s]', '', lowercased)
    # Replace spaces with hyphens
    slug = no_punctuation.replace(' ', '-')
    return slug

@st.fragment
def download_button(*args, **kwargs):
    return st.download_button(*args, **kwargs)


def main():
    st.title("Behavioral Interview Response Enhancer")
    st.write("Improve your behavioral interview responses with AI-powered feedback")
    api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if api_key:
        openai.api_key = api_key
        question = st.text_area("Enter the interview question:", height=100)
        format = st.selectbox(
            "Response Format:",
            ("Audio", "Text", "File")
        )
        if format=="Text":
            response = st.text_area("Enter your response:", height=200)
        elif format=="Audio":
            response = st.audio_input("Record your response:")
        elif format=="File":
            response = st.file_uploader("Upload your wav audio response", type="wav")

        if st.button("Get Feedback"):
            if question and response:
                q_slug = format_string_to_slug(question)
                if format in ("Audio", "File"):
                    with st.spinner("Transcribing your response..."):
                        response = get_transcription(response)
                        st.subheader("Transcription")
                        download_button(
                            "Download transcription",
                            response,
                            file_name=f"{q_slug}-transcription.md",
                            mime="text/plain"
                        )
                        st.write(response)

                with st.spinner("Analyzing your response..."):
                    r = get_revised_response(question, response)
                    st.subheader("💡 Suggestions")
                    for s in r.suggestions:
                        st.write(s)
                    st.subheader("💡 Revised Response")
                    download_button(
                        "Download revised response",
                        r.revised_response,
                        file_name=f"{q_slug}-revised.md",
                        mime="text/plain"
                    )
                    st.write(r.revised_response)

                with st.spinner("Improving your response..."):
                    r = get_improved_response(question, r.revised_response)
                    st.subheader("💡 Improved Response")
                    download_button(
                        "Download improved response",
                        r.improved_response,
                        file_name=f"{q_slug}-improved.md",
                        mime="text/plain"
                    )
                    st.write(r.improved_response)
            else:
                st.warning("Please provide both the question and your response.")
    else:
        st.warning("Please enter your OpenAI API key to continue.")


if __name__ == "__main__":
    main()