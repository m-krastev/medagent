# MedAgent: Medical Diagnosis Swarm powered by Google ADK and Gemini

MedAgent is an advanced medical diagnosis assistant built with Google's Agent Development Kit (ADK) that leverages the power of Gemini models and LlamaIndex to provide accurate and efficient medical insights. This multi-agent system is designed to assist in understanding medical diagnostic workflows by coordinating specialized agents for triage, hypothesis generation, evidence gathering, imaging interpretation, and research consultation.

## Architecture

MedAgent uses ADK's multi-agent architecture with the following specialized agents:

- **Judge Agent (Root)**: Chief Medical Officer orchestrating the diagnostic process
- **Triage Agent**: Initial patient assessment and risk stratification
- **Hypothesis Agent**: Differential diagnosis generation using medical reasoning frameworks
- **Evidence Agent**: Laboratory test ordering and interpretation
- **Imaging Agent**: Radiology study ordering and report generation
- **Research Agent**: Medical literature consultation and final report synthesis

## Getting Started

### Prerequisites

- Python 3.10 or later
- Google API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Installation

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Download medical knowledge base
python scripts/ingest_data.py
# Set up evaluation cases
python scripts/setup_evaluation.py
```

### Running with ADK Web Interface

The recommended way to run MedAgent is using ADK's web interface:

```bash
# Run from the project root directory
adk web
```

## Features

- **Multi-Agent Architecture**: Built on Google ADK with specialized agents for each diagnostic function
- **Interactive Diagnostic Workflow**: Iterative evidence gathering and hypothesis refinement
- **RAG-Enhanced**: Medical literature consultation using LlamaIndex and ChromaDB
- **Simulated Clinical Tools**: Mock laboratory and imaging ordering systems for demonstration
- **Session State Management**: Maintains patient context across diagnostic iterations
- **Web & CLI Interfaces**: Run via ADK's web UI or traditional command-line interface

## Project Structure

```
medagent/
├── agent.py                 # Root agent entry point for ADK
├── agents/                  # ADK-compatible agent definitions
│   ├── judge/              # Root orchestrator (CMO)
│   ├── triage/             # Initial assessment
│   ├── hypothesis/         # Differential diagnosis
│   ├── evidence/           # Laboratory tests
│   ├── imaging/            # Radiology studies
│   └── research/           # Literature consultation
└── scripts/                # Utility scripts
```

## How It Works

1. **Patient Intake**: The judge agent collects demographics and chief complaint via the triage agent
2. **Hypothesis Generation**: Initial differential diagnosis is generated based on presenting symptoms
3. **Evidence Gathering**: Judge iteratively orders tests (labs/imaging) via specialist agents
4. **Hypothesis Refinement**: Differential diagnosis is updated as new evidence arrives
5. **Diagnosis Finalization**: When confidence threshold is reached, final diagnosis is determined
6. **Report Generation**: Research agent creates comprehensive physician handoff documentation

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Agents

To add a new specialist agent:

1. Create a new directory under `agents/`
2. Add `agent.py`, `prompt.py`, and optionally `tools.py`
3. Import and add to judge agent's `sub_agents` list

## Disclaimer

⚠️ **Not for clinical use. For research and educational purposes only.**

This system is a demonstration of multi-agent AI architecture applied to medical diagnostic workflows. It should not be used for actual medical diagnosis or patient care.
