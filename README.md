<div align="center">

<br/>

```
██████╗  █████╗ ██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
██████╔╝███████║██████╔╝█████╗  ██████╔╝█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
██║     ██║  ██║██║     ███████╗██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

**Paste an arXiv link. Get working code in 90 seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://pypi.org/project/paperforge-sdk)
[![PyPI](https://img.shields.io/pypi/v/paperforge-sdk.svg)](https://pypi.org/project/paperforge-sdk)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-teal)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://reactjs.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**PyPI**](https://pypi.org/project/paperforge-sdk) · [**API Docs**](http://localhost:8000/docs) · [**AutoViz AI**](https://autoviz-ai.vercel.app) · [**ModelPulse**](https://github.com/GPREETHAMSAXON/ModelPulse)

<br/>

> *"Paste an arXiv link. Get methodology, working code, and benchmark results — in 90 seconds."*

<br/>

</div>

---

## What is PaperForge?

PaperForge is an AI-powered research accelerator that converts ML papers from arXiv into actionable engineering assets. It reads the paper, extracts the methodology using Claude AI, generates a runnable Python implementation with paper section references, and benchmarks it against your own dataset — all in one click.

**No more spending 6 hours reverse-engineering a paper into code.**

```python
from paperforge import PaperForge

pf = PaperForge(base_url="http://localhost:8000")

# Analyze any arXiv paper
analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
print(analysis.key_algorithm)              # Transformer
print(analysis.implementation_difficulty)  # hard
print(analysis.reported_results)           # {'WMT 2014 EN-DE BLEU': '28.4'}

# Generate a Python implementation
code = pf.generate_from_analysis(analysis)
code.save("transformer_attention.py")

# Full pipeline in one call
result = pf.paper("https://arxiv.org/abs/1706.03762")
result.save_code("output/")
```

---

## Features

| Feature | Description |
|---|---|
| ⚡ **One-click pipeline** | URL in → methodology + code + benchmark out |
| 🧠 **Claude-powered extraction** | Structured JSON: algorithm, datasets, metrics, novelty, reproducibility |
| 🔀 **Smart code strategy** | Easy → full impl · Hard → core mechanism · Theory → documented skeleton |
| 📝 **Section-referenced code** | Comments like `# Section 3.2.2: Scaled dot-product attention` |
| 📊 **Benchmark on your data** | Upload a CSV, run against E2B cloud sandbox, compare vs paper results |
| 🖥️ **Monaco editor UI** | Syntax-highlighted code viewer with copy, download, and Usage/Limitations tabs |
| 🐍 **Python SDK** | `pip install paperforge-sdk` — full programmatic access |
| 🔬 **Works on any ML paper** | Tested on Transformer, BERT, LoRA, XGBoost, DDPM, and more |

---

## Architecture

```
paperforge/
├── app/                    # FastAPI backend
│   ├── api/routes/         # parse, analyze, generate, benchmark endpoints
│   ├── services/           # parser, analyzer, generator, benchmarker, sandbox
│   ├── models/             # Pydantic schemas
│   └── utils/              # ArXiv URL parsing, text cleaning
├── frontend/               # React dashboard
│   └── src/
│       ├── components/     # AnalysisPanel, CodePanel, BenchmarkPanel, ...
│       └── hooks/          # usePaperForge — full pipeline state machine
├── paperforge-sdk/         # Python SDK (PyPI)
│   └── paperforge/
│       ├── client.py       # PaperForge class
│       ├── models.py       # PaperAnalysis, GeneratedCode, BenchmarkResult
│       └── exceptions.py   # exception hierarchy
└── tests/                  # 53 tests passing
```

### Pipeline

```
ArXiv URL / PDF Upload
        │
        ▼
  PyMuPDF Parser ──────────────────► Parsed text + metadata
        │
        ▼
  Claude Sonnet (Call 1)
  Methodology extraction ──────────► PaperAnalysis JSON
        │                            title, algorithm, datasets,
        │                            metrics, results, difficulty
        ▼
  Claude Sonnet (Call 2)
  Code generation ─────────────────► GeneratedCode
        │                            strategy: full / core / skeleton
        │                            section-referenced Python
        ▼
  E2B Cloud Sandbox ───────────────► BenchmarkResult
        │                            metrics vs paper
        ▼                            Claude interpretation
  React Dashboard
  Monaco Editor + Charts
```

---

## Tech Stack

### Backend (`app/`)
- **Framework:** FastAPI + Uvicorn
- **PDF Parsing:** PyMuPDF (fitz)
- **AI:** Anthropic Claude Sonnet (`claude-sonnet-4-20250514`)
- **Sandbox:** E2B Code Interpreter (safe cloud execution)
- **HTTP Client:** httpx with tenacity retry

### Frontend (`frontend/`)
- **Framework:** React 18 + Create React App
- **Code Editor:** Monaco Editor (`@monaco-editor/react`)
- **Styling:** Tailwind CSS v3 + custom design system
- **HTTP:** Axios

### Python SDK (`paperforge-sdk/`)
- **Dependencies:** `httpx` only
- **Models:** Full dataclass hierarchy with properties
- **Compatible:** Python 3.10+

