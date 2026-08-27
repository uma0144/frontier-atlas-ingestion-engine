"""
Unit tests for anti-413 HTML chunker.
"""

from src.llm.chunker import HTMLChunker


def test_html_cleaning():
    raw_html = """
    <html>
        <head><title>Test</title><style>.hidden { display: none; }</style></head>
        <body>
            <nav><a href="/">Home</a></nav>
            <main>
                <h1>Autonomous AI Agents</h1>
                <p>FrontierAtlas is indexing startups and AI research papers worldwide.</p>
            </main>
            <script>console.log("tracking script");</script>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    cleaned = HTMLChunker.clean_html(raw_html)
    assert "tracking script" not in cleaned
    assert "Copyright 2026" not in cleaned
    assert "Autonomous AI Agents" in cleaned
    assert "FrontierAtlas is indexing startups" in cleaned


def test_text_chunking():
    long_text = "Paragraph 1 about AI systems.\n\n" * 50
    chunks = HTMLChunker.chunk_text(long_text, max_chars=300)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 350
