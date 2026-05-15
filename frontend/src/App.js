import React from 'react';
import Header from './components/Header';
import InputBar from './components/InputBar';
import HeroSection from './components/HeroSection';
import AnalysisPanel from './components/AnalysisPanel';
import CodePanel from './components/CodePanel';
import ErrorBanner from './components/ErrorBanner';
import { AnalysisSkeleton, CodeSkeleton } from './components/LoadingPanels';
import { usePaperForge, STAGES } from './hooks/usePaperForge';

export default function App() {
  const {
    stage, stageMessage, analysis, generatedCode, tokensUsed,
    error, paperMeta, runFullPipeline, regenerateCode, reset,
    isLoading, isDone, isError,
  } = usePaperForge();

  const showHero = stage === STAGES.IDLE;
  const showPanels = isLoading || isDone || isError;
  const isRegenerating = stage === STAGES.GENERATING && analysis !== null;

  return (
    <div className="min-h-screen bg-forge-bg relative">
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px)`,
          backgroundSize: '64px 64px',
        }}
      />
      <Header onReset={reset} />
      <main className="relative z-10 max-w-7xl mx-auto px-6 pb-20">
        <div className="py-10">
          <InputBar onSubmit={runFullPipeline} isLoading={isLoading} stageMessage={stageMessage} />
        </div>
        {isError && <ErrorBanner message={error} onDismiss={reset} />}
        {showHero && <HeroSection />}
        {showPanels && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
            <div>
              <SectionLabel
                label="Methodology"
                sub={analysis ? `${analysis.key_algorithm} · ${analysis.paper_type}` : 'Reading paper...'}
              />
              {isLoading && !analysis ? <AnalysisSkeleton /> : (
                <AnalysisPanel analysis={analysis} paperMeta={paperMeta} tokensUsed={tokensUsed} />
              )}
            </div>
            <div>
              <SectionLabel
                label="Implementation"
                sub={generatedCode ? `${generatedCode.strategy} · ${generatedCode.estimated_lines} lines` : 'Generating code...'}
              />
              {isLoading && !generatedCode ? <CodeSkeleton /> : (
                <CodePanel generatedCode={generatedCode} onRegenerate={regenerateCode} isRegenerating={isRegenerating} />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function SectionLabel({ label, sub }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-xs font-mono text-forge-subtle uppercase tracking-widest">{label}</h2>
      {sub && <span className="text-xs font-mono text-forge-subtle/60">{sub}</span>}
    </div>
  );
}
