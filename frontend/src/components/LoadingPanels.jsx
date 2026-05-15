import React from 'react';

function SkeletonBlock({ className }) {
  return <div className={`skeleton rounded-lg ${className}`} />;
}

export function AnalysisSkeleton() {
  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      {[100, 80, 120, 90, 70].map((w, i) => (
        <div key={i} className="p-4 rounded-xl bg-forge-surface border border-forge-border">
          <SkeletonBlock className="h-3 w-24 mb-3" />
          <SkeletonBlock className={`h-4 w-${w < 100 ? '[' + w + '%]' : 'full'} mb-2`} />
          <SkeletonBlock className="h-4 w-3/4" />
        </div>
      ))}
    </div>
  );
}

export function CodeSkeleton() {
  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      <div className="p-4 rounded-xl bg-forge-surface border border-forge-border">
        <SkeletonBlock className="h-5 w-32 mb-3" />
        <SkeletonBlock className="h-4 w-full mb-2" />
        <SkeletonBlock className="h-4 w-2/3" />
      </div>

      <div className="rounded-xl overflow-hidden border border-forge-border" style={{ height: '460px' }}>
        <div className="px-4 py-2 bg-forge-surface border-b border-forge-border flex items-center gap-1.5">
          <SkeletonBlock className="w-3 h-3 rounded-full" />
          <SkeletonBlock className="w-3 h-3 rounded-full" />
          <SkeletonBlock className="w-3 h-3 rounded-full" />
        </div>
        <div className="p-4 space-y-2.5 bg-[#1e1e1e]">
          {[90, 60, 75, 45, 80, 55, 70, 40, 85, 65, 50, 78, 42, 88, 60].map((w, i) => (
            <SkeletonBlock key={i} className="h-3.5" style={{ width: `${w}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}
