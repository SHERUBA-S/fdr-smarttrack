import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, Filter, Plus, FileText, Upload, AlertTriangle,
  ChevronLeft, ChevronRight, RefreshCw, ArrowUpDown
} from 'lucide-react';
import { api } from '../services/api';
import { FDRRecord, FDRStatus } from '../types';
import { StatusBadge } from '../components/StatusBadge';

const STATUS_OPTIONS: FDRStatus[] = [
  'Draft', 'Submitted', 'Under Review', 'Additional Information Required',
  'Approved', 'Renewal Pending', 'Release Requested', 'Released', 'Expired'
];

export const FDRListPage: React.FC = () => {
  const [fdrs, setFdrs] = useState<FDRRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [bankFilter, setBankFilter] = useState('');
  const [hasDiscrepancyFilter, setHasDiscrepancyFilter] = useState<boolean | undefined>(undefined);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const data = await api.getFDRs({
        page,
        page_size: 15,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        bank_name: bankFilter.trim() || undefined,
        has_discrepancy: hasDiscrepancyFilter,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setFdrs(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [page, statusFilter, bankFilter, hasDiscrepancyFilter, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchRecords();
  };

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
  };

  return (
    <div className="space-y-5">
      {/* Page Title & Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Fixed Deposit Receipts (FDR)</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage institutional security deposits, verification checks, and maturities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/fdrs/create"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" /> Create FDR Record
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by FDR number, bank name, or purpose..."
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
            >
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>

            <select
              value={hasDiscrepancyFilter === undefined ? '' : String(hasDiscrepancyFilter)}
              onChange={(e) => {
                const v = e.target.value;
                setHasDiscrepancyFilter(v === '' ? undefined : v === 'true');
                setPage(1);
              }}
              className="px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
            >
              <option value="">All Integrity States</option>
              <option value="true">Flagged Discrepancies</option>
              <option value="false">Verified Consistent</option>
            </select>

            <button
              type="submit"
              className="px-3 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Filter
            </button>
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setStatusFilter('');
                setBankFilter('');
                setHasDiscrepancyFilter(undefined);
                setPage(1);
              }}
              className="px-3 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-lg transition-colors"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 cursor-pointer" onClick={() => toggleSort('fdr_number')}>
                  <div className="flex items-center gap-1">FDR Number <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4">Bank & Branch</th>
                <th className="py-3 px-4 cursor-pointer" onClick={() => toggleSort('principal_amount')}>
                  <div className="flex items-center gap-1">Principal Amount <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 cursor-pointer" onClick={() => toggleSort('issue_date')}>
                  <div className="flex items-center gap-1">Issue Date <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 cursor-pointer" onClick={() => toggleSort('maturity_date')}>
                  <div className="flex items-center gap-1">Maturity Date <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Verification</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                    Loading records from PostgreSQL database...
                  </td>
                </tr>
              ) : fdrs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No matching FDR records found.
                  </td>
                </tr>
              ) : (
                fdrs.map((fdr) => (
                  <tr key={fdr.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900">
                      <Link to={`/fdrs/${fdr.id}`} className="text-blue-600 hover:underline">
                        {fdr.fdr_number}
                      </Link>
                      {fdr.has_discrepancy && (
                        <span className="ml-1.5 inline-flex items-center text-[10px] text-rose-600 font-semibold" title={fdr.discrepancy_notes || 'Discrepancy detected'}>
                          <AlertTriangle className="w-3 h-3 mr-0.5" /> Flagged
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-700">
                      <div className="font-medium text-slate-900">{fdr.bank_name}</div>
                      <div className="text-[10px] text-slate-400">{fdr.branch_name || 'Main Branch'}</div>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      ₹{Number(fdr.principal_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{fdr.issue_date}</td>
                    <td className="py-3 px-4 text-slate-600 font-medium">{fdr.maturity_date}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={fdr.status} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                        fdr.verification_status === 'Passed' ? 'bg-emerald-100 text-emerald-800' :
                        fdr.verification_status === 'Failed' ? 'bg-rose-100 text-rose-800' :
                        fdr.verification_status === 'Warning' ? 'bg-amber-100 text-amber-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {fdr.verification_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <Link
                        to={`/fdrs/${fdr.id}`}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        View
                      </Link>
                      <Link
                        to={`/fdrs/${fdr.id}/upload`}
                        className="text-xs font-medium text-slate-500 hover:text-slate-800"
                        title="Upload Document"
                      >
                        Upload
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="py-3 px-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 bg-slate-50">
          <div>
            Showing <span className="font-semibold text-slate-800">{fdrs.length}</span> of <span className="font-semibold text-slate-800">{total}</span> records
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1.5 border border-slate-300 rounded-lg hover:bg-slate-200/50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-medium text-slate-700">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1.5 border border-slate-300 rounded-lg hover:bg-slate-200/50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
