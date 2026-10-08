import os
import re
from fpdf import FPDF
import markdown


class NotesPDF(FPDF):
    def header(self):
        # Header banner
        self.set_font("Arial", "I", 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, "AI YouTube Video Notes", border=0, align="L")
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("Arial", "I", 9)
        self.set_text_color(150, 150, 150)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", border=0, align="C")


def clean_markdown_for_pdf(text: str) -> str:
    """
    Strips raw emojis and variation selectors that cannot be encoded by standard TTF fonts,
    replacing common section markers with clean text bullets.
    """
    # Replace common emoji headers with clean text
    replacements = {
        "📌": "■",
        "🎯": "•",
        "🔑": "•",
        "⏱️": "⏱",
        "💡": "•",
        "📝": "•",
        "💼": "■",
        "📋": "•",
        "🚀": "•",
        "🧠": "■",
        "🗂️": "•",
        "❓": "•",
    }
    for emoji, rep in replacements.items():
        text = text.replace(emoji, rep)

    # Strip any remaining 4-byte UTF-8 emojis or variation selectors
    clean_text = re.sub(
        r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe00-\ufe0f]",
        "",
        text
    )
    return clean_text


def convert_markdown_to_pdf(markdown_content: str, title: str = "Video Notes") -> bytes:
    """
    Converts a Markdown notes string into a styled, professional PDF binary.
    """
    pdf = NotesPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(left=18, top=18, right=18)
    pdf.add_page()

    # Load Windows system TrueType Arial fonts for clean UTF-8 rendering
    font_regular = "C:/Windows/Fonts/arial.ttf"
    font_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_italic = "C:/Windows/Fonts/ariali.ttf"

    has_custom_fonts = False
    if os.path.exists(font_regular) and os.path.exists(font_bold):
        try:
            pdf.add_font("Arial", "", font_regular)
            pdf.add_font("Arial", "B", font_bold)
            if os.path.exists(font_italic):
                pdf.add_font("Arial", "I", font_italic)
            pdf.set_font("Arial", size=10)
            has_custom_fonts = True
        except Exception:
            has_custom_fonts = False

    font_name = "Arial" if has_custom_fonts else "Helvetica"
    if not has_custom_fonts:
        pdf.set_font(font_name, size=10)

    # Sanitize emojis
    cleaned_md = clean_markdown_for_pdf(markdown_content)

    # Convert Markdown to basic HTML supported by FPDF write_html
    html = markdown.markdown(cleaned_md)

    # Custom HTML styling adjustments for PDF rendering
    styled_html = f"""
    <font face="{font_name}" size="10" color="#222222">
    {html}
    </font>
    """

    pdf.write_html(styled_html)
    
    # Return raw PDF bytes
    return bytes(pdf.output())
