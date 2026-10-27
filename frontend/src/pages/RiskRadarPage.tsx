import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Radar, AlertTriangle, ShieldAlert, ArrowUpRight, CheckCircle2, Clock, FileWarning, RefreshCw, Filter, Info } from 'lucide-react';
import { api } from '../services/api';
import { RiskRadarSummary, RiskRadarItem } from '../types';

export const RiskRadarPage: React.FC = () => {
  const [data, setData] = useState<RiskRadarSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [onlyDiscrepancies, setOnlyDiscrepancies] = useState(false);

  const fetchRadar = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRiskRadar();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate Risk Radar metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRadar();
  }, []);

  const filteredItems = (data?.items || []).filter(item => {
    if (priorityFilter !== 'ALL' && item.priority !== priorityFilter) return false;
    if (onlyDiscrepancies && !item.has_discrepancy) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Radar className="w-5 h-5 text-rose-600" />
            Explainable FDR Risk Radar
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Deterministic rule-based priority engine tracking maturity deadlines, document gaps, and stalled workflows
          </p>
        </div>
        <button
          onClick={fetchRadar}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-evaluate Rules
        </button>
      </div>

      {/* Ethical & Methodology Banner */}
      <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-start gap-3">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-800">Rule-Based Administrative Aid:</span>{' '}
          Risk Radar evaluates deterministic administrative conditions (e.g. days to maturity, uploaded receipts, and verification flags).
          A high-priority flag denotes an urgent operational task and is not a conclusive finding of bank illegitimacy.
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Evaluated Deposits</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{data?.total_evaluated ?? '...'}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-xs bg-rose-50/20">
          <span className="text-[11px] font-semibold text-rose-700 uppercase">High Priority Risk</span>
          <div className="text-2xl font-bold text-rose-700 mt-1">{data?.high_count ?? '...'}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-xs bg-amber-50/20">
          <span className="text-[11px] font-semibold text-amber-700 uppercase">Medium Attention</span>
          <div className="text-2xl font-bold text-amber-700 mt-1">{data?.medium_count ?? '...'}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-xs bg-purple-50/20">
          <span className="text-[11px] font-semibold text-purple-700 uppercase">Field Discrepancies</span>
          <div className="text-2xl font-bold text-purple-700 mt-1">{data?.discrepancy_count ?? '...'}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200/80 text-xs">
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-600 mr-2">Filter Priority:</span>
          {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
                priorityFilter === p
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
          <input
            type="checkbox"
            checked={onlyDiscrepancies}
            onChange={(e) => setOnlyDiscrepancies(e.target.checked)}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          Show only flagged discrepancies
        </label>
      </div>

      {/* Radar Items List */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rose-600" />
            Analyzing compliance rules across all registered FDRs...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-white p-12 text-center text-slate-400 rounded-xl border border-slate-200/80">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            No deposit records match the selected Risk Radar criteria.
          </div>
        ) : (
          filteredItems.map(item => (
            <div
              key={item.fdr_id}
              className={`bg-white rounded-xl border shadow-xs p-5 transition-shadow hover:shadow-md ${
                item.priority === 'HIGH' ? 'border-rose-200' :
                item.priority === 'MEDIUM' ? 'border-amber-200' : 'border-slate-200'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase ${
                    item.priority === 'HIGH' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                    item.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {item.priority} PRIORITY
                  </span>
                  <Link
                    to={`/fdrs/${item.fdr_id}`}
                    className="font-mono font-bold text-sm text-slate-900 hover:text-blue-700 hover:underline"
                  >
                    {item.fdr_number}
                  </Link>
                  <span className="text-xs text-slate-500">&bull; {item.bank_name}</span>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-slate-400">Principal:</span>{' '}
                    <span className="font-semibold text-slate-900">
                      ₹{item.principal_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Maturity:</span>{' '}
                    <span className="font-semibold text-slate-900">{item.maturity_date}</span>
                    <span className={`ml-1 text-[11px] font-semibold ${item.days_left < 0 ? 'text-rose-600' : 'text-slate-600'}`}>
                      ({item.days_left < 0 ? `${Math.abs(item.days_left)}d overdue` : `${item.days_left}d left`})
                    </span>
                  </div>
                  <Link
                    to={`/fdrs/${item.fdr_id}`}
                    className="inline-flex items-center gap-1 text-blue-700 font-semibold hover:text-blue-800"
                  >
                    Investigate <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* Triggered Rules Explanation */}
              <div className="mt-4 space-y-2.5">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Triggered Rule Explanations & Recommended Actions ({item.triggered_rules.length})
                </div>
                {item.triggered_rules.length === 0 ? (
                  <div className="text-xs text-slate-500 italic">
                    Healthy deposit parameters. No compliance threshold violations.
                  </div>
                ) : (
                  item.triggered_rules.map((rule, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-50 border border-slate-200/60 flex flex-col sm:flex-row sm:items-start justify-between gap-2"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            rule.severity === 'CRITICAL' ? 'bg-rose-600' :
                            rule.severity === 'HIGH' ? 'bg-orange-500' : 'bg-amber-500'
                          }`} />
                          <span className="font-bold text-xs text-slate-800">{rule.title}</span>
                          <span className="text-[10px] font-mono text-slate-400">[{rule.rule_id}]</span>
                        </div>
                        <p className="text-xs text-slate-600 pl-4">{rule.explanation}</p>
                      </div>

                      <div className="sm:text-right shrink-0 pl-4 sm:pl-0">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 block">Next Action</span>
                        <span className="text-xs font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {rule.action}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
