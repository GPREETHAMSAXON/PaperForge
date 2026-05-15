import React, { useState, useRef } from 'react';

const EXAMPLE_PAPERS = [
  { label: 'Attention Is All You Need', url: 'https://arxiv.org/abs/1706.03762' },
  { label: 'BERT', url: 'https://arxiv.org/abs/1810.04805' },
  { label: 'LoRA', url: 'https://arxiv.org/abs/2106.09685' },
  { label: 'DDPM', url: 'https://arxiv.org/abs/2006.11239' },
];

export default function InputBar({ onSubmit, isLoading, stageMessage }) {
  const [url, setUrl] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim() && !isLoading) onSubmit(url.trim());
  };

  const handleExample = (exampleUrl) => {
    setUrl(exampleUrl);
    inputRef.current?.focus();
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Main input */}
      <form onSubmit={handleSubmit}>
        <div className={`glow-border rounded-xl bg-forge-surface flex items-center gap-3 px-4 py-3 ${isLoading ? 'opacity-70' : ''}`}>
          {/* ArXiv icon */}
          <div className="shrink-0 text-forge-subtle">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>

          <input
            ref={inputRef}
            type="text"
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="Paste an arXiv URL or ID — e.g. arxiv.org/abs/1706.03762"
            disabled={isLoading}
            className="flex-1 bg-transparent text-forge-text placeholder-forge-subtle text-sm outline-none font-mono"
          />

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="shrink-0 px-4 py-2 rounded-lg bg-forge-accent text-white text-sm font-display font-500 
                       hover:bg-forge-accent-bright transition-all disabled:opacity-40 disabled:cursor-not-allowed
                       shadow-lg shadow-forge-accent/20 hover:shadow-forge-accent/40"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <SpinnerIcon />
                {stageMessage}
              </span>
            ) : (
              'Analyze & Build →'
            )}
          </button>
        </div>
      </form>

      {/* Stage progress indicator */}
      {isLoading && (
        <div className="mt-3 animate-fade-in">
          <StageProgress message={stageMessage} />
        </div>
      )}

      {/* Example papers */}
      {!isLoading && (
        <div className="mt-4 flex flex-wrap gap-2 justify-center animate-fade-in">
          <span className="text-xs text-forge-subtle self-center">Try:</span>
          {EXAMPLE_PAPERS.map(p => (
            <button
              key={p.url}
              onClick={() => handleExample(p.url)}
              className="text-xs px-3 py-1.5 rounded-full border border-forge-border text-forge-subtle 
                         hover:text-forge-text hover:border-forge-muted transition-all font-mono"
            >
              {p.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SpinnerIcon() {
  return (
    <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3"/>
      <path d="M12 2a10 10 0 010 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

function StageProgress({ message }) {
  const stages = ['Fetching paper from arXiv...', 'Claude is reading the paper...', 'Generating implementation...'];
  const current = stages.indexOf(message);

  return (
    <div className="flex items-center justify-center gap-3">
      {stages.map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full transition-all duration-500 ${
            i < current ? 'bg-forge-success' :
            i === current ? 'bg-forge-accent animate-pulse' :
            'bg-forge-muted'
          }`} />
          <span className={`text-xs font-mono transition-colors duration-300 ${
            i === current ? 'text-forge-text' : 'text-forge-subtle'
          }`}>
            {s.replace('...', '')}
          </span>
          {i < stages.length - 1 && (
            <span className="text-forge-muted text-xs ml-1">→</span>
          )}
        </div>
      ))}
    </div>
  );
}
