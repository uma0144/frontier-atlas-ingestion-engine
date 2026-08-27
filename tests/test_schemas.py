"""
Unit tests for schema validation across all 5 entities and mapping log.
"""

from src.schemas import (
    StartupEntity,
    StartupContent,
    StartupData,
    SourceInfo,
    ProductEntity,
    ProductContent,
    PricingModelEnum,
    ResearchPaperEntity,
    ResearchPaperContent,
    JobEntity,
    JobContent,
    NewsEntity,
    NewsContent,
    EntityMappingRecord,
)


def test_startup_schema():
    startup = StartupEntity(
        schemaVersion="1.0",
        recordType="STARTUP",
        source=SourceInfo(name="Y Combinator", url="https://ycombinator.com/companies/openai"),
        content=StartupContent(
            entityName="OpenAI",
            data=StartupData(employeeCount=1500, industry="AI")
        )
    )
    flat = startup.to_flat_dict()
    assert flat["schemaVersion"] == "1.0"
    assert flat["recordType"] == "STARTUP"
    assert flat["content.entityName"] == "OpenAI"
    assert flat["content.data.employeeCount"] == 1500


def test_product_schema():
    product = ProductEntity(
        schemaVersion="1.0",
        recordType="PRODUCT",
        source=SourceInfo(name="Hugging Face", url="https://huggingface.co/openai/whisper"),
        content=ProductContent(
            productName="Whisper",
            startupName="OpenAI",
            pricingModel=PricingModelEnum.FREE,
            category="Speech Recognition"
        )
    )
    flat = product.to_flat_dict()
    assert flat["content.pricingModel"] == "FREE"
    assert flat["content.startupName"] == "OpenAI"


def test_research_paper_schema():
    paper = ResearchPaperEntity(
        schemaVersion="1.0",
        recordType="RESEARCH_PAPER",
        content=ResearchPaperContent(
            title="Attention Is All You Need",
            authors=["Vaswani et al."],
            paper_url="https://arxiv.org/abs/1706.03762",
            github_url="https://github.com/tensorflow/tensor2tensor",
            github_stars=14500,
            published_date="2017-06-12T00:00:00Z"
        )
    )
    flat = paper.to_flat_dict()
    assert flat["content.github_stars"] == 14500
    assert "Vaswani" in flat["content.authors"]


def test_job_schema():
    job = JobEntity(
        schemaVersion="1.0",
        recordType="JOB",
        content=JobContent(
            job_title="AI Research Scientist",
            company="Anthropic",
            date="2026-08-27T10:00:00Z",
            is_remote=True,
            role_family="AI Research",
            job_url="https://anthropic.com/careers"
        )
    )
    flat = job.to_flat_dict()
    assert flat["content.is_remote"] is True
    assert flat["content.role_family"] == "AI Research"


def test_news_schema():
    news = NewsEntity(
        schemaVersion="1.0",
        recordType="NEWS",
        content=NewsContent(
            title="New Frontier LLM Released",
            source_name="TechCrunch AI",
            url="https://techcrunch.com/article",
            published_date="2026-08-27T12:00:00Z",
            summary="State of the art reasoning model."
        )
    )
    flat = news.to_flat_dict()
    assert flat["content.source_name"] == "TechCrunch AI"


def test_mapping_log_schema():
    record = EntityMappingRecord(
        raw_name="OpenAI, Inc.",
        canonical_name="OpenAI",
        entity_type="STARTUP",
        confidence=1.0,
        resolution_method="EXACT_SEED_MATCH"
    )
    flat = record.to_flat_dict()
    assert flat["canonical_name"] == "OpenAI"
    assert flat["confidence"] == 1.0
