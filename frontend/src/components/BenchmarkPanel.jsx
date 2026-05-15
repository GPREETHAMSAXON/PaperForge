import React, { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const STATUS_CONFIG = {
  success: { label: 'Success', color: 'text-forge-success', bg: 'bg-forge-success/10 border-forge-success/30' },
  partial: { label: 'Partial', color: 'text-forge-warning', bg: 'bg-forge-warning/10 border-forge-warning/30' },
  error:   { label: 'Error',   color: 'text-forge-danger',  bg: 'bg-forge-danger/10  border-forge-danger/30'  },
  timeout: { label: 'Timeout', color: 'text-forge-warning', bg: 'bg-forge-warning/10 border-forge-warning/30' },
};

export default function BenchmarkPanel({ analysis, generatedCode, paperMeta }) {
  const [stage, setStage] = useState('idle'); // idle | uploading | running | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const fileRef = useRef(null);

  if (!analysis || !generatedCode) return null;

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      setCsvFile(file);
      setError(null);
    } else {
      setError('Please select a CSV file.');
    }
  };

  const handleRun = async () => {
    if (!csvFile) { setError('Please upload a CSV file first.'); return; }

    try {
      setStage('running');
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append('csv_file', csvFile);
      formData.append('analysis_json', JSON.stringify(analysis));
      formData.append('generated_code', generatedCode.code);
      formData.append('arxiv_id', paperMeta?.arxiv_id || '');
      formData.append('paper_title', analysis.title);
      formData.append('key_algorithm', analysis.key_algorithm);

      const resp = await axios.post(`${API_BASE}/api/v1/benchmark/run`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 90000,
      });

      setResult(resp.data.benchmark);
      setStage('done');
    } catch (err) {
      setStage('error');
      setError(err?.response?.data?.detail || 'Benchmark failed. Check that E2B_API_KEY is set.');
    }
  };

  const statusCfg = result ? STATUS_CONFIG[result.status] : null;

  return (
    <div className="mt-6 animate-slide-up">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-mono text-forge-subtle uppercase tracking-widest">Benchmark</h2>
        <span className="text-xs font-mono text-forge-subtle/60">Run against your dataset</span>
      </div>

      <div className="p-5 rounded-xl bg-forge-surface glow-border space-y-4">
        {/* Upload area */}
        <div>
          <p className="text-sm text-forge-subtle mb-3">
            Upload your CSV dataset to benchmark the generated code against paper-reported results.
          </p>

          <div
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
              csvFile
                ? 'border-forge-success/50 bg-forge-success/5'
                : 'border-forge-border hover:border-forge-muted'
            }`}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            {csvFile ? (
              <div>
                <div className="text-forge-success text-2xl mb-1">✓</div>
                <p className="text-sm font-mono text-forge-text">{csvFile.name}</p>
                <p className="text-xs text-forge-subtle mt-1">
                  {(csvFile.size / 1024).toFixed(1)} KB · Click to change
                </p>
              </div>
            ) : (
              <div>
                <div className="text-forge-subtle text-2xl mb-2">↑</div>
                <p className="text-sm text-forge-subtle">Click to upload CSV</p>
                <p className="text-xs text-forge-subtle/60 mt-1">Max 5MB · must have a header row</p>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 rounded-lg bg-forge-danger/5 border border-forge-danger/30">
            <p className="text-xs font-mono text-forge-danger">{error}</p>
          </div>
        )}

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={!csvFile || stage === 'running'}
          className="w-full py-2.5 rounded-lg bg-forge-accent text-white text-sm font-mono
                     hover:bg-forge-accent-bright transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed
                     shadow-lg shadow-forge-accent/20"
        >
          {stage === 'running' ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
                <path d="M12 2a10 10 0 010 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              Running in E2B sandbox...
            </span>
          ) : '▶ Run Benchmark'}
        </button>

        {/* Results */}
        {result && statusCfg && (
          <div className="space-y-4 animate-fade-in">
            {/* Status + timing */}
            <div className={`flex items-center justify-between p-3 rounded-lg border ${statusCfg.bg}`}>
              <span className={`text-sm font-mono font-500 ${statusCfg.color}`}>
                {statusCfg.label}
              </span>
              <div className="text-right text-xs font-mono text-forge-subtle">
                <div>{result.dataset_rows} rows · {result.dataset_cols} cols</div>
                <div>{result.execution_time_ms}ms</div>
              </div>
            </div>

            {/* Error message */}
            {result.error_message && (
              <div className="p-3 rounded-lg bg-forge-danger/5 border border-forge-danger/30">
                <p className="text-xs font-mono text-forge-danger">{result.error_message}</p>
                {result.stderr && (
                  <pre className="text-xs text-forge-subtle mt-2 overflow-auto max-h-24">
                    {result.stderr}
                  </pre>
                )}
              </div>
            )}

            {/* Metrics */}
            {result.metrics?.length > 0 && (
              <div>
                <h4 className="text-xs font-mono text-forge-subtle uppercase tracking-widest mb-3">
                  Metrics vs Paper
                </h4>
                <div className="space-y-3">
                  {result.metrics.map((m) => (
                    <MetricRow key={m.name} metric={m} />
                  ))}
                </div>
              </div>
            )}

            {/* Interpretation */}
            {result.interpretation && (
              <div className="p-3 rounded-lg bg-forge-accent/5 border border-forge-accent/20">
                <p className="text-xs font-mono text-forge-subtle uppercase tracking-widest mb-1">
                  Claude's Analysis
                </p>
                <p className="text-sm text-forge-text leading-relaxed">{result.interpretation}</p>
              </div>
            )}

            {/* Stdout preview */}
            {result.stdout && result.status === 'success' && (
              <details className="group">
                <summary className="text-xs font-mono text-forge-subtle cursor-pointer hover:text-forge-text">
                  Show output ▸
                </summary>
                <pre className="mt-2 text-xs font-mono text-forge-subtle bg-forge-bg rounded-lg p-3 overflow-auto max-h-40">
                  {result.stdout}
                </pre>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricRow({ metric }) {
  const hasGap = metric.gap_pct !== null && metric.gap_pct !== undefined;
  const isPositive = hasGap && metric.gap_pct >= 0;
  const gapColor = isPositive ? 'text-forge-success' : 'text-forge-danger';

  // Bar width relative to paper value (capped 0-120%)
  const paperNum = metric.paper_value ? parseFloat(metric.paper_value) : null;
  const yourPct = metric.your_value !== null ? Math.min(120, Math.round(metric.your_value * 100)) : null;
  const paperPct = paperNum ? Math.min(100, Math.round(paperNum)) : null;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-forge-subtle">{metric.name}</span>
        <div className="flex items-center gap-3">
          {metric.your_value !== null && (
            <span className="text-forge-text font-500">
              {(metric.your_value * (metric.your_value <= 1 ? 100 : 1)).toFixed(1)}
              {metric.your_value <= 1 ? '%' : ''}
            </span>
          )}
          {metric.paper_value && (
            <span className="text-forge-subtle">paper: {metric.paper_value}</span>
          )}
          {hasGap && (
            <span className={`${gapColor} font-500`}>
              {isPositive ? '+' : ''}{metric.gap_pct}%
            </span>
          )}
        </div>
      </div>
      {/* Progress bars */}
      {yourPct !== null && (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-forge-subtle w-8">Yours</span>
            <div className="flex-1 h-1.5 bg-forge-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-forge-accent rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, yourPct)}%` }}
              />
            </div>
          </div>
          {paperPct !== null && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-forge-subtle w-8">Paper</span>
              <div className="flex-1 h-1.5 bg-forge-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-forge-subtle rounded-full transition-all duration-700"
                  style={{ width: `${Math.min(100, paperPct)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
