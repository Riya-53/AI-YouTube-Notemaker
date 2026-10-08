import re
from typing import Optional, Dict
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extracts the unique 11-character video ID from various YouTube URL formats.
    
    Supported formats:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://www.youtube.com/shorts/dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ
    - Raw ID: dQw4w9WgXcQ
    """
    url = url.strip()
    
    # If the user typed or pasted just the 11-character ID directly
    if len(url) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
        
    # Match standard patterns across desktop, mobile, shorts, and embed links
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/embed\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    return None


def format_timestamp(seconds: float) -> str:
    """Converts seconds (e.g. 75.4) into readable [MM:SS] or [HH:MM:SS] format."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_video_transcript(video_id: str, languages: tuple = ("en", "en-US", "en-GB")) -> Dict[str, any]:
    """
    Fetches the transcript for a given YouTube video ID.
    
    Returns a dictionary:
    - success (bool): True if fetched successfully
    - formatted_transcript (str): Transcript with [MM:SS] timestamps for LLM
    - raw_text (str): Continuous paragraph text
    - error (str): Error description if failed
    """
    api = YouTubeTranscriptApi()
    
    try:
        # Fetch transcript using the API instance
        transcript = api.fetch(video_id, languages=languages)
        
        formatted_lines = []
        raw_words = []
        
        for item in transcript.snippets:
            time_str = format_timestamp(item.start)
            clean_text = item.text.replace("\n", " ").strip()
            
            # Timestamped entry for LLM note organization
            formatted_lines.append(f"[{time_str}] {clean_text}")
            raw_words.append(clean_text)
            
        return {
            "success": True,
            "formatted_transcript": "\n".join(formatted_lines),
            "raw_text": " ".join(raw_words),
            "error": None
        }
        
    except TranscriptsDisabled:
        return {
            "success": False,
            "formatted_transcript": None,
            "raw_text": None,
            "error": "Transcripts / Subtitles are disabled for this video."
        }
        
    except NoTranscriptFound:
        # If preferred languages aren't found, check if any caption track exists
        try:
            transcript_list = api.list(video_id)
            first_transcript = next(iter(transcript_list))
            actual_transcript = first_transcript.fetch()
            
            formatted_lines = [
                f"[{format_timestamp(i.start)}] {i.text.replace(chr(10), ' ').strip()}"
                for i in actual_transcript.snippets
            ]
            raw_words = [i.text.replace(chr(10), ' ').strip() for i in actual_transcript.snippets]
            
            return {
                "success": True,
                "formatted_transcript": "\n".join(formatted_lines),
                "raw_text": " ".join(raw_words),
                "error": None
            }
        except Exception as fallback_error:
            return {
                "success": False,
                "formatted_transcript": None,
                "raw_text": None,
                "error": f"No transcript found for this video: {str(fallback_error)}"
            }
            
    except VideoUnavailable:
        return {
            "success": False,
            "formatted_transcript": None,
            "raw_text": None,
            "error": "The video is unavailable, private, or has been removed."
        }
        
    except Exception as e:
        return {
            "success": False,
            "formatted_transcript": None,
            "raw_text": None,
            "error": f"Failed to fetch transcript: {str(e)}"
        }
