import React from 'react';

export default function Header({ onReset }) {
  return (
    <header className="border-b border-forge-border bg-forge-surface/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 group"
        >
          <div className="w-7 h-7 rounded-lg bg-forge-accent flex items-center justify-center shadow-lg shadow-forge-accent/30 group-hover:shadow-forge-accent/50 transition-shadow">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 7L6 3L10 7L6 11L2 7Z" fill="white" opacity="0.9"/>
              <path d="M6 3L10 7L7 10" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="font-display font-700 text-forge-text text-[15px] tracking-tight">
            Paper<span className="text-gradient">Forge</span>
          </span>
        </button>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-forge-subtle font-mono">v0.2.0</span>
          <a
            href="https://github.com/GPREETHAMSAXON/PaperForge"
            target="_blank"
            rel="noopener noreferrer"
            className="text-forge-subtle hover:text-forge-text transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs px-3 py-1.5 rounded-md border border-forge-border text-forge-subtle hover:text-forge-text hover:border-forge-muted transition-all font-mono"
          >
            API Docs
          </a>
        </div>
      </div>
    </header>
  );
}
