import os
import streamlit as st
from dotenv import load_dotenv
from transcript_extractor import extract_video_id, get_video_transcript
from notes_generator import generate_notes, generate_notes_from_video_url, get_available_models
from pdf_exporter import convert_markdown_to_pdf

# Load existing environment variables
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI YouTube Note-Maker",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #FF0000;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #888;
        margin-bottom: 25px;
    }
    .stDownloadButton > button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if env_api_key:
        st.success("✅ Gemini API Key detected from `.env` file")
        api_key_input = st.text_input(
            "Override API Key (Optional)",
            value=env_api_key,
            type="password",
            help="Your API key from Google AI Studio"
        )
    else:
        st.info("💡 Paste your Google Gemini API key below to get started.")
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Get a 100% free key from https://aistudio.google.com/app/apikey"
        )
        st.markdown("[👉 Get a free Gemini API Key](https://aistudio.google.com/app/apikey)")

    st.divider()

    st.subheader("📝 Note Preferences")
    note_style = st.selectbox(
        "Choose Note Style",
        [
            "Comprehensive Study Notes",
            "Quick Executive Briefing",
            "Study Flashcards & Quiz"
        ],
        index=0
    )

    # Discover real models supported by the entered API key
    available_models = ["gemini-3.8-flash"]
    if api_key_input and api_key_input.strip():
        detected = get_available_models(api_key_input.strip())
        if detected:
            available_models = detected

    model_choice = st.selectbox(
        "Gemini Model",
        available_models,
        index=0,
        help="Active models detected for your Gemini account."
    )

    st.divider()
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. Paste any YouTube video link.
    2. We fetch the official captions/subtitles (or stream the video directly to Gemini if YouTube blocks scraping).
    3. Gemini AI processes the content and generates structured notes.
    4. Download your notes as **PDF** or **Markdown**!
    """)


# Main Interface
st.markdown('<div class="main-title">🎬 AI YouTube Video Note-Maker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Turn any YouTube video into structured, timestamped study notes in seconds.</div>', unsafe_allow_html=True)

# Session state initialization
if "generated_notes" not in st.session_state:
    st.session_state.generated_notes = None
if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None
if "raw_transcript" not in st.session_state:
    st.session_state.raw_transcript = None

tab_link, tab_paste = st.tabs(["🔗 By YouTube Video Link", "📋 Paste Transcript Manually"])

# TAB 1: BY YOUTUBE LINK
with tab_link:
    url_col, btn_col = st.columns([4, 1])
    with url_col:
        youtube_url = st.text_input(
            "Enter YouTube Video Link:",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="url_input"
        )
    with btn_col:
        generate_btn = st.button("🚀 Generate Notes", type="primary", use_container_width=True, key="btn_url")

    if generate_btn:
        if not youtube_url.strip():
            st.warning("⚠️ Please enter a valid YouTube video link.")
        elif not api_key_input.strip():
            st.error("🔑 Please provide a Gemini API Key in the left sidebar.")
        else:
            video_id = extract_video_id(youtube_url)
            
            if not video_id:
                st.error("❌ Could not recognize a valid YouTube Video ID from the link. Please check the URL format.")
            else:
                st.session_state.current_video_id = video_id
                clean_watch_url = f"https://www.youtube.com/watch?v={video_id}"
                
                with st.status("🔍 Processing video...", expanded=True) as status:
                    st.write("Extracting video captions and timestamps...")
                    transcript_res = get_video_transcript(video_id)
                    
                    if transcript_res["success"]:
                        st.write("✅ Transcript successfully extracted.")
                        st.session_state.raw_transcript = transcript_res["formatted_transcript"]
                        
                        try:
                            notes = generate_notes(
                                transcript_with_timestamps=transcript_res["formatted_transcript"],
                                note_style=note_style,
                                api_key=api_key_input.strip(),
                                model_name=model_choice,
                                status_callback=status.write
                            )
                            st.session_state.generated_notes = notes
                            status.update(label="✨ Notes generated successfully!", state="complete", expanded=False)
                        except Exception as err:
                            status.update(label="❌ AI Generation failed", state="error", expanded=True)
                            st.error(str(err))
                    else:
                        # YouTube blocked local IP. Seamless auto-fallback to Gemini Direct Video Ingestion!
                        st.info("ℹ️ YouTube blocked caption scraping from your IP. Automatically switching to Gemini Direct Video Analysis (Google servers analyze the video directly)...")
                        try:
                            notes = generate_notes_from_video_url(
                                video_url=clean_watch_url,
                                note_style=note_style,
                                api_key=api_key_input.strip(),
                                model_name=model_choice,
                                status_callback=status.write
                            )
                            st.session_state.generated_notes = notes
                            st.session_state.raw_transcript = "Note: Subtitle scraping was blocked by YouTube for this IP. Notes were generated by Google Gemini directly analyzing the video stream."
                            status.update(label="✨ Notes generated via Gemini Direct Video Analysis!", state="complete", expanded=False)
                        except Exception as fallback_err:
                            status.update(label="❌ Generation failed", state="error", expanded=True)
                            st.error(f"Captions blocked by YouTube, and Gemini direct analysis returned: {fallback_err}")

# TAB 2: PASTE TRANSCRIPT MANUALLY
with tab_paste:
    st.markdown("💡 *If YouTube ever blocks caption downloads for a video, you can copy the transcript from YouTube's description ('Show transcript') and paste it here!*")
    manual_video_url = st.text_input("Optional Video Link (for embedded preview):", placeholder="https://www.youtube.com/watch?v=...", key="manual_url")
    manual_transcript = st.text_area("Paste Transcript / Subtitles text here:", height=200, placeholder="Paste copied transcript text here...", key="manual_text")
    generate_manual_btn = st.button("🚀 Generate Notes from Text", type="primary", key="btn_manual")

    if generate_manual_btn:
        if not manual_transcript.strip():
            st.warning("⚠️ Please paste some transcript text first.")
        elif not api_key_input.strip():
            st.error("🔑 Please provide a Gemini API Key in the left sidebar.")
        else:
            vid_id = extract_video_id(manual_video_url) if manual_video_url.strip() else None
            st.session_state.current_video_id = vid_id or "custom_video"
            st.session_state.raw_transcript = manual_transcript
            
            with st.status("🤖 Generating notes with Gemini...", expanded=True) as status:
                try:
                    notes = generate_notes(
                        transcript_with_timestamps=manual_transcript,
                        note_style=note_style,
                        api_key=api_key_input.strip(),
                        model_name=model_choice,
                        status_callback=status.write
                    )
                    st.session_state.generated_notes = notes
                    status.update(label="✨ Notes generated successfully!", state="complete", expanded=False)
                except Exception as err:
                    status.update(label="❌ Generation failed", state="error", expanded=True)
                    st.error(str(err))


# DISPLAY RESULTS
if st.session_state.generated_notes:
    st.divider()
    
    col_video, col_notes = st.columns([1, 2])
    
    with col_video:
        st.subheader("📺 Video Player")
        if st.session_state.current_video_id and st.session_state.current_video_id != "custom_video":
            st.video(f"https://www.youtube.com/watch?v={st.session_state.current_video_id}")
        else:
            st.info("No video link provided for preview.")
        
        with st.expander("📄 View Transcript / Text Used"):
            st.text_area(
                "Transcript Content",
                value=st.session_state.raw_transcript,
                height=350,
                disabled=True
            )
            
    with col_notes:
        st.subheader("📝 Generated Notes")
        
        # Download Buttons (PDF & Markdown)
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            try:
                pdf_data = convert_markdown_to_pdf(st.session_state.generated_notes)
                st.download_button(
                    label="📕 Download as PDF (.pdf)",
                    data=pdf_data,
                    file_name=f"notes_{st.session_state.current_video_id}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as pdf_err:
                st.error(f"Could not prepare PDF: {pdf_err}")
                
        with dl_col2:
            st.download_button(
                label="📄 Download as Markdown (.md)",
                data=st.session_state.generated_notes,
                file_name=f"notes_{st.session_state.current_video_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        # Render markdown notes
        st.markdown(st.session_state.generated_notes)
