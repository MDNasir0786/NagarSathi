import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { PriorityBadge } from '../ui/PriorityBadge';

export const AIInsightCard = ({ aiAnalysis }) => {
  if (!aiAnalysis) return null;

  const {
    autoCategory,
    predictedPriority,
    confidenceScore,
    isDuplicateDetected,
    duplicateComplaintId,
    recommendedWorkerDept,
    imageVerified,
    imageVerificationNote,
  } = aiAnalysis;

  return (
    <div className="bg-gradient-to-r from-emerald-50 to-teal-50/60 border border-emerald-200 rounded-2xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-emerald-600 text-white rounded-xl shadow-xs">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-bold text-gray-900 text-sm">Smart Bhopal AI Engine Result</h4>
            <p className="text-[11px] text-gray-500">Auto-Assisted Computer Vision & Classifier</p>
          </div>
        </div>
        <span className="bg-emerald-600 text-white text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase tracking-wider">
          {(confidenceScore * 100).toFixed(0)}% Confidence
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 text-xs">
        <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100">
          <span className="text-[10px] text-gray-400 font-semibold block uppercase">Auto Category</span>
          <span className="font-bold text-gray-900">{autoCategory}</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100">
          <span className="text-[10px] text-gray-400 font-semibold block uppercase">Predicted Priority</span>
          <PriorityBadge priority={predictedPriority} className="mt-0.5" />
        </div>
        <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100 col-span-2 sm:col-span-1">
          <span className="text-[10px] text-gray-400 font-semibold block uppercase">Recommended Dept</span>
          <span className="font-bold text-emerald-800">{recommendedWorkerDept || 'Municipal Wing'}</span>
        </div>
      </div>

      {imageVerified && (
        <div className="flex items-start gap-2 bg-white/90 p-2.5 rounded-xl border border-emerald-200 text-xs text-emerald-900">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <span>{imageVerificationNote || 'AI verified authentic civic issue photo evidence.'}</span>
        </div>
      )}

      {isDuplicateDetected && (
        <div className="flex items-center gap-2 bg-amber-50 p-2.5 rounded-xl border border-amber-200 text-xs text-amber-900 font-medium">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Similar issue detected nearby (ID: {duplicateComplaintId || 'SB-2026-8901'}).</span>
        </div>
      )}
    </div>
  );
};
