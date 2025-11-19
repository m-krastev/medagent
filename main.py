import asyncio
import os
import logging
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from src.core.orchestrator import MedicalOrchestrator
from src.utils.logging_setup import setup_logging

# Setup Logger
setup_logging()
logger = logging.getLogger("Main")

app = typer.Typer()
console = Console()

async def run_diagnosis(complaint: str):
    """
    Runs the diagnostic loop for a given complaint.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        console.print("[bold red]❌ Error: GOOGLE_API_KEY environment variable required.[/bold red]")
        return

    # Check for RAG data
    if not os.path.exists("data/chroma_db"):
        console.print("[bold yellow]⚠️  RAG Database not found.[/bold yellow]")
        console.print("   Please run: [green]python scripts/ingest_data.py[/green]")
        return

    orchestrator = MedicalOrchestrator()
    
    console.print(Panel.fit(f"[bold blue]Processing Complaint:[/bold blue] {complaint}", title="🏥 MedAgent"))
    
    try:
        final_case = await orchestrator.run_diagnostic_loop(complaint)
        
        console.print("\n")
        console.rule("[bold green]FINAL MEDICAL REPORT[/bold green]")
        console.print(f"[bold]DIAGNOSIS:[/bold] {final_case.final_diagnosis}")
        console.print(Panel(Markdown(final_case.research_notes[-1] if final_case.research_notes else "No research notes available."), title="Physician Handoff"))
        console.print("\n[dim]DISCLAIMER: AI-generated content. Not professional medical advice.[/dim]")
        
    except Exception as e:
        logger.exception("System Crash")
        console.print(f"[bold red]System Error:[/bold red] {e}")

@app.command()
def run():
    """
    Interactive mode to enter patient complaints.
    """
    console.print(Panel.fit("[bold cyan]GOOGLE ADK ENTERPRISE MEDICAL SYSTEM v1.0[/bold cyan]", border_style="cyan"))
    
    complaint = typer.prompt("Enter Patient Complaint")
    if not complaint:
        complaint = "65M with high fever, productive cough, and chest pain."
        console.print(f"[dim]Using default: {complaint}[/dim]")
    
    asyncio.run(run_diagnosis(complaint))

@app.command()
def diagnose(complaint: str):
    """
    One-shot diagnosis for a specific complaint.
    """
    asyncio.run(run_diagnosis(complaint))

if __name__ == "__main__":
    app()
