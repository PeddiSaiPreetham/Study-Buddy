import os
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv
from pytube import YouTube
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def explain_topic(topic):
    prompt = f"""
I want to study '{topic}'. Please explain this topic clearly as if I am a student.

Instructions:
- Use Markdown formatting
- Include **headings**, **bullet points**, and **examples**
- Keep it concise but deep
- Add **tips to remember** at the end
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def generate_flashcards(topic):
    prompt = f"""
Create 5 flashcards in Q&A format for the topic **'{topic}'**.
Return the flashcards using:
- Markdown formatting
- Numbered list
- Bold questions
- Regular answers
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def follow_up_questions(topic):
    prompt = f"""
List 5 thoughtful follow-up questions for a student after learning about **'{topic}'**.
Use Markdown bullet points.
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def summarize_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages[:5]:
            text += page.extract_text() or ""

        if not text.strip():
            return "❌ Could not extract text from the PDF."

        prompt = f"""
Summarize the following academic PDF content in Markdown format:
- Provide bullet-point summary
- Organize into sections
- Emphasize key concepts

Content:\n\n{text[:5000]}
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error reading PDF: {e}"


def get_video_id(url):
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
    except Exception:
        return None

def summarize_youtube(url):
    try:
        video_id = get_video_id(url)
        if not video_id:
            return "❌ Invalid YouTube URL."

        # Fetch English transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_transcript(['en'])  # Try manual transcript first
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(['en']).fetch()  # Try auto-generated

        transcript_text = " ".join([t['text'] for t in transcript.fetch()])

        if len(transcript_text.strip()) == 0:
            return "❌ Transcript is empty."

        prompt = f"Summarize the key educational points in the following YouTube video transcript:\n\n{transcript_text[:5000]} in markdown format and Organize into sections."
        response = model.generate_content(prompt)
        return response.text

    except TranscriptsDisabled:
        return "❌ Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "❌ No English transcript available for this video."
    except Exception as e:
        return f"❌ Error summarizing video: {e}"


with gr.Blocks() as demo:
    gr.Markdown("# 📘 Study Buddy\nYour smart AI learning assistant!")

    with gr.Tab("📚 Study a Topic"):
        topic_input = gr.Textbox(label="🔍 What do you want to study?", placeholder="Quantum Mechanics, Photosynthesis, Backend Development, Deep Learning")
        with gr.Row():
            explain_btn = gr.Button("📖 Explain")
            flashcard_btn = gr.Button("🧠 Flashcards")
            followup_btn = gr.Button("❓ Follow-up Qs")

        explain_out = gr.Markdown()
        flashcard_out = gr.Markdown()
        followup_out = gr.Markdown()

        def explain_with_status(topic):
            yield "⏳ Generating explanation, please wait..."
            yield explain_topic(topic)
        
        explain_btn.click(fn=explain_with_status, inputs=topic_input, outputs=explain_out)
        def flashcard_with_status(topic):
            yield "⏳ Generating flashcards..."
            yield generate_flashcards(topic)
        
        def followup_with_status(topic):
            yield "⏳ Generating follow-up questions..."
            yield follow_up_questions(topic)
        
        flashcard_btn.click(flashcard_with_status, inputs=topic_input, outputs=flashcard_out)
        followup_btn.click(followup_with_status, inputs=topic_input, outputs=followup_out)
        
    with gr.Tab("📄 Summarize PDF"):
        pdf_input = gr.File(label="📎 Upload a PDF", file_types=[".pdf"])
        pdf_btn = gr.Button("📑 Summarize")
        pdf_out = gr.Markdown()
        def summarize_pdf_with_status(pdf_file):
            yield "⏳ Extracting and summarizing PDF..."
            yield summarize_pdf(pdf_file)
        
        pdf_btn.click(summarize_pdf_with_status, inputs=pdf_input, outputs=pdf_out)

    with gr.Tab("🎥 Summarize YouTube Video"):
        yt_url = gr.Textbox(label="🎬 YouTube URL")
        yt_btn = gr.Button("📝 Summarize")
        yt_out = gr.Markdown()
        def summarize_youtube_with_status(url):
            yield "⏳ Fetching and summarizing YouTube video..."
            yield summarize_youtube(url)

        
        yt_btn.click(summarize_youtube_with_status, inputs=yt_url, outputs=yt_out)

if __name__ == "__main__":
    demo.launch()
