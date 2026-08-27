"""
Pydantic v2 schemas for all intelligence graph entities and mapping logs.
Strictly adheres to FrontierAtlas / GraphOne evaluation specifications.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class PricingModelEnum(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"


class SourceInfo(BaseModel):
    name: str = Field(..., description="Name of the source site")
    url: str = Field(..., description="Original source URL")


# ==========================================
# 1. Startup Entity Schema
# ==========================================
class StartupData(BaseModel):
    employeeCount: Optional[int] = Field(default=None, description="Number of employees")
    industry: Optional[str] = Field(default=None, description="Industry or sector")
    description: Optional[str] = Field(default=None, description="Brief description")
    location: Optional[str] = Field(default=None, description="Headquarters location")


class StartupContent(BaseModel):
    entityName: str = Field(..., description="Canonical startup name")
    data: StartupData = Field(default_factory=StartupData)


class StartupEntity(BaseModel):
    schemaVersion: str = Field(default="1.0", description="Versioning for the schema")
    recordType: str = Field(default="STARTUP", description="Fixed to STARTUP")
    source: SourceInfo
    content: StartupContent
    collectedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp"
    )

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "recordType": self.recordType,
            "source.name": self.source.name,
            "source.url": self.source.url,
            "content.entityName": self.content.entityName,
            "content.data.employeeCount": self.content.data.employeeCount or "",
            "content.data.industry": self.content.data.industry or "",
            "content.data.description": self.content.data.description or "",
            "collectedAt": self.collectedAt,
        }


# ==========================================
# 2. Product Entity Schema
# ==========================================
class ProductContent(BaseModel):
    productName: str = Field(..., description="Product name")
    startupName: str = Field(..., description="Canonical startup/creator name")
    pricingModel: PricingModelEnum = Field(
        default=PricingModelEnum.FREEMIUM, 
        description="FREE, FREEMIUM, PAID, ENTERPRISE"
    )
    category: Optional[str] = Field(default="AI Tool", description="Product category")
    description: Optional[str] = Field(default=None, description="Product summary")


class ProductEntity(BaseModel):
    schemaVersion: str = Field(default="1.0", description="Versioning for the schema")
    recordType: str = Field(default="PRODUCT", description="Fixed to PRODUCT")
    source: SourceInfo
    content: ProductContent
    collectedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp"
    )

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "recordType": self.recordType,
            "source.name": self.source.name,
            "source.url": self.source.url,
            "content.productName": self.content.productName,
            "content.startupName": self.content.startupName,
            "content.pricingModel": self.content.pricingModel.value if hasattr(self.content.pricingModel, 'value') else str(self.content.pricingModel),
            "content.category": self.content.category or "",
            "content.description": self.content.description or "",
            "collectedAt": self.collectedAt,
        }


# ==========================================
# 3. Research Paper Entity Schema
# ==========================================
class ResearchPaperContent(BaseModel):
    title: str = Field(..., description="Title of the research paper")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    paper_url: str = Field(..., description="Link to the Arxiv/PDF page")
    github_url: Optional[str] = Field(default=None, description="Link to associated code repository")
    github_stars: Optional[int] = Field(default=0, description="Current number of stars on GitHub repo")
    published_date: str = Field(..., description="ISO-8601 publication date")
    summary: Optional[str] = Field(default=None, description="Abstract / Summary")


class ResearchPaperEntity(BaseModel):
    schemaVersion: str = Field(default="1.0", description="Versioning for the schema")
    recordType: str = Field(default="RESEARCH_PAPER", description="Fixed to RESEARCH_PAPER")
    content: ResearchPaperContent

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "recordType": self.recordType,
            "content.title": self.content.title,
            "content.authors": ", ".join(self.content.authors) if isinstance(self.content.authors, list) else str(self.content.authors),
            "content.paper_url": self.content.paper_url,
            "content.github_url": self.content.github_url or "",
            "content.github_stars": self.content.github_stars if self.content.github_stars is not None else 0,
            "content.published_date": self.content.published_date,
            "content.summary": self.content.summary or "",
        }


# ==========================================
# 4. Job Entity Schema
# ==========================================
class JobContent(BaseModel):
    job_title: str = Field(..., description="Title of the job role")
    company: str = Field(..., description="Canonical company name")
    date: str = Field(..., description="ISO-8601 publication date")
    is_remote: bool = Field(default=True, description="Remote eligibility")
    role_family: str = Field(default="Engineering", description="Functional category (e.g., Engineering, Research)")
    location: Optional[str] = Field(default="Remote", description="Job location")
    job_url: str = Field(..., description="Application URL")


class JobEntity(BaseModel):
    schemaVersion: str = Field(default="1.0", description="Versioning for the schema")
    recordType: str = Field(default="JOB", description="Fixed to JOB")
    content: JobContent

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "recordType": self.recordType,
            "content.job_title": self.content.job_title,
            "content.company": self.content.company,
            "content.date": self.content.date,
            "content.is_remote": self.content.is_remote,
            "content.role_family": self.content.role_family,
            "content.location": self.content.location or "",
            "content.job_url": self.content.job_url,
        }


# ==========================================
# 5. News Entity Schema
# ==========================================
class NewsContent(BaseModel):
    title: str = Field(..., description="Headline of the news article")
    source_name: str = Field(..., description="Publication source name")
    url: str = Field(..., description="Direct URL to article")
    published_date: str = Field(..., description="ISO-8601 publication date")
    summary: str = Field(..., description="Extracted full-text summary / snippet")
    author: Optional[str] = Field(default=None, description="Author name")


class NewsEntity(BaseModel):
    schemaVersion: str = Field(default="1.0", description="Versioning for the schema")
    recordType: str = Field(default="NEWS", description="Fixed to NEWS")
    content: NewsContent

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "recordType": self.recordType,
            "content.title": self.content.title,
            "content.source_name": self.content.source_name,
            "content.url": self.content.url,
            "content.published_date": self.content.published_date,
            "content.author": self.content.author or "",
            "content.summary": self.content.summary,
        }


# ==========================================
# 6. Entity Mapping Log Schema (Audit Trail)
# ==========================================
class EntityMappingRecord(BaseModel):
    raw_name: str = Field(..., description="Raw extracted string from web source")
    canonical_name: str = Field(..., description="Normalized/canonicalized entity name")
    entity_type: str = Field(default="STARTUP", description="STARTUP, PRODUCT, or COMPANY")
    confidence: float = Field(default=1.0, description="Match confidence score (0.0 - 1.0)")
    resolution_method: str = Field(
        default="EXACT_MATCH", 
        description="EXACT_MATCH, RULE_BASED, FUZZY_LEVENSTEIN, SEED_LOOKUP, or LLM"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 resolution timestamp"
    )

    def to_flat_dict(self) -> Dict[str, Any]:
        return {
            "raw_name": self.raw_name,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "confidence": round(self.confidence, 4),
            "resolution_method": self.resolution_method,
            "timestamp": self.timestamp,
        }
