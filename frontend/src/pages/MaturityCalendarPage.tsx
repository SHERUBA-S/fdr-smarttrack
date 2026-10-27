import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, AlertCircle, Clock, CheckCircle2, RefreshCw, ArrowUpRight, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { MaturityCalendarResponse, MaturityBucketItem } from '../types';

export const MaturityCalendarPage: React.FC = () => {
  const [data, setData] = useState<MaturityCalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'expired' | 'within_7_days' | 'within_15_days' | 'within_30_days' | 'future'>('within_30_days');

  const fetchCalendar = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMaturityCalendar();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate maturity calendar windows');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalendar();
  }, []);

  const activeBucket: MaturityBucketItem[] = data ? data.buckets[activeTab] || [] : [];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-700" />
            Maturity Timeline Calendar & In-App Alerts
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configurable 30, 15, and 7-day maturity countdown windows with compliance renewal triggers
          </p>
        </div>
        <button
          onClick={fetchCalendar}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-sync Maturity Windows
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          {error}
        </div>
      )}

      {/* Countdown Window Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <button
          onClick={() => setActiveTab('expired')}
          className={`p-3.5 rounded-xl border text-left transition-all ${
            activeTab === 'expired'
              ? 'border-rose-600 bg-rose-50/70 shadow-xs ring-1 ring-rose-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <span className="text-[10px] uppercase font-bold text-rose-700 block">Overdue Maturity</span>
          <div className="text-xl font-bold text-rose-800 mt-1">{data?.summary.expired_count ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Immediate action</span>
        </button>

        <button
          onClick={() => setActiveTab('within_7_days')}
          className={`p-3.5 rounded-xl border text-left transition-all ${
            activeTab === 'within_7_days'
              ? 'border-orange-600 bg-orange-50/70 shadow-xs ring-1 ring-orange-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <span className="text-[10px] uppercase font-bold text-orange-700 block">&le; 7 Days Window</span>
          <div className="text-xl font-bold text-orange-800 mt-1">{data?.summary.within_7_days_count ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Critical deadline</span>
        </button>

        <button
          onClick={() => setActiveTab('within_15_days')}
          className={`p-3.5 rounded-xl border text-left transition-all ${
            activeTab === 'within_15_days'
              ? 'border-amber-600 bg-amber-50/70 shadow-xs ring-1 ring-amber-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <span className="text-[10px] uppercase font-bold text-amber-700 block">&le; 15 Days Window</span>
          <div className="text-xl font-bold text-amber-800 mt-1">{data?.summary.within_15_days_count ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Urgent follow-up</span>
        </button>

        <button
          onClick={() => setActiveTab('within_30_days')}
          className={`p-3.5 rounded-xl border text-left transition-all ${
            activeTab === 'within_30_days'
              ? 'border-blue-600 bg-blue-50/70 shadow-xs ring-1 ring-blue-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <span className="text-[10px] uppercase font-bold text-blue-700 block">&le; 30 Days Window</span>
          <div className="text-xl font-bold text-blue-800 mt-1">{data?.summary.within_30_days_count ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Advance notice</span>
        </button>

        <button
          onClick={() => setActiveTab('future')}
          className={`p-3.5 rounded-xl border text-left transition-all ${
            activeTab === 'future'
              ? 'border-emerald-600 bg-emerald-50/70 shadow-xs ring-1 ring-emerald-600'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">&gt; 30 Days (Healthy)</span>
          <div className="text-xl font-bold text-emerald-800 mt-1">{data?.summary.future_count ?? '...'}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Compliant</span>
        </button>
      </div>

      {/* Bucket Items Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">
            Deposits in Selected Window ({activeBucket.length})
          </h3>
          <span className="text-xs text-slate-400">As of {data?.as_of_date}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">FDR Number</th>
                <th className="py-3 px-4">Issuing Bank</th>
                <th className="py-3 px-4">Principal Amount</th>
                <th className="py-3 px-4">Maturity Date</th>
                <th className="py-3 px-4">Days Left</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                    Calculating maturity windows...
                  </td>
                </tr>
              ) : activeBucket.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    No deposit records currently in this countdown window.
                  </td>
                </tr>
              ) : (
                activeBucket.map((fdr) => (
                  <tr key={fdr.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      <Link to={`/fdrs/${fdr.id}`} className="text-blue-700 hover:underline">
                        {fdr.fdr_number}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 text-slate-700">{fdr.bank_name}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      ₹{fdr.principal_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-800">{fdr.maturity_date}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        fdr.days_left < 0 ? 'bg-rose-100 text-rose-800' :
                        fdr.days_left <= 7 ? 'bg-orange-100 text-orange-800' :
                        fdr.days_left <= 15 ? 'bg-amber-100 text-amber-800' :
                        fdr.days_left <= 30 ? 'bg-blue-100 text-blue-800' :
                        'bg-emerald-100 text-emerald-800'
                      }`}>
                        {fdr.days_left < 0 ? `${Math.abs(fdr.days_left)} days overdue` : `${fdr.days_left} days left`}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                        {fdr.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Link
                        to={`/renewals?fdr_id=${fdr.id}`}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-[11px] font-semibold transition-colors"
                      >
                        Renew
                      </Link>
                      <Link
                        to={`/fdrs/${fdr.id}`}
                        className="text-xs font-semibold text-blue-700 hover:text-blue-900"
                      >
                        View
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
