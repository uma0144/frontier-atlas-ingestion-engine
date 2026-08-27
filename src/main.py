"""
Master Pipeline Orchestrator for GraphOne / FrontierAtlas Intelligence Ingestion Engine.
Coordinates massive bulk acquisition, real-time signal crawlers, entity resolution, and export.
"""

import asyncio
import argparse
import sys
import logging
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.crawlers.papers_crawler import PapersCrawler
from src.crawlers.startups_crawler import StartupsCrawler
from src.crawlers.products_crawler import ProductsCrawler
from src.crawlers.news_crawler import NewsCrawler
from src.crawlers.jobs_crawler import JobsCrawler
from src.resolver.entity_resolver import EntityResolver
from src.exporters.excel_exporter import ExcelExporter
from src.config import EXCEL_OUTPUT_PATH, TARGET_PAPERS_COUNT, TARGET_STARTUPS_COUNT, TARGET_PRODUCTS_COUNT

console = Console(legacy_windows=False, highlight=False)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PipelineRunner")


async def run_pipeline(
    papers_target: int = TARGET_PAPERS_COUNT,
    startups_target: int = TARGET_STARTUPS_COUNT,
    products_target: int = TARGET_PRODUCTS_COUNT,
    skip_bulk: bool = False
):
    start_time = datetime.now()
    console.print(Panel.fit(
        "[bold cyan]GraphOne / FrontierAtlas - AI Ingestion & Intelligence Graph Engine[/bold cyan]\n"
        "[dim]Production Ingestion Pipeline - Scalable - Fault-Tolerant - Zero-Hallucination[/dim]",
        border_style="cyan"
    ))

    resolver = EntityResolver()
    
    # Instantiate Crawlers
    papers_crawler = PapersCrawler()
    startups_crawler = StartupsCrawler()
    products_crawler = ProductsCrawler()
    news_crawler = NewsCrawler()
    jobs_crawler = JobsCrawler()

    papers = []
    startups = []
    products = []

    try:
        # ==========================================
        # Phase I: Massive Bulk Extraction
        # ==========================================
        if not skip_bulk:
            console.print("\n[bold yellow]=== Phase I: Executing Massive Bulk Data Acquisition ===[/bold yellow]")
            with console.status("[bold green]Crawling Research Papers, Startups, and Products concurrently..."):
                bulk_tasks = [
                    papers_crawler.crawl(target_count=papers_target),
                    startups_crawler.crawl(target_count=startups_target),
                    products_crawler.crawl(target_count=products_target)
                ]
                papers, startups, products = await asyncio.gather(*bulk_tasks)
            console.print(f"[green][OK] Acquired {len(papers)} Research Papers (with GitHub metrics)[/green]")
            console.print(f"[green][OK] Acquired {len(startups)} Startups[/green]")
            console.print(f"[green][OK] Acquired {len(products)} AI Products[/green]")
        else:
            console.print("[dim]Skipping bulk phase (--skip-bulk enabled)[/dim]")

        # ==========================================
        # Phase II: High-Fidelity Signal Ingestion (24h Freshness)
        # ==========================================
        console.print("\n[bold yellow]=== Phase II: Executing Fresh Signals Ingestion (<24h) ===[/bold yellow]")
        with console.status("[bold green]Crawling 5 AI News sources & 5 AI Job boards..."):
            signal_tasks = [
                news_crawler.crawl(),
                jobs_crawler.crawl()
            ]
            news, jobs = await asyncio.gather(*signal_tasks)
        console.print(f"[green][OK] Ingested {len(news)} strictly 24-hour fresh News articles[/green]")
        console.print(f"[green][OK] Ingested {len(jobs)} strictly 24-hour fresh Job postings[/green]")

        # ==========================================
        # Phase IV: Deterministic Entity Resolution
        # ==========================================
        console.print("\n[bold yellow]=== Phase IV: Running Deterministic Entity Resolution ===[/bold yellow]")
        with console.status("[bold green]Resolving entity names and standardizing canonical graph..."):
            # Resolve Startup Entities
            for s in startups:
                raw_name = s.content.entityName
                canonical, conf, method = resolver.resolve(raw_name, entity_type="STARTUP")
                s.content.entityName = canonical

            # Resolve Product Creators
            for p in products:
                raw_creator = p.content.startupName
                canonical, conf, method = resolver.resolve(raw_creator, entity_type="STARTUP")
                p.content.startupName = canonical

            # Resolve Job Companies
            for j in jobs:
                raw_co = j.content.company
                canonical, conf, method = resolver.resolve(raw_co, entity_type="COMPANY")
                j.content.company = canonical

        mapping_logs = resolver.get_audit_logs()
        console.print(f"[green][OK] Completed Entity Resolution. Logged {len(mapping_logs)} canonical audit records.[/green]")

        # ==========================================
        # Exporting to 6-Tab Workbook
        # ==========================================
        console.print("\n[bold yellow]=== Exporting Final Deliverable: 6-Tab Intelligence Workbook ===[/bold yellow]")
        output_file = ExcelExporter.export_all(
            startups=startups,
            products=products,
            papers=papers,
            jobs=jobs,
            news=news,
            mappings=mapping_logs,
            output_path=EXCEL_OUTPUT_PATH
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        # Summary Table
        table = Table(title="Pipeline Ingestion Metrics Summary", header_style="bold magenta")
        table.add_column("Vertical / Tab", style="cyan")
        table.add_column("Target Required", justify="right", style="dim")
        table.add_column("Collected Count", justify="right", style="bold green")
        table.add_column("Freshness / Verification", style="yellow")

        table.add_row("Startups", f">= {startups_target}", str(len(startups)), "YC & AI Ecosystem Verified")
        table.add_row("Products", f">= {products_target}", str(len(products)), "Pricing Models Parsed (FREE/FREEMIUM/etc)")
        table.add_row("Research Papers", f">= {papers_target}", str(len(papers)), "Live GitHub Stars & ArXiv Links")
        table.add_row("Jobs", "All Fresh", str(len(jobs)), "Strictly < 24 Hours")
        table.add_row("News", "All Fresh", str(len(news)), "Strictly < 24 Hours")
        table.add_row("Entity Mapping Log", "Audit Trail", str(len(mapping_logs)), "Fuzzy & Legal Suffix Resolved")

        console.print(table)
        console.print(f"\n[bold green][OK] All data exported successfully to:[/bold green] [bold underline]{output_file}[/bold underline]")
        console.print(f"[bold cyan]Total Pipeline Runtime: {elapsed:.2f} seconds[/bold cyan]\n")

    finally:
        # Clean shutdown of sessions
        await papers_crawler.close()
        await startups_crawler.close()
        await products_crawler.close()
        await news_crawler.close()
        await jobs_crawler.close()


def main():
    parser = argparse.ArgumentParser(description="GraphOne / FrontierAtlas Data Ingestion Engine")
    parser.add_argument("--papers", type=int, default=1000, help="Target count for research papers")
    parser.add_argument("--startups", type=int, default=1000, help="Target count for startups")
    parser.add_argument("--products", type=int, default=1000, help="Target count for products")
    parser.add_argument("--skip-bulk", action="store_true", help="Skip bulk acquisition and run only fresh signals")

    args = parser.parse_args()
    asyncio.run(run_pipeline(
        papers_target=args.papers,
        startups_target=args.startups,
        products_target=args.products,
        skip_bulk=args.skip_bulk
    ))


if __name__ == "__main__":
    main()
