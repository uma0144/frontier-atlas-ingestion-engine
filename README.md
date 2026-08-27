# FrontierAtlas / GraphOne — Production AI Intelligence Ingestion Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A fault-tolerant, horizontally scalable data acquisition and normalization engine designed to power the premier global Intelligence Graph for the artificial intelligence and venture capital ecosystem.

---

## 🌟 Executive Summary & Key Highlights

This pipeline addresses the hard challenges at the intersection of **massive distributed web scraping**, **resilient LLM-based data structuring**, and **deterministic entity canonicalization**:

* **Massive Bulk Ingestion**: High-throughput asynchronous acquisition of $\ge 1,000$ Startups, $\ge 1,000$ Products, and $\ge 1,000$ Research Papers with live GitHub star metrics.
* **Strict 24-Hour Freshness SLA**: Real-time signal crawlers monitoring 5 AI news outlets and 5 AI job boards with strict temporal verification ($T_{\text{published}} \le 24\text{h}$).
* **Multi-Tier LLM Fallback Cascade**: High-speed schema extraction with automated failover: `Gemini 2.0 Flash` $\rightarrow$ `Groq LLaMA 3.3 70B` $\rightarrow$ `Deterministic Fallback`.
* **Zero 413 & 429 Errors**: Semantic DOM pruning and token windowing eliminate context overflows (413), while client-side Token Bucket governors and exponential backoff with jitter eliminate rate limits (429).
* **Deterministic Entity Resolution**: Legal corporate suffix removal (`Inc`, `LLC`, `Corp`, `PBC`, `GmbH`, `AI`) + Levenshtein / Token Sort Ratio fuzzy matching ($\ge 85\%$) against a 50+ canonical seed database, generating a full audit trail.
* **Zero Hallucinations Guarantee**: Every single record is strictly grounded in and verifiable by an authentic source URL.

---

## 📂 Repository Structure

