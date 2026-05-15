# PaperForge SDK

**Convert arXiv research papers into runnable Python implementations — in seconds.**

[![PyPI version](https://img.shields.io/pypi/v/paperforge.svg)](https://pypi.org/project/paperforge/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PaperForge reads an arXiv paper, extracts the methodology using Claude AI, and generates a working Python implementation — complete with section references, usage examples, and honest limitations.

---

## Installation

```bash
pip install paperforge
```

---

## Quick Start

```python
from paperforge import PaperForge

pf = PaperForge(base_url="http://localhost:8000")  # or your deployed URL

# Analyze a paper
analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
print(analysis.key_algorithm)              # Transformer
print(analysis.implementation_difficulty)  # hard
print(analysis.reported_results)           # {'WMT 2014 EN-DE BLEU': '28.4'}

# Generate a Python implementation
code = pf.generate("https://arxiv.org/abs/1706.03762")
print(code.strategy)        # core  (hard papers get core mechanism only)
print(code.estimated_lines) # 67
code.save("transformer.py") # save to disk

# Full pipeline in one call
result = pf.paper("https://arxiv.org/abs/1706.03762")
result.save_code("output/")
print(f"Used {result.total_tokens:,} tokens")
```

---

## Features

| Feature | Description |
|---|---|
| **Paper analysis** | Extracts algorithm, datasets, metrics, novelty, reproducibility notes |
| **Code generation** | Generates runnable Python with paper section references |
| **Smart strategy** | Easy → full impl · Hard → core mechanism · Non-implementable → skeleton |
| **PDF upload** | Works with local PDFs, not just arXiv |
| **Benchmarking** | Run generated code against your CSV dataset via E2B sandbox |
| **Type-safe** | Full dataclass models with properties and methods |

---

## API Reference

### `PaperForge(base_url, timeout)`

Main client class.

```python
# Against local dev server
pf = PaperForge(base_url="http://localhost:8000")

# Against deployed API
pf = PaperForge(base_url="https://paperforge.onrender.com")

# As context manager (auto-closes HTTP client)
with PaperForge(base_url="http://localhost:8000") as pf:
    analysis = pf.analyze("1706.03762")
```

---

### `pf.analyze(url)` → `PaperAnalysis`

Fetch and analyze any arXiv paper.

```python
analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
# or bare ID:
analysis = pf.analyze("1706.03762")

print(analysis.title)                    # "Attention Is All You Need"
print(analysis.key_algorithm)            # "Transformer"
print(analysis.implementation_difficulty) # "hard"
print(analysis.is_hard)                  # True
print(analysis.datasets_used)           # ["WMT 2014 English-German", ...]
print(analysis.evaluation_metrics)      # ["BLEU"]
print(analysis.reported_results)        # {"WMT 2014 EN-DE BLEU": "28.4"}
print(analysis.dependencies)            # ["torch", "numpy"]
print(analysis.reproducibility_notes)   # "Full hyperparameters in appendix..."
print(analysis.tokens_used)             # 12868
```

**`PaperAnalysis` properties:**
- `.is_hard` — True if difficulty is "hard"
- `.is_easy` — True if difficulty is "easy"

---

### `pf.generate(url)` → `GeneratedCode`

Generate a Python implementation from an arXiv paper.

```python
code = pf.generate("https://arxiv.org/abs/1603.02754")

print(code.strategy)          # "full"  (XGBoost is medium difficulty)
print(code.estimated_lines)   # 85
print(code.explanation)       # "Implements XGBoost gradient boosting..."
print(code.install_command)   # "pip install sklearn numpy"
print(code.limitations)       # "No distributed training, no GPU support..."
print(code.code)              # Full Python source code

# Save to file
code.save("xgboost_impl.py")          # saves to file
code.save("output/")                   # saves as paperforge_implementation.py
code.print_usage()                     # prints usage example to stdout
```

**Generation strategies:**
- `"full"` — complete implementation (easy/medium papers)
- `"core"` — core mechanism only (hard papers like Transformer, BERT)
- `"skeleton"` — documented stubs (non-implementable or theory papers)

---

### `pf.generate_from_analysis(analysis)` → `GeneratedCode`

Skip re-parsing when you already have an analysis.

```python
analysis = pf.analyze("1706.03762")
# Regenerate without fetching the paper again:
code = pf.generate_from_analysis(analysis)
```

---

### `pf.paper(url)` → `PaperResult`

Full pipeline: analyze + generate in one call.

```python
result = pf.paper("https://arxiv.org/abs/1706.03762")

print(result.arxiv_id)                    # "1706.03762"
print(result.analysis.key_algorithm)      # "Transformer"
print(result.code.strategy)               # "core"
print(result.total_tokens)                # 14968

result.save_code("output/")               # save generated code
result.save_code("transformer_impl.py")   # save to specific file
```

---

### `pf.analyze_pdf(path)` → `PaperAnalysis`

Analyze a local PDF file.

```python
analysis = pf.analyze_pdf("papers/my_paper.pdf")
print(analysis.title)
```

---

### `pf.benchmark(csv_path, analysis, code)` → `BenchmarkResult`

Run generated code against your dataset in an E2B cloud sandbox.

> Requires `E2B_API_KEY` configured on the server.

```python
analysis = pf.analyze("https://arxiv.org/abs/1603.02754")
code = pf.generate_from_analysis(analysis)
result = pf.benchmark("data/iris.csv", analysis, code)

print(result.status)          # "success"
print(result.dataset_rows)    # 150
print(result.interpretation)  # Claude's plain-English analysis
print(result.execution_time_ms) # 6690

for metric in result.metrics:
    print(metric.name, metric.your_value, metric.paper_value, metric.gap_pct)
    print(metric.beat_paper)  # True/False/None
```

---

## Error Handling

```python
from paperforge import PaperForge
from paperforge.exceptions import (
    PaperNotFoundError,
    InvalidArxivURLError,
    TimeoutError,
    ConnectionError,
    APIError,
)

pf = PaperForge(base_url="http://localhost:8000")

try:
    analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
except PaperNotFoundError:
    print("Paper not found on arXiv — check the ID")
except InvalidArxivURLError:
    print("Invalid arXiv URL format")
except TimeoutError:
    print("Request timed out — try increasing timeout parameter")
except ConnectionError:
    print("Cannot connect to PaperForge API — is the server running?")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

---

## Self-Hosting

The SDK points to any PaperForge API instance. To run locally:

```bash
# Clone the PaperForge backend
git clone https://github.com/GPREETHAMSAXON/PaperForge
cd PaperForge

# Install and configure
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

# Start the server
uvicorn app.main:app --reload
```

Then use the SDK:

```python
pf = PaperForge(base_url="http://localhost:8000")
```

---

## Examples

```bash
# Run the quickstart example (requires local server running)
python examples/quickstart.py
```

---

## License

MIT © [Saxon](https://github.com/GPREETHAMSAXON)

---

## Related

- [PaperForge Web App](https://github.com/GPREETHAMSAXON/PaperForge) — the full-stack product
- [AutoViz AI](https://autoviz-ai.vercel.app) — data analytics platform
- [ModelPulse](https://github.com/GPREETHAMSAXON/ModelPulse) — ML model monitoring
