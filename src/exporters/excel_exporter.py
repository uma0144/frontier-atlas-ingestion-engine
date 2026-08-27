"""
Data Exporter:
Exports all 5 entity collections and entity mapping audit logs into a unified
6-tab Microsoft Excel spreadsheet (.xlsx) and individual CSVs for Google Sheets import.
"""

import logging
from pathlib import Path
from typing import List
import pandas as pd
from src.schemas import (
    StartupEntity,
    ProductEntity,
    ResearchPaperEntity,
    JobEntity,
    NewsEntity,
    EntityMappingRecord,
)
from src.config import EXCEL_OUTPUT_PATH, OUTPUT_DIR

logger = logging.getLogger("Exporter")


class ExcelExporter:
    @staticmethod
    def export_all(
        startups: List[StartupEntity],
        products: List[ProductEntity],
        papers: List[ResearchPaperEntity],
        jobs: List[JobEntity],
        news: List[NewsEntity],
        mappings: List[EntityMappingRecord],
        output_path: Path = EXCEL_OUTPUT_PATH
    ) -> Path:
        """Export all data to a 6-tab Excel workbook and accompanying CSV files."""
        logger.info(f"Generating 6-tab Excel workbook at {output_path}...")

        # 1. Convert entities to flat dictionaries for DataFrames
        df_startups = pd.DataFrame([s.to_flat_dict() for s in startups])
        df_products = pd.DataFrame([p.to_flat_dict() for p in products])
        df_papers = pd.DataFrame([r.to_flat_dict() for r in papers])
        df_jobs = pd.DataFrame([j.to_flat_dict() for j in jobs])
        df_news = pd.DataFrame([n.to_flat_dict() for n in news])
        df_mappings = pd.DataFrame([m.to_flat_dict() for m in mappings])

        # 2. Write to Multi-Tab Excel Spreadsheet
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_startups.to_excel(writer, sheet_name="Startups", index=False)
            df_products.to_excel(writer, sheet_name="Products", index=False)
            df_papers.to_excel(writer, sheet_name="Research Papers", index=False)
            df_jobs.to_excel(writer, sheet_name="Jobs", index=False)
            df_news.to_excel(writer, sheet_name="News", index=False)
            df_mappings.to_excel(writer, sheet_name="Entity Mapping Log", index=False)

        # 3. Also export individual CSV files for straightforward Google Sheets upload
        df_startups.to_csv(OUTPUT_DIR / "1_startups.csv", index=False)
        df_products.to_csv(OUTPUT_DIR / "2_products.csv", index=False)
        df_papers.to_csv(OUTPUT_DIR / "3_research_papers.csv", index=False)
        df_jobs.to_csv(OUTPUT_DIR / "4_jobs.csv", index=False)
        df_news.to_csv(OUTPUT_DIR / "5_news.csv", index=False)
        df_mappings.to_csv(OUTPUT_DIR / "6_entity_mapping_log.csv", index=False)

        logger.info(
            f"Successfully exported data:\n"
            f"  - Startups: {len(df_startups)} rows\n"
            f"  - Products: {len(df_products)} rows\n"
            f"  - Research Papers: {len(df_papers)} rows\n"
            f"  - Jobs: {len(df_jobs)} rows\n"
            f"  - News: {len(df_news)} rows\n"
            f"  - Entity Mappings: {len(df_mappings)} rows"
        )
        return output_path
