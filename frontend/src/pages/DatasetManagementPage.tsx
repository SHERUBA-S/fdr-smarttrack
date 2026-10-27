import React, { useState } from 'react';
import { Database, Play, Trash2, CheckCircle2, AlertCircle, RefreshCw, Info } from 'lucide-react';
import { api } from '../services/api';

export const DatasetManagementPage: React.FC = () => {
  const [generating, setGenerating] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (mode: 'DEMO' | 'FULL') => {
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.generateDataset(mode);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to purge synthetic demo records from PostgreSQL?')) return;
    setResetting(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.resetDemoData();
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Reset failed');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          Synthetic Dataset Management
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Generate large-scale realistic synthetic data directly into dedicated PostgreSQL
        </p>
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold">Dataset Integrity & Ethical Notice</h4>
          <p className="leading-relaxed">
            All generated banks, institutions, FDR numbers, and approvals are purely synthetic mock data for hackathon evaluation.
            No real individuals' data, real accounts, or official AICTE endorsement is represented.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs space-y-1">
          <div className="flex items-center gap-2 font-bold text-sm text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Operation Completed Successfully!</span>
          </div>
          <pre className="font-mono text-[11px] bg-white/70 p-2.5 rounded border border-emerald-200 mt-2 overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Demo Dataset Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 text-blue-700 font-bold text-sm">
              <Database className="w-4 h-4" />
              <span>Standard Demo Dataset</span>
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Fast generation suitable for live jury demonstrations and UI testing:
            </p>
            <ul className="text-xs text-slate-600 list-disc list-inside mt-2 space-y-1">
              <li>60 Synthetic Institutions</li>
              <li>15 Commercial & Public Banks</li>
              <li>350 FDR Records with realistic distributions</li>
              <li>Pre-seeded edge cases and discrepancy flags</li>
              <li>~0.5 second generation time</li>
            </ul>
          </div>

          <button
            onClick={() => handleGenerate('DEMO')}
            disabled={generating || resetting}
            className="w-full py-2 px-4 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Generate Demo Dataset
          </button>
        </div>

        {/* Full Baseline Dataset Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 text-purple-700 font-bold text-sm">
              <Database className="w-4 h-4" />
              <span>Full Baseline Scale Dataset</span>
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Full scale benchmark stress test for database indexes and aggregations:
            </p>
            <ul className="text-xs text-slate-600 list-disc list-inside mt-2 space-y-1">
              <li>2,000 Institutions</li>
              <li>100 Banks & Branch networks</li>
              <li>20,000 Synthetic FDR Records</li>
              <li>5,000 Renewal & Release requests</li>
              <li>Bulk PostgreSQL batch inserts</li>
            </ul>
          </div>

          <button
            onClick={() => handleGenerate('FULL')}
            disabled={generating || resetting}
            className="w-full py-2 px-4 bg-purple-700 hover:bg-purple-800 text-white text-xs font-semibold rounded-lg shadow-xs flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Generate Full Scale (20k FDRs)
          </button>
        </div>
      </div>

      {/* Reset Demo Records */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-slate-900">Purge Synthetic Records</h4>
          <p className="text-xs text-slate-500 mt-0.5">
            Safely remove all records tagged with <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded">is_synthetic = True</code>
          </p>
        </div>
        <button
          onClick={handleReset}
          disabled={generating || resetting}
          className="px-4 py-2 border border-rose-300 text-rose-700 hover:bg-rose-50 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          {resetting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
          Reset Synthetic Data
        </button>
      </div>
    </div>
  );
};
