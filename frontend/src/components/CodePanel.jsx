import React, { useState } from 'react';
import Editor from '@monaco-editor/react';

const MONACO_OPTIONS = {
  readOnly: true,
  minimap: { enabled: false },
  fontSize: 13,
  lineHeight: 22,
  fontFamily: '"JetBrains Mono", "Fira Code", monospace',
  fontLigatures: true,
  padding: { top: 16, bottom: 16 },
  scrollBeyondLastLine: false,
  renderLineHighlight: 'none',
  overviewRulerLanes: 0,
  hideCursorInOverviewRuler: true,
  scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
  lineNumbers: 'on',
  glyphMargin: false,
  folding: false,
  contextmenu: false,
};

const STRATEGY_META = {
  full:     { label: 'Full Implementation', desc: 'Complete algorithm implementation' },
  core:     { label: 'Core Mechanism',      desc: 'Central operation only — not full pipeline' },
  skeleton: { label: 'Documented Skeleton', desc: 'Stubs with detailed docstrings' },
};

export default function CodePanel({ generatedCode, onRegenerate, isRegenerating }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('code'); // 'code' | 'usage' | 'limits'

  if (!generatedCode) return null;

  const stratMeta = STRATEGY_META[generatedCode.strategy] || STRATEGY_META.full;
  const stratBadgeClass = `badge-${generatedCode.strategy}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(generatedCode.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([generatedCode.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'paperforge_implementation.py';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-4 animate-slide-up">
      {/* Header card */}
      <div className="p-4 rounded-xl bg-forge-surface glow-border">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-mono ${stratBadgeClass}`}>
              {stratMeta.label}
            </span>
            <p className="text-xs text-forge-subtle mt-2">{stratMeta.desc}</p>
          </div>
          <div className="text-right shrink-0">
            <div className="text-xs font-mono text-forge-subtle">
              {generatedCode.estimated_lines} lines
            </div>
            <div className="text-xs font-mono text-forge-subtle mt-0.5">
              {generatedCode.install_command}
            </div>
          </div>
        </div>
        <p className="text-sm text-forge-text leading-relaxed">{generatedCode.explanation}</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-forge-surface rounded-lg p-1 glow-border">
        {[
          { id: 'code',   label: 'Implementation' },
          { id: 'usage',  label: 'Usage Example' },
          { id: 'limits', label: 'Limitations' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-1.5 text-xs font-mono rounded-md transition-all ${
              activeTab === tab.id
                ? 'bg-forge-accent text-white shadow-lg shadow-forge-accent/20'
                : 'text-forge-subtle hover:text-forge-text'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Code editor */}
      {activeTab === 'code' && (
        <div className="rounded-xl overflow-hidden border border-forge-border animate-fade-in" style={{ height: '460px' }}>
          <div className="flex items-center justify-between px-4 py-2 bg-forge-surface border-b border-forge-border">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
            </div>
            <span className="text-xs font-mono text-forge-subtle">paperforge_implementation.py</span>
            <div className="flex gap-2">
              <ActionButton onClick={handleCopy} label={copied ? '✓ Copied' : 'Copy'} />
              <ActionButton onClick={handleDownload} label="Download .py" primary />
            </div>
          </div>
          <Editor
            height="calc(100% - 41px)"
            language="python"
            value={generatedCode.code}
            theme="vs-dark"
            options={MONACO_OPTIONS}
          />
        </div>
      )}

      {/* Usage example */}
      {activeTab === 'usage' && (
        <div className="rounded-xl overflow-hidden border border-forge-border animate-fade-in" style={{ height: '460px' }}>
          <div className="flex items-center justify-between px-4 py-2 bg-forge-surface border-b border-forge-border">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
            </div>
            <span className="text-xs font-mono text-forge-subtle">usage_example.py</span>
            <ActionButton
              onClick={() => navigator.clipboard.writeText(generatedCode.usage_example)}
              label="Copy"
            />
          </div>
          <Editor
            height="calc(100% - 41px)"
            language="python"
            value={generatedCode.usage_example}
            theme="vs-dark"
            options={{ ...MONACO_OPTIONS, lineNumbers: 'off' }}
          />
        </div>
      )}

      {/* Limitations */}
      {activeTab === 'limits' && (
        <div className="rounded-xl bg-forge-surface border border-forge-border p-5 animate-fade-in" style={{ minHeight: '460px' }}>
          <h3 className="text-xs font-mono text-forge-subtle uppercase tracking-widest mb-4">
            What this implementation does NOT cover
          </h3>
          <div className="space-y-2">
            {generatedCode.limitations
              .split(/[•\n]/)
              .filter(l => l.trim())
              .map((line, i) => (
                <div key={i} className="flex gap-3 items-start">
                  <span className="text-forge-danger text-sm mt-0.5 shrink-0">✗</span>
                  <span className="text-sm text-forge-subtle leading-relaxed">{line.trim()}</span>
                </div>
              ))}
          </div>
          <div className="mt-6 p-3 rounded-lg bg-forge-accent/5 border border-forge-accent/20">
            <p className="text-xs text-forge-subtle">
              <span className="text-forge-accent">Tip:</span> This is a {generatedCode.strategy === 'core' ? 'core mechanism' : generatedCode.strategy} implementation.
              For a full reproduction, combine with the paper's appendix and referenced codebases.
            </p>
          </div>
        </div>
      )}

      {/* Actions row */}
      <div className="flex gap-2">
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="flex-1 py-2.5 rounded-lg border border-forge-border text-sm font-mono text-forge-subtle 
                     hover:text-forge-text hover:border-forge-muted transition-all disabled:opacity-40"
        >
          {isRegenerating ? '⟳ Regenerating...' : '⟳ Regenerate'}
        </button>
        <button
          onClick={handleDownload}
          className="flex-1 py-2.5 rounded-lg bg-forge-accent text-white text-sm font-mono 
                     hover:bg-forge-accent-bright transition-all shadow-lg shadow-forge-accent/20"
        >
          ↓ Download .py
        </button>
      </div>
    </div>
  );
}

function ActionButton({ onClick, label, primary }) {
  return (
    <button
      onClick={onClick}
      className={`text-xs px-2.5 py-1 rounded font-mono transition-all ${
        primary
          ? 'bg-forge-accent text-white hover:bg-forge-accent-bright'
          : 'text-forge-subtle hover:text-forge-text border border-forge-border hover:border-forge-muted'
      }`}
    >
      {label}
    </button>
  );
}
