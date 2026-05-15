import React from 'react';

export default function AnalysisPanel({ analysis, paperMeta, tokensUsed }) {
  if (!analysis) return null;

  const difficultyClass = {
    easy: 'badge-easy',
    medium: 'badge-medium',
    hard: 'badge-hard',
  }[analysis.implementation_difficulty] || 'badge-medium';

  return (
    <div className="flex flex-col gap-4 animate-slide-up">
      {/* Paper title */}
      <div className="p-4 rounded-xl bg-forge-surface glow-border">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h2 className="font-display font-600 text-forge-text text-base leading-snug">
            {analysis.title}
          </h2>
          {paperMeta?.arxiv_id && (
            <a
              href={`https://arxiv.org/abs/${paperMeta.arxiv_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-xs text-forge-subtle hover:text-forge-accent transition-colors font-mono"
            >
              {paperMeta.arxiv_id} ↗
            </a>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge label={analysis.implementation_difficulty} className={difficultyClass} />
          <Badge label={analysis.paper_type} className="badge-skeleton" />
          {analysis.is_implementable ? (
            <Badge label="implementable" className="badge-full" />
          ) : (
            <Badge label="not implementable" className="badge-hard" />
          )}
        </div>
      </div>

      {/* Key algorithm */}
      <Section title="Core Algorithm">
        <div className="font-mono text-sm text-forge-accent bg-forge-accent/5 px-3 py-2 rounded-lg border border-forge-accent/20">
          {analysis.key_algorithm}
        </div>
      </Section>

      {/* Problem statement */}
      <Section title="Problem">
        <p className="text-sm text-forge-subtle leading-relaxed">{analysis.problem_statement}</p>
      </Section>

      {/* Proposed method */}
      <Section title="Method">
        <p className="text-sm text-forge-subtle leading-relaxed">{analysis.proposed_method}</p>
      </Section>

      {/* Novelty */}
      <Section title="What's New">
        <p className="text-sm text-forge-subtle leading-relaxed">{analysis.novelty}</p>
      </Section>

      {/* Datasets */}
      {analysis.datasets_used?.length > 0 && (
        <Section title="Datasets">
          <div className="flex flex-wrap gap-2">
            {analysis.datasets_used.map(d => (
              <span key={d} className="text-xs px-2 py-1 rounded-md bg-forge-muted text-forge-subtle font-mono">
                {d}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Results */}
      {Object.keys(analysis.reported_results || {}).length > 0 && (
        <Section title="Reported Results">
          <div className="space-y-1.5">
            {Object.entries(analysis.reported_results).map(([k, v]) => (
              <div key={k} className="flex justify-between items-center text-xs">
                <span className="text-forge-subtle font-mono">{k}</span>
                <span className="text-forge-success font-mono font-500">{v}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Dependencies */}
      {analysis.dependencies?.length > 0 && (
        <Section title="Dependencies">
          <div className="flex flex-wrap gap-1.5">
            {analysis.dependencies.map(d => (
              <span key={d} className="text-xs px-2 py-0.5 rounded bg-forge-muted text-forge-subtle font-mono">
                {d}
              </span>
            ))}
          </div>
        </Section>
      )}

      {/* Reproducibility */}
      {analysis.reproducibility_notes && (
        <Section title="Reproducibility">
          <p className="text-xs text-forge-subtle leading-relaxed">{analysis.reproducibility_notes}</p>
        </Section>
      )}

      {/* Token usage */}
      {tokensUsed > 0 && (
        <div className="text-xs text-forge-subtle font-mono text-center pt-1">
          {tokensUsed.toLocaleString()} tokens used
        </div>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="p-4 rounded-xl bg-forge-surface glow-border">
      <h3 className="text-xs font-mono text-forge-subtle uppercase tracking-widest mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function Badge({ label, className }) {
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full font-mono capitalize ${className}`}>
      {label}
    </span>
  );
}
