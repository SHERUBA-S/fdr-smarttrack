import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Hourglass, AlertTriangle, Clock, ShieldAlert, CheckCircle2, RefreshCw, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import { BottleneckResponse, BottleneckItem } from '../types';

export const BottleneckMonitorPage: React.FC = () => {
  const [data, setData] = useState<BottleneckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBottlenecks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getBottlenecks();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze workflow queues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBottlenecks();
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Hourglass className="w-5 h-5 text-amber-600" />
            Workflow Bottleneck & SLA Latency Monitor
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time tracking of review queue age, unverified deposit backlogs, and pending clearance requests
          </p>
        </div>
        <button
          onClick={fetchBottlenecks}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-audit Latencies
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Verification Backlog</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{data?.verification_queue_pending ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Deposits pending initial review</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-xs bg-amber-50/20">
          <span className="text-[11px] font-semibold text-amber-700 uppercase">Pending Renewals</span>
          <div className="text-2xl font-bold text-amber-700 mt-1">{data?.renewal_requests_pending ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Extensions awaiting decision</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-xs bg-purple-50/20">
          <span className="text-[11px] font-semibold text-purple-700 uppercase">Pending Releases</span>
          <div className="text-2xl font-bold text-purple-700 mt-1">{data?.release_requests_pending ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Clearance NOC approvals</span>
        </div>
        <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-xs bg-rose-50/20">
          <span className="text-[11px] font-semibold text-rose-700 uppercase">SLA Breaches (&gt;7 Days)</span>
          <div className="text-2xl font-bold text-rose-700 mt-1">{data?.critical_breaches_count ?? '...'}</div>
          <span className="text-[10px] text-rose-600 font-semibold mt-1 block">Requires immediate intervention</span>
        </div>
      </div>

      {/* Bottlenecks Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">
            Stalled Tasks Requiring Supervisory Attention ({data?.items.length ?? 0})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Queue Latency</th>
                <th className="py-3 px-4">Queue Type</th>
                <th className="py-3 px-4">FDR Number</th>
                <th className="py-3 px-4">Issuing Bank</th>
                <th className="py-3 px-4">Responsible Role</th>
                <th className="py-3 px-4">Action Required</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-600" />
                    Calculating queue ages and SLA metrics...
                  </td>
                </tr>
              ) : (data?.items || []).length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    No bottleneck delays! All workflow items are being resolved within SLA targets.
                  </td>
                </tr>
              ) : (
                data?.items.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        b.pending_days >= 7 ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {b.pending_days} days pending
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{b.type}</td>
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      {b.fdr_id ? (
                        <Link to={`/fdrs/${b.fdr_id}`} className="text-blue-700 hover:underline">
                          {b.fdr_number}
                        </Link>
                      ) : (
                        b.fdr_number
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{b.bank_name}</td>
                    <td className="py-3.5 px-4 text-slate-700 font-medium">{b.responsible_role}</td>
                    <td className="py-3.5 px-4 text-slate-700 max-w-xs">{b.action_required}</td>
                    <td className="py-3.5 px-4 text-right">
                      {b.fdr_id ? (
                        <Link
                          to={`/fdrs/${b.fdr_id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900"
                        >
                          Resolve <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      ) : (
                        <Link
                          to="/review-queue"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900"
                        >
                          Review Queue <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
