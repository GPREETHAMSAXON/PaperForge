import React from 'react';

export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="w-full max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-start gap-3 p-4 rounded-xl bg-forge-danger/5 border border-forge-danger/30">
        <span className="text-forge-danger shrink-0 mt-0.5">✕</span>
        <div className="flex-1">
          <p className="text-sm text-forge-danger font-mono">{message}</p>
          <p className="text-xs text-forge-subtle mt-1">
            Make sure the FastAPI server is running on localhost:8000 and the arXiv URL is valid.
          </p>
        </div>
        <button
          onClick={onDismiss}
          className="text-forge-subtle hover:text-forge-text text-xs shrink-0 font-mono"
        >
          dismiss
        </button>
      </div>
    </div>
  );
}
