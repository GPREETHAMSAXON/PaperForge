# PaperForge

**Paste an ArXiv link. Get working code, methodology breakdown, and benchmark results.**

PaperForge is an AI-powered research accelerator that converts ML papers into actionable engineering assets — in seconds, not hours.

---

## What it does

| Input | Output |
|---|---|
| ArXiv URL or PDF | Structured methodology extraction |
| Paper full text | Runnable Python implementation |
| Your dataset (CSV) | Benchmark results vs paper-reported numbers |
| — | Exportable PDF report |

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **AI**: Claude API (`claude-sonnet-4-20250514`) via Anthropic SDK
- **PDF Parsing**: PyMuPDF (fitz)
- **Database**: Supabase (PostgreSQL)
- **Code Sandbox**: E2B (coming in v0.2)
- **Frontend**: React + Tailwind (coming in v0.3)

## Quickstart

```bash
git clone https://github.com/GPREETHAMSAXON/paperforge
cd paperforge

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Fill in ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

## API Endpoints

### Health
```
GET /health
```

### Parse — extract metadata only (fast, no Claude call)
```
POST /api/v1/parse/arxiv
{ "url": "https://arxiv.org/abs/2301.07041" }

POST /api/v1/parse/upload
multipart/form-data: file=<pdf>
```

### Analyze — full pipeline with Claude methodology extraction
```
POST /api/v1/analyze/arxiv
{ "url": "https://arxiv.org/abs/2301.07041" }

POST /api/v1/analyze/upload
multipart/form-data: file=<pdf>
```

### Example response (`/analyze/arxiv`)

```json
{
  "success": true,
  "arxiv_id": "1706.03762",
  "tokens_used": 3847,
  "analysis": {
    "title": "Attention Is All You Need",
    "problem_statement": "RNNs process sequences sequentially, limiting parallelization.",
    "proposed_method": "The Transformer relies entirely on attention mechanisms...",
    "key_algorithm": "Transformer",
    "novelty": "First architecture without recurrence or convolutions.",
    "datasets_used": ["WMT 2014 English-German", "WMT 2014 English-French"],
    "evaluation_metrics": ["BLEU"],
    "reported_results": { "BLEU EN-DE": "28.4" },
    "implementation_difficulty": "medium",
    "dependencies": ["torch", "numpy"],
    "reproducibility_notes": "Full hyperparameters in Appendix A.",
    "paper_type": "empirical",
    "is_implementable": true
  }
}
```

## Running Tests

```bash
pytest tests/ -v
```

61 tests, all passing.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | From console.anthropic.com |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `ENVIRONMENT` | No | `development` or `production` |
| `CLAUDE_MODEL` | No | Default: `claude-sonnet-4-20250514` |
| `MAX_PDF_SIZE_MB` | No | Default: 20 |

## Roadmap

- [x] v0.1 — Parse + analyze pipeline (ArXiv + PDF upload)
- [ ] v0.2 — Code generation endpoint + E2B sandbox execution
- [ ] v0.3 — React dashboard with Monaco code editor
- [ ] v0.4 — Benchmark against user dataset + chart output
- [ ] v0.5 — PDF report export + paper history

## Author

Saxon — B.Tech CSE, Vignan's Institute of Information Technology  
GitHub: [@GPREETHAMSAXON](https://github.com/GPREETHAMSAXON)
