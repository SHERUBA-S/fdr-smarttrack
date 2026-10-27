import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { GitCommit, ArrowRight, Clock, ShieldCheck, RefreshCw, CheckCircle2, FileText, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import { FDRLifecycleChain } from '../types';

export const LifecycleChainPage: React.FC = () => {
  const [chains, setChains] = useState<FDRLifecycleChain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFdrId, setSelectedFdrId] = useState<string | null>(null);

  const fetchChains = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLifecycleChains(30);
      setChains(data);
      if (data.length > 0) {
        setSelectedFdrId(data[0].fdr_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to construct lifecycle chains');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChains();
  }, []);

  const selectedChain = chains.find(c => c.fdr_id === selectedFdrId) || chains[0];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-indigo-600" />
            FDR Lifecycle Chain of Custody
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            End-to-end traceable historical lineage linking registrations, receipts, renewal requests, and supervisory clearances
          </p>
        </div>
        <button
          onClick={fetchChains}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-sync Lineage
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-slate-400">
          <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-2 text-indigo-600" />
          Reconstructing lifecycle chain events from PostgreSQL logs...
        </div>
      ) : chains.length === 0 ? (
        <div className="bg-white p-12 text-center text-slate-400 rounded-xl border border-slate-200/80">
          No FDR lifecycle records found.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Chain Selector */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs p-4 space-y-3">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Active Deposit Chains ({chains.length})
            </span>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {chains.map((c) => (
                <button
                  key={c.fdr_id}
                  onClick={() => setSelectedFdrId(c.fdr_id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selectedFdrId === c.fdr_id
                      ? 'border-indigo-600 bg-indigo-50/40 shadow-xs ring-1 ring-indigo-600'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-slate-900">{c.fdr_number}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {c.current_status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 mt-1 truncate">{c.bank_name}</div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2 pt-2 border-t border-slate-100">
                    <span>₹{c.principal_amount.toLocaleString('en-IN')}</span>
                    <span>{c.timeline_events.length} Recorded Events</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Right: Visual Chain Timeline */}
          {selectedChain && (
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 shadow-xs p-6 space-y-6">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                      Lineage Chain
                    </span>
                    <h2 className="font-mono font-bold text-base text-slate-900">{selectedChain.fdr_number}</h2>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {selectedChain.bank_name} &bull; Principal: ₹{selectedChain.principal_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <Link
                  to={`/fdrs/${selectedChain.fdr_id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                >
                  View FDR Record <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Chain Diagram Flow */}
              <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
                {selectedChain.timeline_events.map((event, idx) => (
                  <div key={idx} className="relative group">
                    {/* Bullet marker */}
                    <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center shadow-xs">
                      <div className="w-2 h-2 rounded-full bg-indigo-600" />
                    </div>

                    <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200/80 space-y-2 group-hover:border-indigo-300 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                            {event.stage}
                          </span>
                          <span className="text-xs font-bold text-slate-900">{event.title}</span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>

                      <p className="text-xs text-slate-700">{event.details}</p>

                      <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1 border-t border-slate-200/50">
                        <span>
                          <strong className="text-slate-600">Actor:</strong> {event.actor}
                        </span>
                        <span>
                          <strong className="text-slate-600">Outcome:</strong>{' '}
                          <span className="font-semibold text-slate-800">{event.status}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
