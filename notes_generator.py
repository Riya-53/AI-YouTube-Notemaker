import os
import time
from typing import Optional, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file if present
load_dotenv()


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Creates and returns a Gemini client.
    Priority:
    1. Explicitly passed api_key (from Streamlit UI input)
    2. GEMINI_API_KEY environment variable (from .env file)
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "Gemini API key is missing. Please provide it in the web interface sidebar "
            "or set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=key.strip())


def get_available_models(api_key: Optional[str] = None) -> List[str]:
    """
    Queries Google API to discover the exact models currently active and accessible for the user's key.
    """
    try:
        client = get_gemini_client(api_key=api_key)
        valid_models = []
        for m in client.models.list():
            actions = m.supported_actions or []
            if "generateContent" in actions:
                name = m.name
                if name.startswith("models/"):
                    name = name[len("models/"):]
                valid_models.append(name)
                
        # Put flash models first
        flash_models = [m for m in valid_models if "flash" in m.lower()]
        other_models = [m for m in valid_models if "flash" not in m.lower()]
        ordered = flash_models + other_models
        
        # Ensure gemini-3.8-flash is at the top if present
        if "gemini-3.8-flash" in ordered:
            ordered.remove("gemini-3.8-flash")
            ordered.insert(0, "gemini-3.8-flash")
            
        return ordered if ordered else ["gemini-3.8-flash"]
    except Exception:
        return ["gemini-3.8-flash"]


STYLE_PROMPTS = {
    "Comprehensive Study Notes": """
You are an expert academic tutor and technical note-taker. Transform the following video content into crystal-clear, beautifully organized study notes.

Structure your response with the following sections in clean Markdown:
# 📌 [Title of the Video / Topic]

## 🎯 Executive Summary (TL;DR)
A crisp 2-3 sentence overview of what the video covers and why it matters.

## 🔑 Key Takeaways & Core Concepts
- Highlight 4-6 primary lessons or big ideas.
- Use bold text for key terms.

## ⏱️ Detailed Section Breakdown (with Timestamps / Chapters)
Group the content chronologically:
- **[MM:SS] Topic / Section Title**: Detailed explanation, key arguments, formulas, or examples discussed.

## 💡 Practical Action Items / Next Steps
- Actionable steps the viewer can take immediately based on this video.

## 📝 Important Terminology / Glossary (if applicable)
- Define any technical jargon or specific keywords introduced in the video.
""",

    "Quick Executive Briefing": """
You are a senior executive assistant. Summarize the following video content into a concise briefing.

Structure your response in clean Markdown:
# 💼 Executive Briefing

## 🎯 Bottom Line Up Front (BLUF)
A 2-sentence summary of the main conclusion.

## 📋 Core Highlights (Top 5 Points)
1. ...
2. ...
3. ...
4. ...
5. ...

## 🚀 Strategic Recommendations / Action Items
- What decisions or actions should be taken based on this.
""",

    "Study Flashcards & Quiz": """
You are an educational quizmaster. Turn the following video content into an active recall study tool.

Structure your response in clean Markdown:
# 🧠 Active Recall Study Guide

## 🗂️ Flashcards (Question & Answer)
Provide 5-7 core concept flashcards:
- **Q**: [Question]
  - **A**: [Concise, accurate answer with relevant timestamp reference]

## ❓ Multiple Choice Self-Quiz
Provide 3-4 multiple choice questions to test comprehension:
1. **[Question]**
   - A) ...
   - B) ...
   - C) ...
   - D) ...
   *(Include the correct answer and a brief explanation beneath each question inside a spoiler or blockquote)*
"""
}


