import asyncio
import os
import logging
import typer
import warnings
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from src.core.orchestrator import MedicalOrchestrator
from src.utils.logging_setup import setup_logging

# Suppress asyncio unclosed resource warnings (aiohttp cleanup)
warnings.filterwarnings("ignore", category=ResourceWarning)

# Setup Logger
setup_logging()
logger = logging.getLogger("Main")

app = typer.Typer()
console = Console()

async def run_diagnosis(show_logs: bool = False):
    """
    Runs the diagnostic loop with interactive demographic and complaint collection.
    """
    if not show_logs:
        logging.getLogger().setLevel(logging.CRITICAL)
    
    if not os.environ.get("GOOGLE_API_KEY"):
        console.print("[bold red]❌ Error: GOOGLE_API_KEY environment variable required.[/bold red]")
        return

    # Check for RAG data
    if not os.path.exists("data/chroma_db"):
        console.print("[bold yellow]⚠️  RAG Database not found.[/bold yellow]")
        console.print("   Please run: [green]python scripts/ingest_data.py[/green]")
        return

    orchestrator = MedicalOrchestrator()
    
    console.print(Panel.fit("[bold blue]Medical Diagnostic System[/bold blue]", title="🏥 MedAgent"))
    
    try:
        final_case = await orchestrator.run_diagnostic_loop()
        
        console.print("\n")
        console.rule("[bold green]FINAL MEDICAL REPORT[/bold green]")
        console.print(f"[bold]DIAGNOSIS:[/bold] {final_case.final_diagnosis}")
        console.print(Panel(Markdown(final_case.research_notes[-1] if final_case.research_notes else "No research notes available."), title="Physician Handoff"))
        console.print("\n[dim]DISCLAIMER: AI-generated content. Not professional medical advice.[/dim]")
        
    except Exception as e:
        logger.exception("System Crash")
        console.print(f"[bold red]System Error:[/bold red] {e}")

@app.command()
def run(show_logs: bool = typer.Option(False, "--show-logs", help="Show log output")):
    """
    Interactive mode with demographic and complaint collection.
    """
    console.print(Panel.fit("[bold cyan]GOOGLE ADK ENTERPRISE MEDICAL SYSTEM v1.0[/bold cyan]", border_style="cyan"))
    asyncio.run(run_diagnosis(show_logs=show_logs))

@app.command()
def diagnose(complaint: str, show_logs: bool = typer.Option(False, "--show-logs", help="Show log output")):
    """
    One-shot diagnosis for a specific complaint (legacy - not used with new flow).
    """
    console.print("[bold yellow]⚠️  Note: Using interactive flow. Complaint parameter ignored.[/bold yellow]")
    asyncio.run(run_diagnosis(show_logs=show_logs))

if __name__ == "__main__":
    app()
