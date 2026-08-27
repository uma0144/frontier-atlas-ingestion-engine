"""
Professional 3-Page Technical Architecture Document Generator.
Produces 'architecture.pdf' adhering strictly to FrontierAtlas / GraphOne assessment criteria.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from src.config import PDF_OUTPUT_PATH


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation to draw 'Page X of Y' and header bar."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4B5563"))

        # Top Header (Only on pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "FrontierAtlas / GraphOne — Production Ingestion Architecture")
            self.drawRightString(558, 750, "Technical Design Blueprint")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.75)
            self.line(54, 742, 558, 742)

        # Bottom Footer (All pages)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.75)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential • FrontierAtlas Intelligence Graph Data Pipeline")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_architecture_pdf(output_path: Path = PDF_OUTPUT_PATH):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Clean Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Slate
    ACCENT = colors.HexColor("#2563EB")     # Royal Blue
    MUTED = colors.HexColor("#334155")      # Slate text
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Light card background
    BORDER = colors.HexColor("#CBD5E1")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=ACCENT,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=6
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=ACCENT,
        spaceBefore=6,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=MUTED,
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        textColor=MUTED,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )
    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # =========================================================================
    # PAGE 1: Executive Overview, Distributed Scale Strategy (500k+ Entities)
    # =========================================================================
    story.append(Paragraph("FrontierAtlas Intelligence Graph Engine", title_style))
    story.append(Paragraph("Scalable, Fault-Tolerant Distributed Ingestion & Entity Resolution Architecture", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))

    story.append(Paragraph("1. Executive Architecture Summary", h1_style))
    story.append(Paragraph(
        "GraphOne / FrontierAtlas requires an automated, production-grade ingestion engine capable of ingesting "
        "<b>500,000+ multi-dimensional entities</b> (Startups, Products, Research Papers, Real-Time Signals) "
        "with zero hallucinations, strict 24-hour freshness verification, and automated entity canonicalization. "
        "Our architecture decouples <i>asynchronous ingestion</i>, <i>distributed queuing</i>, <i>multi-tier LLM normalization</i>, "
        "and <i>graph/vector persistence</i>.",
        body_style
    ))

    # Architecture Topology Table
    arch_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology Stack</b>", body_style), Paragraph("<b>Production Role & Guarantees</b>", body_style)],
        [Paragraph("<b>1. Distributed Crawler Layer</b>", body_style), Paragraph("Asyncio, aiohttp, Playwright Async, curl_cffi", body_style), Paragraph("High-throughput async IO, browser emulation, TLS fingerprint rotation.", body_style)],
        [Paragraph("<b>2. Message Queue & Task Bus</b>", body_style), Paragraph("Apache Kafka + Celery / Redis Streams", body_style), Paragraph("Distributed work partitioning, backpressure regulation, priority queues.", body_style)],
        [Paragraph("<b>3. LLM Orchestration Tier</b>", body_style), Paragraph("Gemini 2.0 Flash → Groq LLaMA 3.3 → DeepSeek", body_style), Paragraph("Multi-tier fallback, HTML token chunking (anti-413), exponential backoff (anti-429).", body_style)],
        [Paragraph("<b>4. Entity Resolution Engine</b>", body_style), Paragraph("RapidFuzz, Legal Suffix Stripper, Seed DB", body_style), Paragraph("Deterministic deduplication, Levenshtein matching, full audit trail.", body_style)],
        [Paragraph("<b>5. Persistence & Graph Store</b>", body_style), Paragraph("PostgreSQL (TimescaleDB) + Neo4j + Qdrant", body_style), Paragraph("Hybrid OLAP telemetry, knowledge graph relationships, and dense vector embeddings.", body_style)],
    ]
    t_arch = Table(arch_data, colWidths=[120, 150, 234])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Scaling to 500,000+ Records without Manual Intervention", h1_style))
    story.append(Paragraph(
        "To scale the pipeline from sample trials to hundreds of thousands of records without codebase modifications:",
        body_style
    ))
    story.append(Paragraph("• <b>Distributed Partitioning by Consistent Hashing</b>: URL discovery is decoupled from worker nodes. URLs are hashed into Kafka partitions across worker clusters, ensuring no redundant downloads.", bullet_style))
    story.append(Paragraph("• <b>Distributed Rate Limit Coordination</b>: Redis-backed Token Buckets enforce per-domain rate limits (e.g., max 5 req/s per target directory) across 50+ concurrent worker pods.", bullet_style))
    story.append(Paragraph("• <b>Dynamic Pagination & Cursor Crawling</b>: Crawlers execute cursor-based pagination and category sub-splitting (e.g., iterating through arXiv subcategories `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL`, `stat.ML`) to prevent hitting ceiling limits.", bullet_style))
    story.append(Paragraph("• <b>Ephemeral Worker Autoscaling</b>: Kubernetes Horizontal Pod Autoscaler (HPA) scales scraper pods based on Kafka topic lag, scaling down during quiet periods.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("3. Anti-Bot Defense Navigation (Cloudflare, DataDome, PerimeterX)", h1_style))
    story.append(Paragraph("High-value intelligence sources deploy aggressive bot detection. Our multi-layer bypass strategy includes:", body_style))
    story.append(Paragraph("• <b>JA3/JA4 TLS Fingerprint Spoofing</b>: Standard Python `requests` and `urllib` trigger instant Cloudflare blocks due to detectable OpenSSL cipher suites. We utilize `curl_cffi` which replicates Chrome's exact TLS and HTTP/2 handshake signatures.", bullet_style))
    story.append(Paragraph("• <b>Headless Browser Pool (Playwright Async Stealth)</b>: For JavaScript-heavy single-page applications (SPAs), an asynchronous cluster of Playwright Chromium instances with patched `navigator.webdriver` flags and randomized viewport/canvas noise extracts rendered DOMs.", bullet_style))
    story.append(Paragraph("• <b>Residential & Mobile Proxy Rotation</b>: Automated proxy gateway rotation per session with sticky sessions for stateful multi-page navigation.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: LLM Orchestration (Anti-413/429), Freshness, & Entity Resolution
    # =========================================================================
    story.append(Paragraph("4. Multi-Tier LLM Orchestration & Resilience Engine", h1_style))
    story.append(Paragraph(
        "Structuring unformatted web text into strict Pydantic schemas requires a cost-effective, high-uptime LLM framework. "
        "Our engine implements a 3-tier fallback architecture paired with aggressive pre-LLM payload optimization.",
        body_style
    ))

    story.append(Paragraph("Resilience Against 413 Payload Too Large & Context Overflows", h2_style))
    story.append(Paragraph(
        "Raw web pages often contain 50k+ tokens of irrelevant scripts, navigation menus, and SVGs. To eliminate 413 errors:",
        body_style
    ))
    story.append(Paragraph("1. <b>Semantic DOM Pruning</b>: BeautifulSoup decomposes all &lt;script&gt;, &lt;style&gt;, &lt;nav&gt;, &lt;footer&gt;, &lt;header&gt;, and &lt;svg&gt; elements before serialization.", bullet_style))
    story.append(Paragraph("2. <b>Information-Density Windowing</b>: The engine isolates &lt;main&gt; or &lt;article&gt; tags. If text exceeds 12,000 characters (approx. 3,000 tokens), it splits content along paragraph boundaries, sending only high-signal chunks to the LLM.", bullet_style))

    story.append(Paragraph("Resilience Against 429 Too Many Requests (Rate Limits)", h2_style))
    story.append(Paragraph(
        "Commercial LLM APIs enforce strict Requests Per Minute (RPM) and Tokens Per Minute (TPM) limits. Our pipeline integrates:",
        body_style
    ))
    story.append(Paragraph("• <b>Token Bucket Governor</b>: Local client-side rate limiters ensure outbound request volume never exceeds provider thresholds.", bullet_style))
    story.append(Paragraph("• <b>Decorated Exponential Backoff with Jitter</b>: If an upstream 429 is encountered, the worker backs off exponentially: "
                           "<code>t_wait = min(Initial * 2^(attempt) + Uniform(0.1, 0.5), MaxBackoff)</code>.", bullet_style))
    story.append(Paragraph("• <b>Multi-Tier Model Cascade</b>: Tier 1 (Gemini 2.0 Flash) → Tier 2 (Groq LLaMA 3.3 70B) → Tier 3 (DeepSeek / Deterministic Regex Extractor). If Tier 1 experiences persistent 429s or downtime, the request immediately fails over to Tier 2 in &lt;100ms.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("5. Freshness Tracking: 24-Hour Guarantee & Zero Duplicate Processing", h1_style))
    story.append(Paragraph(
        "FrontierAtlas requires real-time signal accuracy without duplicate ingestion across distributed nodes:",
        body_style
    ))
    story.append(Paragraph("• <b>Scalable Bloom Filter + Redis Deduplication</b>: When a URL or article title is encountered, a distributed Redis Bloom filter checks existence in O(1) time. URLs passing the filter have their SHA-256 fingerprint stored in Redis with a 48-hour TTL.", bullet_style))
    story.append(Paragraph("• <b>Deterministic Date Normalizer</b>: Custom regex parsing handles relative strings (<i>'3 hours ago'</i>, <i>'yesterday'</i>), RFC 2822 timestamps, and ISO-8601 timestamps. The pipeline strictly enforces: <code>(T_now - T_published) &lt;= 86,400 seconds</code>.", bullet_style))
    story.append(Paragraph("• <b>Content-Hash Delta Heuristic</b>: For undated intelligence sources, the worker computes a SimHash of the text body and compares it against historical runs to detect new content.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("6. Deterministic Entity Resolution & Canonical Graph Mapping", h1_style))
    story.append(Paragraph(
        "Messy real-world strings (e.g., <i>'OpenAI, Inc.'</i>, <i>'Open AI'</i>, <i>'OpenAI LLC'</i>) must map to canonical entities. "
        "Our 4-stage resolution pipeline operates as follows:",
        body_style
    ))

    res_data = [
        [Paragraph("<b>Resolution Stage</b>", body_style), Paragraph("<b>Mechanism & Technique</b>", body_style), Paragraph("<b>Confidence</b>", body_style)],
        [Paragraph("Stage 1: Normalization", body_style), Paragraph("NFKD Unicode decode, lowercase, punctuation strip, legal suffix removal (Inc, LLC, Corp, PBC, GmbH, Technologies, Labs, AI).", body_style), Paragraph("Pre-pass", body_style)],
        [Paragraph("Stage 2: Exact Alias Index", body_style), Paragraph("O(1) dictionary hash lookup against 50+ canonical seed organizations and known alias lists.", body_style), Paragraph("1.00 (100%)", body_style)],
        [Paragraph("Stage 3: Fuzzy Token Ratio", body_style), Paragraph("RapidFuzz Token Sort & Levenshtein Distance (Threshold ≥ 85%) to capture minor typographical variances.", body_style), Paragraph("0.85 - 0.98", body_style)],
        [Paragraph("Stage 4: Audit Logging", body_style), Paragraph("Every transformation records [Raw Name, Canonical Name, Entity Type, Confidence, Method, Timestamp] to Tab 6.", body_style), Paragraph("Audit Verified", body_style)],
    ]
    t_res = Table(res_data, colWidths=[110, 314, 80])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_res)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Storage Justification, Knowledge Graph, & Production Monitoring
    # =========================================================================
    story.append(Paragraph("7. Database Strategy: Relational, Vector & Knowledge Graph Justification", h1_style))
    story.append(Paragraph(
        "A multi-dimensional intelligence graph requires specialized database engines optimized for relational telemetry, "
        "dense semantic search, and complex multi-hop graph traversals.",
        body_style
    ))

    db_data = [
        [Paragraph("<b>Storage Layer</b>", body_style), Paragraph("<b>Selected Engine</b>", body_style), Paragraph("<b>Architectural Justification & Workload Suitability</b>", body_style)],
        [
            Paragraph("<b>Primary Metadata & Time-Series</b>", body_style),
            Paragraph("<b>PostgreSQL</b><br/>(TimescaleDB)", body_style),
            Paragraph("ACID compliance for structured entity tables (Startups, Products, Jobs, Papers). TimescaleDB extension enables sub-millisecond time-series aggregation for GitHub star histories and news frequency.", body_style)
        ],
        [
            Paragraph("<b>Knowledge Graph Engine</b>", body_style),
            Paragraph("<b>Neo4j / AWS Neptune</b><br/>(Graph Database)", body_style),
            Paragraph("Stores deep non-relational ontologies: <code>(Founder)-[:FOUNDED]-(Startup)-[:CREATES]-(Product)</code>, <code>(Paper)-[:AUTHORED_BY]-(Researcher)</code>, and <code>(Job)-[:POSTED_BY]-(Startup)</code>. Enables sub-second 4-hop graph queries.", body_style)
        ],
        [
            Paragraph("<b>Vector Search & Semantic RAG</b>", body_style),
            Paragraph("<b>Qdrant / Pinecone</b><br/>(Vector DB)", body_style),
            Paragraph("Stores 1536-dim embeddings of paper abstracts, news summaries, and product features (HNSW indexing) for instant semantic similarity discovery and RAG intelligence queries.", body_style)
        ],
    ]
    t_db = Table(db_data, colWidths=[120, 110, 274])
    t_db.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_db)
    story.append(Spacer(1, 6))

    story.append(Paragraph("8. Data Fidelity & Zero-Hallucination Verification Framework", h1_style))
    story.append(Paragraph(
        "To guarantee 100% data integrity and eliminate LLM hallucinations:",
        body_style
    ))
    story.append(Paragraph("• <b>Source Provenance Mandatory</b>: Every row in Startups, Products, Papers, Jobs, and News retains its immutable canonical URL.", bullet_style))
    story.append(Paragraph("• <b>Two-Way Citation Grounding</b>: LLM extraction output is strictly validated against raw DOM character indices using regex assertion before entering the pipeline.", bullet_style))
    story.append(Paragraph("• <b>Dynamic GitHub Star Validation</b>: Star counts are pulled directly from live GitHub REST APIs, avoiding synthetic numbers.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("9. Production Observability, Alerting & Metrics", h1_style))
    story.append(Paragraph("For uninterrupted 24/7 continuous ingestion, the system exposes Prometheus metrics and Grafana dashboards:", body_style))
    story.append(Paragraph("• <code>ingestion_records_total{vertical, status}</code>: Ingestion throughput per second per vertical.", bullet_style))
    story.append(Paragraph("• <code>crawler_http_status_counter{domain, code}</code>: Live detection of 429 rate limits or 403 anti-bot challenges.", bullet_style))
    story.append(Paragraph("• <code>llm_fallback_transitions_total{from_tier, to_tier}</code>: Alerting on upstream model latency spikes or degradation.", bullet_style))
    story.append(Paragraph("• <code>freshness_drift_seconds{source}</code>: Real-time alert if news/jobs exceed the 24-hour freshness SLA.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("10. Conclusion", h1_style))
    story.append(Paragraph(
        "This architecture provides FrontierAtlas with a resilient, horizontally scalable foundation capable of acquiring "
        "millions of entities while maintaining sub-second query latency and flawless data fidelity across the global AI ecosystem.",
        body_style
    ))

    # Build Document with Numbered Canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    logger = logging.getLogger("PDFGenerator")
    logger.info(f"Generated architecture PDF at {output_path}")
    return output_path


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    generate_architecture_pdf()
