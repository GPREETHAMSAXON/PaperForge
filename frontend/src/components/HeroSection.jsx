import React from 'react';

const FEATURES = [
  {
    icon: '⬡',
    title: 'Parse any ML paper',
    desc: 'ArXiv URL or PDF upload. Handles 15+ page papers in seconds.',
  },
  {
    icon: '◈',
    title: 'Claude extracts the method',
    desc: 'Algorithm, datasets, metrics, novelty — structured and ready.',
  },
  {
    icon: '⟡',
    title: 'Get runnable Python',
    desc: 'Implementation with section references. Download and run immediately.',
  },
];

export default function HeroSection() {
  return (
    <div className="flex flex-col items-center text-center py-16 animate-fade-in">
      {/* Glow orb */}
      <div
        className="absolute top-24 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />

      <div className="relative z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-forge-border bg-forge-surface text-xs font-mono text-forge-subtle mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-forge-success animate-pulse" />
          Powered by Claude + FastAPI
        </div>

        {/* Headline */}
        <h1 className="font-display font-700 text-5xl text-forge-text leading-tight tracking-tight mb-4">
          Research papers →<br />
          <span className="text-gradient">Working code</span>
        </h1>

        <p className="text-forge-subtle text-lg max-w-lg mb-12 leading-relaxed">
          Paste an arXiv link. PaperForge reads the paper, extracts the methodology,
          and generates a runnable Python implementation — in under 90 seconds.
        </p>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="p-4 rounded-xl bg-forge-surface glow-border text-left"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="text-2xl text-forge-accent mb-3 font-display">{f.icon}</div>
              <div className="text-sm font-display font-500 text-forge-text mb-1.5">{f.title}</div>
              <div className="text-xs text-forge-subtle leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