def generate_notes(
    transcript_with_timestamps: str,
    note_style: str = "Comprehensive Study Notes",
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.8-flash",
    status_callback: Optional[callable] = None
) -> str:
    """
    Sends the timestamped transcript to Google Gemini and generates structured notes.
    Handles temporary 503 high-demand spikes gracefully with progressive retries.
    """
    client = get_gemini_client(api_key=api_key)
    selected_prompt = STYLE_PROMPTS.get(note_style, STYLE_PROMPTS["Comprehensive Study Notes"])

    full_prompt = f"""
{selected_prompt}

----------------------
VIDEO TRANSCRIPT (WITH TIMESTAMPS):
{transcript_with_timestamps}
----------------------

Guidelines:
- Rely strictly on the information provided in the transcript.
- Do not make up timestamps or facts.
- Keep the formatting neat, legible, and visually engaging using Markdown headers, bullet points, and callouts.
"""

    delays = [3, 6, 9]
    last_error_msg = ""

    for attempt, delay in enumerate(delays):
        try:
            if status_callback:
                if attempt == 0:
                    status_callback(f"🤖 Generating notes with {model_name}...")
                else:
                    status_callback(f"⏳ Google AI is busy (503). Retrying with {model_name} (Attempt {attempt + 1}/{len(delays)})...")

            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )
            return response.text

        except Exception as e:
            error_msg = str(e)
            last_error_msg = error_msg

            if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                time.sleep(delay)
                continue
            elif "API_KEY_INVALID" in error_msg or ("400" in error_msg and "key" in error_msg.lower()):
                raise RuntimeError("Invalid Gemini API key. Please check your key from Google AI Studio.")
            elif "RESOURCE_EXHAUSTED" in error_msg:
                raise RuntimeError("Gemini API rate limit reached (15 requests/minute). Please wait 30 seconds and try again.")
            else:
                raise RuntimeError(f"Gemini API Error: {error_msg}")

    raise RuntimeError(
        f"Google AI servers are currently experiencing peak global demand (503). "
        "The server is temporarily busy—please click 'Generate Notes' again in 10-15 seconds."
    )


def generate_notes_from_video_url(
    video_url: str,
    note_style: str = "Comprehensive Study Notes",
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.8-flash",
    status_callback: Optional[callable] = None
) -> str:
    """
    Directly asks Google Gemini to watch and analyze the YouTube video URL natively.
    Bypasses local IP blocks completely because Google fetches the video internally from YouTube servers!
    """
    client = get_gemini_client(api_key=api_key)
    selected_prompt = STYLE_PROMPTS.get(note_style, STYLE_PROMPTS["Comprehensive Study Notes"])

    full_prompt = f"""
{selected_prompt}

Guidelines:
- Watch and listen to the YouTube video provided at this link.
- Extract all core concepts, main discussions, and key takeaways.
- Include estimated timestamps for different sections where applicable.
- Format the response in clean, structured Markdown.
"""

    video_part = types.Part.from_uri(
        file_uri=video_url,
        mime_type="video/mp4"
    )

    delays = [3, 6, 9]
    last_error_msg = ""

    for attempt, delay in enumerate(delays):
        try:
            if status_callback:
                if attempt == 0:
                    status_callback(f"🌐 Analyzing video directly via Google Gemini ({model_name})...")
                else:
                    status_callback(f"⏳ Google AI is busy (503). Retrying direct video analysis (Attempt {attempt + 1}/{len(delays)})...")

            response = client.models.generate_content(
                model=model_name,
                contents=[video_part, full_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )
            return response.text

        except Exception as e:
            error_msg = str(e)
            last_error_msg = error_msg

            if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                time.sleep(delay)
                continue
            elif "API_KEY_INVALID" in error_msg or ("400" in error_msg and "key" in error_msg.lower()):
                raise RuntimeError("Invalid Gemini API key. Please check your key from Google AI Studio.")
            elif "RESOURCE_EXHAUSTED" in error_msg:
                raise RuntimeError("Gemini API rate limit reached. Please wait 30 seconds and try again.")
            else:
                raise RuntimeError(f"Gemini API Direct Video Error: {error_msg}")

    raise RuntimeError(
        f"Google AI servers are temporarily busy (503). "
        "Please wait a few seconds and try clicking 'Generate Notes' again."
    )
