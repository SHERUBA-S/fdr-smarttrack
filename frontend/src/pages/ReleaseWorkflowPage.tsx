import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Unlock, ArrowUpRight, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { FDRRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const ReleaseWorkflowPage: React.FC = () => {
  const [fdrs, setFdrs] = useState<FDRRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReleases = async () => {
    setLoading(true);
    try {
      const data = await api.getFDRs({
        page: 1,
        page_size: 50,
        status: 'Release Requested'
      });
      setFdrs(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReleases();
  }, []);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Security Deposit Release Workflow
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Clearance verification and release requests for completed statutory guarantee obligations
          </p>
        </div>
        <button
          onClick={fetchReleases}
          className="p-2 border border-slate-200 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">FDR Number</th>
                <th className="py-3 px-4">Bank Name</th>
                <th className="py-3 px-4">Principal Amount</th>
                <th className="py-3 px-4">Maturity Date</th>
                <th className="py-3 px-4">Current Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                    Loading release requests...
                  </td>
                </tr>
              ) : fdrs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    No release requests currently awaiting official decision.
                  </td>
                </tr>
              ) : (
                fdrs.map((fdr) => (
                  <tr key={fdr.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900">
                      <Link to={`/fdrs/${fdr.id}`} className="text-blue-600 hover:underline">
                        {fdr.fdr_number}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-slate-700">{fdr.bank_name}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      ₹{Number(fdr.principal_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-medium">{fdr.maturity_date}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={fdr.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/fdrs/${fdr.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-purple-700 hover:text-purple-900"
                      >
                        Review Clearance <ArrowUpRight className="w-3 h-3" />
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
