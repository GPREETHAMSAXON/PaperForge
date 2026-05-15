"""
PaperForge SDK — Quickstart Examples

Run against a local server:
    uvicorn app.main:app --reload  (in your PaperForge backend folder)
    python examples/quickstart.py
"""
from paperforge import PaperForge

# Point to local dev server
pf = PaperForge(base_url="http://localhost:8000")

print("=" * 60)
print("PaperForge SDK Quickstart")
print("=" * 60)

# ── Example 1: Health check ────────────────────────────────────────────────
print("\n1. Health check")
health = pf.health()
print(f"   Status: {health['status']} | Version: {health['version']}")

# ── Example 2: Analyze a paper ─────────────────────────────────────────────
print("\n2. Analyzing 'Attention Is All You Need'...")
analysis = pf.analyze("https://arxiv.org/abs/1706.03762")
print(f"   Title:      {analysis.title}")
print(f"   Algorithm:  {analysis.key_algorithm}")
print(f"   Difficulty: {analysis.implementation_difficulty}")
print(f"   Datasets:   {', '.join(analysis.datasets_used[:2])}")
print(f"   Results:    {list(analysis.reported_results.items())[:2]}")
print(f"   Tokens:     {analysis.tokens_used:,}")

# ── Example 3: Generate code ───────────────────────────────────────────────
print("\n3. Generating implementation (skipping re-parse)...")
code = pf.generate_from_analysis(analysis)
print(f"   Strategy:  {code.strategy}")
print(f"   Lines:     {code.estimated_lines}")
print(f"   Install:   {code.install_command}")
print(f"   Tokens:    {code.tokens_used:,}")

# Save to file
saved = code.save("output/transformer_attention.py")
print(f"   Saved to:  {saved}")

# ── Example 4: Full pipeline ───────────────────────────────────────────────
print("\n4. Full pipeline — XGBoost paper...")
result = pf.paper("https://arxiv.org/abs/1603.02754")
print(f"   {result}")
print(f"   Algorithm:     {result.analysis.key_algorithm}")
print(f"   Strategy:      {result.code.strategy}")
print(f"   Total tokens:  {result.total_tokens:,}")
result.save_code("output/")
print(f"   Code saved to: output/")

print("\n" + "=" * 60)
print("Done! Check the output/ folder for generated .py files.")
print("=" * 60)
