import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CheckSquare, AlertTriangle, ShieldAlert, ArrowUpRight, CheckCircle2, RefreshCw, FileText, Info } from 'lucide-react';
import { api } from '../services/api';
import { ConsistencyCheckResponse, ConsistencyCheckItem } from '../types';

export const ConsistencyCheckerPage: React.FC = () => {
  const [data, setData] = useState<ConsistencyCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');

  const fetchChecks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getConsistencyChecks();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to execute consistency audit');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChecks();
  }, []);

  const filteredItems = (data?.items || []).filter(item => {
    if (severityFilter !== 'ALL' && item.severity !== severityFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-blue-700" />
            Document & Field Consistency Checker
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-validation of mandatory deposit parameters, receipt uploads, and date boundaries
          </p>
        </div>
        <button
          onClick={fetchChecks}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-audit Consistency
        </button>
      </div>

      {/* Mandatory Statutory Notice */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold">Administrative Consistency Scope & Banking Notice</div>
          <p className="leading-relaxed">
            {data?.disclaimer ||
              'Automated administrative consistency checks only. Passing checks does not constitute official commercial bank authentication or verify institutional balance reserves.'}
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* Audit Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Records Audited</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{data?.total_records_checked ?? '...'}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-xs bg-rose-50/20">
          <span className="text-[11px] font-semibold text-rose-700 uppercase">Total Inconsistencies</span>
          <div className="text-2xl font-bold text-rose-700 mt-1">{data?.inconsistency_count ?? '...'}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-orange-100 shadow-xs bg-orange-50/20">
          <span className="text-[11px] font-semibold text-orange-700 uppercase">Critical Date / Mismatch</span>
          <div className="text-2xl font-bold text-orange-700 mt-1">
            {(data?.items || []).filter(i => i.severity === 'CRITICAL').length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-xs bg-amber-50/20">
          <span className="text-[11px] font-semibold text-amber-700 uppercase">Missing Receipts</span>
          <div className="text-2xl font-bold text-amber-700 mt-1">
            {(data?.items || []).filter(i => i.field === 'documents').length}
          </div>
        </div>
      </div>

      {/* Severity Filter */}
      <div className="flex items-center gap-2 bg-white p-3 rounded-xl border border-slate-200/80 text-xs">
        <span className="font-semibold text-slate-600 mr-1">Filter Severity:</span>
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(sev => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
              severityFilter === sev
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Inconsistency Cards Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Issue Type</th>
                <th className="py-3 px-4">FDR Reference</th>
                <th className="py-3 px-4">Field / Evidence</th>
                <th className="py-3 px-4">Description & Impact</th>
                <th className="py-3 px-4">Recommended Review</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                    Running consistency rules across deposits and OCR documents...
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    All records conform to active consistency standards!
                  </td>
                </tr>
              ) : (
                filteredItems.map(item => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                        item.severity === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                        item.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {item.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {item.issue_type}
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      <Link to={`/fdrs/${item.fdr_id}`} className="text-blue-700 font-semibold hover:underline">
                        {item.fdr_number}
                      </Link>
                      <div className="text-[10px] text-slate-400">{item.bank_name}</div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-600">
                      {item.field}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700 max-w-xs">
                      {item.description}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 font-medium">
                      {item.recommended_action}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/fdrs/${item.fdr_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900"
                      >
                        Inspect <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
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
