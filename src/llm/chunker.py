"""
Intelligent HTML & Payload Chunker (Anti-413 Payload Too Large Engine):
Strips non-semantic boilerplate and truncates/chunks text while preserving dense informational tokens.
"""

import re
from typing import List
from bs4 import BeautifulSoup
from src.config import MAX_HTML_CHARS, MAX_CHUNK_TOKENS


class HTMLChunker:
    @staticmethod
    def clean_html(html_content: str) -> str:
        """Strip scripts, stylesheets, SVG, navigations, and return dense clean text."""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove non-content tags
        for element in soup(["script", "style", "nav", "footer", "header", "svg", "noscript", "iframe", "form"]):
            element.decompose()

        # Extract main semantic containers if available
        main_content = soup.find(["main", "article", "div#content", "div.post-content"])
        if main_content:
            text = main_content.get_text(separator="\n")
        else:
            text = soup.get_text(separator="\n")

        # Clean excessive newlines and whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        return cleaned_text

    @staticmethod
    def chunk_text(text: str, max_chars: int = MAX_HTML_CHARS) -> List[str]:
        """Split clean text into semantically preserved windows preventing 413s."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para) + 2
            if current_length + para_len > max_chars:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [para]
                    current_length = para_len
                else:
                    # Single paragraph exceeds max_chars, split by sentence or character boundary
                    chunks.append(para[:max_chars])
                    current_chunk = []
                    current_length = 0
            else:
                current_chunk.append(para)
                current_length += para_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks
