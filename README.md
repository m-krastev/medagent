# MedAgent: Medical Diagnosis Swarm powered by Gemini and LlamaIndex

MedAgent is an advanced medical diagnosis assistant that leverages the power of Google's Gemini model and LlamaIndex to provide accurate and efficient medical insights. This project is designed to assist healthcare professionals in diagnosing medical conditions by analyzing patient data and medical literature.

## Getting Started

```bash
uv venv
source .venv/bin/activate
uv pip install -e .

# Set up environment variables
echo "GOOGLE_API_KEY=your_google_api_key" >> .env

# Download medical database
python scripts/ingest_data.py

# Run the MedAgent application
medagent run
```

## Features

- Several specialized agents orchestrated to provide comprehensive medical diagnosis support.
- Integration with Google's Gemini model for advanced natural language processing.
- Utilization of LlamaIndex for efficient data indexing and retrieval.
- User-friendly interface for easy interaction with the diagnosis assistant.

\* Not for clinical use. For research purposes only.
