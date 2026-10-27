import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import { api } from '../services/api';
import { Institution, Bank } from '../types';
import { useAuth } from '../context/AuthContext';

export const FDRCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [banks, setBanks] = useState<Bank[]>([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Form states
  const [fdrNumber, setFdrNumber] = useState('');
  const [institutionId, setInstitutionId] = useState('');
  const [bankName, setBankName] = useState('State Bank of India');
  const [branchName, setBranchName] = useState('Main Commercial Branch');
  const [principalAmount, setPrincipalAmount] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [interestRate, setInterestRate] = useState('7.10');
  const [issueDate, setIssueDate] = useState('');
  const [maturityDate, setMaturityDate] = useState('');
  const [purpose, setPurpose] = useState('AICTE Regulatory Approval Security Deposit');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [instList, bankList] = await Promise.all([
          api.getInstitutions(),
          api.getBanks()
        ]);
        setInstitutions(instList);
        setBanks(bankList);

        // Preselect institution if institution user
        if (user?.institution_id) {
          setInstitutionId(user.institution_id);
        } else if (instList.length > 0) {
          setInstitutionId(instList[0].id);
        }
      } catch (err: any) {
        setError('Failed loading institutions or banks');
      } finally {
        setLoadingInitial(false);
      }
    };
    loadData();
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (new Date(maturityDate) <= new Date(issueDate)) {
      setError('Maturity date must be strictly after issue date.');
      return;
    }

    if (Number(principalAmount) <= 0) {
      setError('Principal amount must be greater than zero.');
      return;
    }

    setSubmitting(true);
    try {
      const created = await api.createFDR({
        fdr_number: fdrNumber.trim(),
        institution_id: institutionId,
        bank_name: bankName.trim(),
        branch_name: branchName.trim() || undefined,
        principal_amount: principalAmount,
        currency,
        interest_rate: interestRate ? interestRate : undefined,
        issue_date: issueDate,
        maturity_date: maturityDate,
        purpose: purpose.trim()
      });

      // Redirect directly to document upload page for this FDR
      navigate(`/fdrs/${created.id}/upload?created=1`);
    } catch (err: any) {
      setError(err.message || 'Failed to create FDR record');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingInitial) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mb-2" />
        <p className="text-sm">Preparing registration form...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <Link
          to="/fdrs"
          className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Register New Fixed Deposit Receipt
          </h1>
          <p className="text-xs text-slate-500">
            Record administrative details and deposit parameters for compliance tracking
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                FDR Reference / Receipt Number *
              </label>
              <input
                type="text"
                required
                value={fdrNumber}
                onChange={(e) => setFdrNumber(e.target.value)}
                placeholder="e.g. FDR/SBI/2026/099881"
                className="w-full text-xs font-mono border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Institution *
              </label>
              <select
                required
                disabled={user?.role === 'INSTITUTION_USER' && Boolean(user?.institution_id)}
                value={institutionId}
                onChange={(e) => setInstitutionId(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-hidden disabled:bg-slate-100"
              >
                {institutions.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name} ({i.code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Issuing Bank Name *
              </label>
              <input
                type="text"
                required
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="e.g. State Bank of India"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Branch Name
              </label>
              <input
                type="text"
                value={branchName}
                onChange={(e) => setBranchName(e.target.value)}
                placeholder="e.g. Sansad Marg Main Branch"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Principal Amount (INR) *
              </label>
              <input
                type="number"
                step="0.01"
                min="1"
                required
                value={principalAmount}
                onChange={(e) => setPrincipalAmount(e.target.value)}
                placeholder="e.g. 500000.00"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Interest Rate (% p.a.)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="30"
                value={interestRate}
                onChange={(e) => setInterestRate(e.target.value)}
                placeholder="e.g. 7.10"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Issue / Opening Date *
              </label>
              <input
                type="date"
                required
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Maturity Date *
              </label>
              <input
                type="date"
                required
                min={issueDate || undefined}
                value={maturityDate}
                onChange={(e) => setMaturityDate(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Purpose / Statutory Guarantee Category
            </label>
            <input
              type="text"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
            />
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <Link
              to="/fdrs"
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save & Proceed to Document Upload
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