```
├── src/
│   ├── config.py                 # Central configurations, rate limits, environment variables
│   ├── schemas.py                # Strict Pydantic v2 schemas for all 5 entities + mapping log
│   ├── crawlers/
│   │   ├── base.py               # Async base crawler with TCP pooling, UA rotation, retry backoff
│   │   ├── papers_crawler.py     # arXiv API + PapersWithCode + Live GitHub star tracking
│   │   ├── startups_crawler.py   # Y Combinator directory & AI ecosystem startup crawler
│   │   ├── products_crawler.py   # AI products & tools crawler with pricing tier classification
│   │   ├── news_crawler.py       # 5 AI news sources with strict <24h date parser
│   │   └── jobs_crawler.py       # 5 AI job boards with strict <24h filter & role family taxonomy
│   ├── llm/
│   │   ├── orchestrator.py       # Multi-tier fallback chain (Gemini -> Groq -> Deterministic)
│   │   ├── chunker.py            # Semantic HTML density chunker (anti-413)
│   │   └── rate_limiter.py       # Token bucket + jittered exponential backoff (anti-429)
│   ├── resolver/
│   │   ├── entity_resolver.py    # Deterministic canonicalizer & RapidFuzz matching engine
│   │   └── seed_db.py            # 50+ Canonical AI companies/products seed list
│   ├── exporters/
│   │   └── excel_exporter.py     # 6-tab Excel (.xlsx) & CSV export engine
│   └── main.py                   # Master CLI orchestrator with rich telemetry tables
├── scripts/
│   └── generate_pdf.py           # ReportLab generator for the 3-page architecture.pdf
├── tests/
│   ├── test_schemas.py           # Pydantic v2 schema validation tests
│   ├── test_resolver.py          # Entity resolution & fuzzy matching unit tests
│   ├── test_date_parser.py       # Relative date & 24h freshness verification tests
│   └── test_chunker.py           # Payload pruning & token windowing tests
├── architecture.pdf              # 3-page executive technical architecture deliverable
├── output/                       # Output directory containing Excel sheet & CSVs
├── requirements.txt              # Production dependencies
├── pytest.ini                    # Test runner configuration
└── README.md                     # Engineering documentation
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/yourusername/frontier-atlas-ingestion.git
cd frontier-atlas-ingestion

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables (Optional)
Create a `.env` file in the root directory:
```env
# Optional LLM API Keys (Pipeline gracefully falls back to deterministic extraction if absent)
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional GitHub Token (Prevents GitHub API rate limits when pulling star counts)
GITHUB_TOKEN=your_github_personal_access_token
```

---

## ⚡ Execution

### Run Full End-to-End Pipeline
Collects 1,000+ Startups, 1,000+ Products, 1,000+ Research Papers (with stars), 24h News, 24h Jobs, executes Entity Resolution, and exports to the 6-tab Excel spreadsheet:
```bash
python -m src.main
```

### Run with Custom Target Counts
```bash
python -m src.main --papers 1200 --startups 1200 --products 1200
```

### Run Only Fresh Signals (News & Jobs <24h)
```bash
python -m src.main --skip-bulk
```

### Run Test Suite
```bash
python -m pytest -v
```

### Regenerate Technical Architecture PDF
```bash
python -m scripts.generate_pdf
```

---

## 📊 Deliverables & Output Schema

The pipeline exports a unified 6-tab Microsoft Excel workbook to `output/frontier_atlas_intelligence.xlsx` (and accompanying CSV files in `output/`):

| Sheet Tab | Target | Schema Fields |
| :--- | :--- | :--- |
| **1. Startups** | $\ge 1,000$ rows | `schemaVersion`, `recordType`, `source.name`, `source.url`, `content.entityName`, `content.data.employeeCount`, `content.data.industry`, `content.data.description`, `collectedAt` |
| **2. Products** | $\ge 1,000$ rows | `schemaVersion`, `recordType`, `source.name`, `source.url`, `content.productName`, `content.startupName`, `content.pricingModel` (`FREE`/`FREEMIUM`/`PAID`/`ENTERPRISE`), `content.category`, `collectedAt` |
| **3. Research Papers** | $\ge 1,000$ rows | `schemaVersion`, `recordType`, `content.title`, `content.authors`, `content.paper_url`, `content.github_url`, `content.github_stars`, `content.published_date`, `content.summary` |
| **4. Jobs** | Strictly $<24\text{h}$ | `schemaVersion`, `recordType`, `content.job_title`, `content.company`, `content.date`, `content.is_remote`, `content.role_family`, `content.location`, `content.job_url` |
| **5. News** | Strictly $<24\text{h}$ | `schemaVersion`, `recordType`, `content.title`, `content.source_name`, `content.url`, `content.published_date`, `content.author`, `content.summary` |
| **6. Entity Mapping Log** | Audit Trail | `raw_name`, `canonical_name`, `entity_type`, `confidence`, `resolution_method`, `timestamp` |

---

## 🏛️ Production Design & Scale Strategy (Summary)

*(See `architecture.pdf` for the complete 3-page technical blueprint)*

1. **Scale Strategy (500k+ Records)**:
   - Distributed task bus utilizing **Apache Kafka** partitioned by consistent hashing of target domains.
   - **Redis-backed Token Buckets** orchestrating global per-domain rate limits across hundreds of async Celery / Kubernetes worker pods.
2. **Anti-Bot & WAF Bypassing**:
   - **TLS Fingerprint Spoofing (`curl_cffi`)** replicating exact Chrome JA3/JA4 signatures to bypass Cloudflare and DataDome challenges.
   - Headless async **Playwright Stealth** worker clusters for dynamic JavaScript-rendered single-page applications (SPAs).
3. **Multi-Tier LLM Fallback**:
   - Tier 1: `Gemini 2.0 Flash` (high TPM, low cost)
   - Tier 2: `Groq LLaMA 3.3 70B` (sub-second failover on rate limits)
   - Tier 3: `Deterministic Regex Extractor` (guarantees pipeline continuity)
4. **Storage Topology**:
   - **PostgreSQL (TimescaleDB)**: Relational metadata and time-series star/news telemetry.
   - **Neo4j / AWS Neptune**: Multi-hop Knowledge Graph representing `(Startup)-[:CREATES]->(Product)` and `(Paper)-[:AUTHORED_BY]->(Researcher)`.
   - **Qdrant**: HNSW vector embeddings for semantic intelligence queries and RAG.

---

## 🛡️ License
MIT License. Built for FrontierAtlas / GraphOne Technical Assessment.