---

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))
- E2B API key ([e2b.dev](https://e2b.dev)) — optional, for benchmark feature

### 1. Clone and install

```bash
git clone https://github.com/GPREETHAMSAXON/PaperForge.git
cd PaperForge
```

Install backend dependencies:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
E2B_API_KEY=e2b_...              # optional — for benchmark feature
ENVIRONMENT=development
```

### 3. Start both servers

**Terminal 1 — Backend:**
```bash
cd PaperForge
venv\Scripts\activate
uvicorn app.main:app --reload
# PaperForge API running on http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
cd PaperForge/frontend
npm start
# React app running on http://localhost:3000
```

---

## API Reference

All endpoints are documented interactively at `/docs` (Swagger UI).

### Parse — fast, no Claude call

```
POST   /api/v1/parse/arxiv        Fetch and parse paper from arXiv
POST   /api/v1/parse/upload       Parse an uploaded PDF
```

### Analyze — methodology extraction

```
POST   /api/v1/analyze/arxiv      Parse + Claude methodology extraction
POST   /api/v1/analyze/upload     Upload PDF + analyze
```

### Generate — code generation

```
POST   /api/v1/generate/arxiv          Full pipeline: parse → analyze → generate
POST   /api/v1/generate/from-analysis  Generate from existing analysis (faster)
POST   /api/v1/generate/upload         Upload PDF + generate
```

### Benchmark — run against your data

```
POST   /api/v1/benchmark/run      Run generated code against CSV in E2B sandbox
```

### Example response (`/api/v1/analyze/arxiv`)

```json
{
  "success": true,
  "arxiv_id": "1706.03762",
  "tokens_used": 12868,
  "analysis": {
    "title": "Attention Is All You Need",
    "key_algorithm": "Transformer",
    "implementation_difficulty": "hard",
    "datasets_used": ["WMT 2014 English-German", "WMT 2014 English-French"],
    "evaluation_metrics": ["BLEU"],
    "reported_results": { "WMT 2014 EN-DE BLEU": "28.4" },
    "dependencies": ["torch", "numpy"],
    "is_implementable": true
  }
}
```

---

## Python SDK

### Installation

```bash
pip install paperforge-sdk
```

### Usage

```python
from paperforge import PaperForge

pf = PaperForge(base_url="http://localhost:8000")

# Analyze
analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
print(analysis.key_algorithm)   # Transformer
print(analysis.is_hard)         # True

# Generate
code = pf.generate_from_analysis(analysis)
code.save("output/")            # saves as paperforge_implementation.py

# Full pipeline
result = pf.paper("https://arxiv.org/abs/1603.02754")
print(result.total_tokens)      # 14,968

# Benchmark
bench = pf.benchmark("data/iris.csv", analysis, code)
print(bench.status)             # success
print(bench.interpretation)     # Claude's plain-English analysis
for m in bench.metrics:
    print(m.name, m.your_value, m.gap_pct)
```

### Error handling

```python
from paperforge.exceptions import (
    PaperNotFoundError, TimeoutError, ConnectionError, APIError
)

try:
    analysis = pf.analyze("1706.03762")
except PaperNotFoundError:
    print("Paper not found on arXiv")
except TimeoutError:
    print("Try increasing timeout — Claude calls take 40-90s")
except ConnectionError:
    print("Is the PaperForge server running?")
```

---

## Code Generation Strategies

PaperForge automatically selects a strategy based on the paper:

| Strategy | When | What you get |
|---|---|---|
| `full` | Easy / medium papers | Complete runnable implementation |
| `core` | Hard papers (Transformer, BERT) | Core mechanism only — e.g. attention without training loop |
| `skeleton` | Theory / survey papers | Documented stubs with detailed docstrings |

Generated code always includes:
- Comments referencing specific paper sections (`# Section 3.2.1`)
- A `run_<algorithm>(df)` entry point
- A `if __name__ == "__main__":` smoke test

---

## Benchmark Feature

Upload a CSV dataset and PaperForge will:

1. Run the generated code against your data in an E2B cloud sandbox
2. Extract metrics (accuracy, F1, RMSE, etc.)
3. Compare to paper-reported results
4. Return Claude's plain-English interpretation

```
Your dataset: 15 rows · 5 cols · 6,690ms execution

METRICS VS PAPER
  base_score    100.0%   ████████████████████
  n_trees       11.0     ████

CLAUDE'S ANALYSIS
Your 15-row dataset is vastly smaller than the paper's 1.7 billion
examples. Consider testing on a dataset with at least 10,000+ samples
to better leverage XGBoost's scalability benefits.
```

> Note: Benchmark works best with sklearn/numpy papers. PyTorch-heavy papers
> (Transformer, BERT, LoRA) require GPU infrastructure not available in the sandbox.

---

## Tests

```bash
python -m pytest tests/ --ignore=tests/test_validation.py -v
# 53 passed
```

To run real paper validation (makes actual API calls):

```bash
set RUN_VALIDATION=1
python -m pytest tests/test_validation.py -v --timeout=120
```

---

## Roadmap

- [ ] Deployment on Render + Vercel (live public URL)
- [ ] Paper history — save and revisit past analyses
- [ ] Paper comparison — A vs B side by side
- [ ] Hugging Face dataset auto-connect
- [ ] Export PDF report
- [ ] GitHub Actions CI/CD pipeline
- [ ] Auth + user accounts (Supabase)

---

## Built by

**Saxon Preetham**  
B.Tech CSE · Vignan's Institute of Information Technology, Visakhapatnam  
Vice Chairperson, IEEE Student Branch · CGPA 9.03  
GitHub: [@GPREETHAMSAXON](https://github.com/GPREETHAMSAXON)

---

## Related Projects

- [**ModelPulse**](https://github.com/GPREETHAMSAXON/ModelPulse) — ML model monitoring SaaS
- [**AutoViz AI**](https://autoviz-ai.vercel.app) — AI-powered data analytics platform

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**If PaperForge saved you 6 hours of paper-to-code work, give it a ⭐**

</div>
