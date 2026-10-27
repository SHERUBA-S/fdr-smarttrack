import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, IndianRupee, AlertTriangle, Clock, CheckCircle,
  Building2, ArrowUpRight, ShieldAlert, AlertCircle, RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { api } from '../services/api';
import { DashboardMetrics, UrgentActionItem } from '../types';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';

const STATUS_COLORS: Record<string, string> = {
  Approved: '#10b981',
  Submitted: '#3b82f6',
  'Under Review': '#6366f1',
  'Renewal Pending': '#f59e0b',
  'Release Requested': '#8b5cf6',
  Released: '#059669',
  Expired: '#ef4444',
  'Additional Information Required': '#f97316',
  Draft: '#94a3b8'
};

export const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await api.getDashboardMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mb-2" />
        <p className="text-sm">Calculating database aggregations...</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm">
        {error || 'Unable to load dashboard data.'}
      </div>
    );
  }

  const formattedPrincipal = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(Number(metrics.total_recorded_principal));

  return (
    <div className="space-y-6">
      {/* Top Banner / Disclaimer */}
      <div className="bg-blue-900 text-white p-5 rounded-2xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Security Deposit & FDR Portfolio Dashboard</h1>
          <p className="text-xs text-blue-200 mt-1 max-w-2xl leading-relaxed">
            {metrics.disclaimer}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/fdrs/create"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors shrink-0"
          >
            + Register New FDR
          </Link>
          <button
            onClick={fetchMetrics}
            className="p-2 bg-blue-800 hover:bg-blue-700 rounded-lg text-blue-200 hover:text-white transition-colors"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Recorded FDRs"
          value={metrics.total_fdrs.toLocaleString()}
          subtitle="Active & archived records"
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Recorded Principal Value"
          value={formattedPrincipal}
          subtitle="Administrative total from receipts"
          icon={IndianRupee}
          color="emerald"
        />
        <StatCard
          title="Maturity Follow-ups (30d)"
          value={metrics.fdrs_approaching_maturity_30d}
          subtitle={`${metrics.fdrs_overdue_maturity} currently overdue`}
          icon={Clock}
          color="amber"
          badge={metrics.fdrs_overdue_maturity > 0 ? 'Action Due' : undefined}
        />
        <StatCard
          title="Discrepancy Alerts"
          value={metrics.records_with_discrepancies}
          subtitle={`${metrics.records_awaiting_review} records in review queue`}
          icon={ShieldAlert}
          color="rose"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution (Pie Chart) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
          <h3 className="text-sm font-bold text-slate-800 mb-4">Lifecycle Status Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.status_distribution}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  paddingAngle={3}
                >
                  {metrics.status_distribution.map((entry) => (
                    <Cell
                      key={entry.status}
                      fill={STATUS_COLORS[entry.status] || '#94a3b8'}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any) => [`${value} FDRs`, name]}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 12-Month Maturity Timeline (Bar Chart) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-800 mb-4">Maturity Timeline Projections (Next 12 Months)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.maturity_timeline}>
                <XAxis dataKey="month_year" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} name="Matures Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Urgent Action Queue Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Priority Follow-up & Urgent Action Queue</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Overdue maturity dates, pending review approvals, and flagged discrepancies
            </p>
          </div>
          <Link
            to="/fdrs"
            className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1"
          >
            View All Records <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">FDR Number</th>
                <th className="py-3 px-4">Institution</th>
                <th className="py-3 px-4">Bank</th>
                <th className="py-3 px-4">Principal</th>
                <th className="py-3 px-4">Maturity Date</th>
                <th className="py-3 px-4">Urgency</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {metrics.urgent_actions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No urgent follow-up items found.
                  </td>
                </tr>
              ) : (
                metrics.urgent_actions.map((act) => (
                  <tr key={act.fdr_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900">
                      {act.fdr_number}
                    </td>
                    <td className="py-3 px-4 text-slate-700 max-w-[200px] truncate" title={act.institution_name}>
                      {act.institution_name}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {act.bank_name}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      ₹{Number(act.principal_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {act.maturity_date}
                      <span className="block text-[10px] text-slate-400">
                        {act.days_to_maturity < 0
                          ? `${Math.abs(act.days_to_maturity)} days overdue`
                          : `${act.days_to_maturity} days left`}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          act.urgency === 'OVERDUE'
                            ? 'bg-rose-100 text-rose-800'
                            : act.urgency === 'CRITICAL'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {act.urgency}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={act.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/fdrs/${act.fdr_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        Review <ArrowUpRight className="w-3 h-3" />
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
