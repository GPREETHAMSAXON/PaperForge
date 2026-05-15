import { useState, useCallback } from 'react';
import { api } from '../api/client';

export const STAGES = {
  IDLE: 'idle',
  PARSING: 'parsing',
  ANALYZING: 'analyzing',
  GENERATING: 'generating',
  DONE: 'done',
  ERROR: 'error',
};

const STAGE_MESSAGES = {
  [STAGES.PARSING]:    'Fetching paper from arXiv...',
  [STAGES.ANALYZING]:  'Claude is reading the paper...',
  [STAGES.GENERATING]: 'Generating implementation...',
  [STAGES.DONE]:       'Done',
  [STAGES.ERROR]:      'Something went wrong',
};

export function usePaperForge() {
  const [stage, setStage] = useState(STAGES.IDLE);
  const [analysis, setAnalysis] = useState(null);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [sandboxResult, setSandboxResult] = useState(null);
  const [tokensUsed, setTokensUsed] = useState(0);
  const [error, setError] = useState(null);
  const [paperMeta, setPaperMeta] = useState(null);

  const reset = useCallback(() => {
    setStage(STAGES.IDLE);
    setAnalysis(null);
    setGeneratedCode(null);
    setSandboxResult(null);
    setTokensUsed(0);
    setError(null);
    setPaperMeta(null);
  }, []);

  // Full pipeline: parse → analyze → generate
  const runFullPipeline = useCallback(async (url) => {
    if (!url.trim()) return;

    try {
      setError(null);
      setAnalysis(null);
      setGeneratedCode(null);
      setSandboxResult(null);

      // Stage 1: Show parsing state
      setStage(STAGES.PARSING);
      await new Promise(r => setTimeout(r, 400)); // brief pause for UX

      // Stage 2: Analyze (parse + Claude call 1)
      setStage(STAGES.ANALYZING);
      const analyzeRes = await api.analyzeArxiv(url);
      const { analysis: analysisData, arxiv_id, tokens_used: t1 } = analyzeRes.data;
      setAnalysis(analysisData);
      setPaperMeta({ arxiv_id, title: analysisData.title });
      setTokensUsed(t1);

      // Stage 3: Generate (Claude call 2)
      setStage(STAGES.GENERATING);
      const genRes = await api.generateFromAnalysis(arxiv_id, analysisData, false);
      const { generated_code, sandbox_result, tokens_used: t2 } = genRes.data;
      setGeneratedCode(generated_code);
      setSandboxResult(sandbox_result);
      setTokensUsed(t1 + t2);

      setStage(STAGES.DONE);
    } catch (err) {
      setStage(STAGES.ERROR);
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Something went wrong. Check the URL and try again.'
      );
    }
  }, []);

  // Regenerate code without re-analyzing
  const regenerateCode = useCallback(async () => {
    if (!analysis || !paperMeta) return;
    try {
      setStage(STAGES.GENERATING);
      setError(null);
      const genRes = await api.generateFromAnalysis(paperMeta.arxiv_id, analysis, false);
      const { generated_code, tokens_used } = genRes.data;
      setGeneratedCode(generated_code);
      setTokensUsed(prev => prev + tokens_used);
      setStage(STAGES.DONE);
    } catch (err) {
      setStage(STAGES.ERROR);
      setError('Code regeneration failed. Try again.');
    }
  }, [analysis, paperMeta]);

  return {
    stage,
    stageMessage: STAGE_MESSAGES[stage] || '',
    analysis,
    generatedCode,
    sandboxResult,
    tokensUsed,
    error,
    paperMeta,
    runFullPipeline,
    regenerateCode,
    reset,
    isLoading: [STAGES.PARSING, STAGES.ANALYZING, STAGES.GENERATING].includes(stage),
    isDone: stage === STAGES.DONE,
    isError: stage === STAGES.ERROR,
  };
}
