# 🎬 AI YouTube Video Note-Maker

Transform any YouTube video into structured, timestamped study notes, executive briefings, and flashcard quizzes in seconds using **Google Gemini** and **Streamlit**.

---

## ✨ Features

- **Multi-Format Note Generation**:
  - 📌 **Comprehensive Study Notes**: Executive summary, key takeaways, timestamped section breakdown, and action items.
  - 💼 **Quick Executive Briefing**: Bottom Line Up Front (BLUF) + Top 5 key takeaways.
  - 🧠 **Active Recall Flashcards & Quiz**: Study flashcards and self-test multiple-choice questions.
- **Dual Video Ingestion Strategy**:
  - Direct subtitle/caption extraction via `youtube-transcript-api`.
  - Seamless automatic fallback to **Google Gemini Multimodal Video Ingestion** (bypasses IP blocks and handles videos without subtitles).
  - Manual transcript paste tab for custom lectures or notes.
- **Export Options**:
  - 📕 **Download as PDF (.pdf)**: Beautifully formatted A4 documents with headers and page numbers.
  - 📄 **Download as Markdown (.md)**: 1-click import into Notion, Obsidian, or GitHub.
- **Reliability & Resilience**:
  - Exponential backoff retry logic to handle temporary Google Gemini 503 traffic surges.
  - Automatic model capability detection for any Google Gemini API key.

---

## 🚀 Quickstart (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/youtube-notes-ai.git
cd youtube-notes-ai
```

### 2. Create a virtual environment & install dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Set your API Key (Optional)
Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
*(Alternatively, enter your API key directly into the web UI sidebar).*

### 4. Run the app
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## ☁️ Deployment (Streamlit Community Cloud — 100% Free)

1. Push this repository to **GitHub**.
2. Go to **[share.streamlit.io](https://share.streamlit.io/)** and sign in with GitHub.
3. Click **"New app"**, select your repository, branch (`main`), and set Main file path to `app.py`.
4. Under **Advanced Settings > Secrets**, you can optionally set:
   ```toml
   GEMINI_API_KEY = "your_actual_key_here"
   ```
5. Click **"Deploy"** — your app is live on the internet with a public URL!
