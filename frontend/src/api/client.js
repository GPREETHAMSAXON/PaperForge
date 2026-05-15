import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min — Claude calls can take 40-90s
  headers: { 'Content-Type': 'application/json' },
});

export const api = {
  // Parse only — fast, no Claude call
  parseArxiv: (url) =>
    client.post('/api/v1/parse/arxiv', { url }),

  // Analyze — parse + Claude methodology extraction
  analyzeArxiv: (url) =>
    client.post('/api/v1/analyze/arxiv', { url }),

  // Generate — parse + analyze + code generation
  generateArxiv: (url, includeSandbox = false) =>
    client.post('/api/v1/generate/arxiv', {
      url,
      include_sandbox_test: includeSandbox,
    }),

  // Generate from existing analysis (skip re-parsing)
  generateFromAnalysis: (arxivId, analysis, includeSandbox = false) =>
    client.post('/api/v1/generate/from-analysis', {
      arxiv_id: arxivId,
      analysis,
      include_sandbox_test: includeSandbox,
    }),

  // Health check
  health: () => client.get('/health'),
};

export default client;
