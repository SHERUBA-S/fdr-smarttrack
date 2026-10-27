import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FileText, ShieldCheck, AlertTriangle, CheckCircle, RefreshCw,
  Upload, ExternalLink, Calendar, Building, IndianRupee, Key, Clock, Edit3, Save, X
} from 'lucide-react';
import { api } from '../services/api';
import { FDRRecord, VerificationOutcome } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const FDRDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [fdr, setFdr] = useState<FDRRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Field editing state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [correctedValue, setCorrectedValue] = useState('');

  // Workflow Dialog States
  const [renewalOpen, setRenewalOpen] = useState(false);
  const [newMaturityDate, setNewMaturityDate] = useState('');
  const [renewalRationale, setRenewalRationale] = useState('');

  const [releaseOpen, setReleaseOpen] = useState(false);
  const [clearanceRef, setClearanceRef] = useState('');
  const [releaseRationale, setReleaseRationale] = useState('');

  const [decisionOpen, setDecisionOpen] = useState(false);
  const [decisionType, setDecisionType] = useState('APPROVE');
  const [decisionReason, setDecisionReason] = useState('');

  const [actionLoading, setActionLoading] = useState(false);

  const fetchFDR = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await api.getFDR(id);
      setFdr(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load FDR record');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFDR();
  }, [id]);

  const handleCorrectField = async (fieldId: string) => {
    if (!correctedValue.trim()) return;
    try {
      await api.correctField(fieldId, correctedValue.trim());
      setEditingFieldId(null);
      fetchFDR();
    } catch (err: any) {
      alert(err.message || 'Failed to update field');
    }
  };

  const handleTriggerVerify = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.verifyFDR(id);
      fetchFDR();
    } catch (err: any) {
      alert(err.message || 'Verification execution failed');
    } finally {
      setActionLoading(false);
    }
  };

  const submitRenewal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newMaturityDate || !renewalRationale) return;
    setActionLoading(true);
    try {
      await api.renewFDR(id, newMaturityDate, renewalRationale);
      setRenewalOpen(false);
      fetchFDR();
    } catch (err: any) {
      alert(err.message || 'Renewal request failed');
    } finally {
      setActionLoading(false);
    }
  };

  const submitRelease = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !clearanceRef || !releaseRationale) return;
    setActionLoading(true);
    try {
      await api.releaseFDR(id, clearanceRef, releaseRationale);
      setReleaseOpen(false);
      fetchFDR();
    } catch (err: any) {
      alert(err.message || 'Release request failed');
    } finally {
      setActionLoading(false);
    }
  };

  const submitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !decisionReason) return;
    setActionLoading(true);
    try {
      let targetStatus = 'Approved';
      if (decisionType === 'REJECT') targetStatus = 'Rejected';
      if (decisionType === 'REQUEST_INFO') targetStatus = 'Additional Information Required';
      if (decisionType === 'RELEASE') targetStatus = 'Released';

      await api.decideFDR(id, decisionType, targetStatus, decisionReason);
      setDecisionOpen(false);
      fetchFDR();
    } catch (err: any) {
      alert(err.message || 'Decision failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mb-2" />
        <p className="text-sm">Loading FDR record details...</p>
      </div>
    );
  }

  if (error || !fdr) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm">
        {error || 'FDR record not found.'}
      </div>
    );
  }

  const isReviewerOrAdmin = user && ['SUPER_ADMIN', 'REVIEWING_OFFICIAL'].includes(user.role);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 font-mono">
              FDR #{fdr.fdr_number}
            </h1>
            <StatusBadge status={fdr.status} />
            {fdr.has_discrepancy && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-700">
                <AlertTriangle className="w-3.5 h-3.5" /> Discrepancy Flagged
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {fdr.bank_name} &bull; {fdr.purpose} &bull; Registered on {new Date(fdr.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleTriggerVerify}
            disabled={actionLoading}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
          >
            <ShieldCheck className="w-4 h-4 text-blue-600" /> Re-run Verification
          </button>

          <Link
            to={`/fdrs/${fdr.id}/upload`}
            className="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
          >
            <Upload className="w-4 h-4" /> Upload Document
          </Link>

          {/* Renewal Request */}
          {['Approved', 'Submitted'].includes(fdr.status) && (
            <button
              onClick={() => setRenewalOpen(true)}
              className="px-3.5 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Request Renewal
            </button>
          )}

          {/* Release Request */}
          {['Approved'].includes(fdr.status) && (
            <button
              onClick={() => setReleaseOpen(true)}
              className="px-3.5 py-2 bg-purple-50 hover:bg-purple-100 text-purple-800 text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Request Release
            </button>
          )}

          {/* Review Decision Button */}
          {isReviewerOrAdmin && (
            <button
              onClick={() => setDecisionOpen(true)}
              className="px-3.5 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
            >
              Review Decision
            </button>
          )}
        </div>
      </div>

      {/* Discrepancy Note Alert */}
      {fdr.has_discrepancy && fdr.discrepancy_notes && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">Automated Integrity Warning</h4>
            <p className="mt-0.5 leading-relaxed">{fdr.discrepancy_notes}</p>
          </div>
        </div>
      )}

      {/* Core Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Principal Amount</div>
          <div className="text-xl font-bold text-slate-900 mt-1">
            ₹{Number(fdr.principal_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Currency: {fdr.currency}</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Tenure & Dates</div>
          <div className="text-sm font-semibold text-slate-900 mt-1">
            {fdr.issue_date} &rarr; {fdr.maturity_date}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            ROI: {fdr.interest_rate ? `${fdr.interest_rate}% p.a.` : 'Standard'}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Issuing Bank</div>
          <div className="text-sm font-semibold text-slate-900 mt-1 truncate" title={fdr.bank_name}>
            {fdr.bank_name}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">{fdr.branch_name || 'Main Commercial Branch'}</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Anomaly Priority Score</div>
          <div className="text-xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <span>{fdr.anomaly_score !== null && fdr.anomaly_score !== undefined ? fdr.anomaly_score : '0.05'}</span>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
              (fdr.anomaly_score || 0) > 0.5 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
            }`}>
              {(fdr.anomaly_score || 0) > 0.5 ? 'High Review Priority' : 'Normal Baseline'}
            </span>
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">ML IsolationForest experimental signal</div>
        </div>
      </div>

      {/* OCR Extraction Review Section */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Document Processing & OCR Extraction Review</h3>
            <p className="text-xs text-slate-500">
              Side-by-side comparison with provenance tracking and field correction
            </p>
          </div>
          <span className="text-xs text-slate-500">
            {fdr.documents.length} Document(s) attached
          </span>
        </div>

        {fdr.documents.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No document attached yet. Upload a scanned receipt or PDF to extract fields automatically.
          </div>
        ) : (
          fdr.documents.map((doc) => (
            <div key={doc.id} className="border border-slate-200 rounded-lg p-4 space-y-3 bg-slate-50/50">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span>{doc.file_name}</span>
                  <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded-sm">
                    {doc.ocr_status}
                  </span>
                </div>
                <a
                  href={`/api/v1/documents/${doc.id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1 font-medium"
                >
                  Download / View File <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              {/* Extracted Fields Table */}
              <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Field Name</th>
                      <th className="py-2.5 px-3">OCR Extracted Value</th>
                      <th className="py-2.5 px-3">Calibrated Confidence</th>
                      <th className="py-2.5 px-3">User Corrected Value</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {doc.extracted_fields.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-slate-400 text-xs">
                          No structured fields parsed from document text.
                        </td>
                      </tr>
                    ) : (
                      doc.extracted_fields.map((f) => (
                        <tr key={f.id} className="hover:bg-slate-50/60">
                          <td className="py-2.5 px-3 font-semibold text-slate-800 capitalize">
                            {f.field_name.replace('_', ' ')}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-700">
                            {f.extracted_value || '<Not Detected>'}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                              f.confidence >= 0.8 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                            }`}>
                              {Math.round(f.confidence * 100)}%
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            {editingFieldId === f.id ? (
                              <input
                                type="text"
                                autoFocus
                                value={correctedValue}
                                onChange={(e) => setCorrectedValue(e.target.value)}
                                className="w-full px-2 py-1 text-xs border border-blue-400 rounded focus:outline-hidden"
                              />
                            ) : (
                              <span className={f.is_corrected ? 'font-semibold text-blue-700' : 'text-slate-400'}>
                                {f.user_corrected_value || (f.is_corrected ? 'Updated' : '—')}
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {editingFieldId === f.id ? (
                              <div className="flex items-center justify-end gap-1">
                                <button
                                  onClick={() => handleCorrectField(f.id)}
                                  className="p-1 bg-emerald-600 text-white rounded hover:bg-emerald-700"
                                  title="Save"
                                >
                                  <Save className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => setEditingFieldId(null)}
                                  className="p-1 bg-slate-200 text-slate-600 rounded hover:bg-slate-300"
                                  title="Cancel"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  setEditingFieldId(f.id);
                                  setCorrectedValue(f.user_corrected_value || f.extracted_value || '');
                                }}
                                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                              >
                                <Edit3 className="w-3 h-3" /> Correct
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Verification Engine Results Section */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Deterministic Verification Checks & Disclaimers</h3>
            <p className="text-xs text-slate-500">
              Rule-based integrity engine evaluating fields, tenure, bank uniqueness, and document alignment
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
            {fdr.verification_checks.length} Checks Run
          </span>
        </div>

        <div className="space-y-3">
          {fdr.verification_checks.map((check) => (
            <div
              key={check.id}
              className={`p-3.5 rounded-lg border text-xs transition-colors ${
                check.outcome === 'Passed' ? 'bg-emerald-50/40 border-emerald-200' :
                check.outcome === 'Failed' ? 'bg-rose-50/40 border-rose-200' :
                check.outcome === 'Warning' ? 'bg-amber-50/40 border-amber-200' :
                'bg-purple-50/40 border-purple-200'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 font-bold text-slate-900">
                  {check.outcome === 'Passed' && <CheckCircle className="w-4 h-4 text-emerald-600" />}
                  {check.outcome === 'Failed' && <AlertTriangle className="w-4 h-4 text-rose-600" />}
                  {check.outcome === 'Warning' && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                  {check.outcome === 'Awaiting External Verification' && <ShieldCheck className="w-4 h-4 text-purple-600" />}
                  <span>{check.check_name}</span>
                </div>
                <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                  check.outcome === 'Passed' ? 'bg-emerald-200/60 text-emerald-900' :
                  check.outcome === 'Failed' ? 'bg-rose-200/60 text-rose-900' :
                  check.outcome === 'Warning' ? 'bg-amber-200/60 text-amber-900' :
                  'bg-purple-200/60 text-purple-900'
                }`}>
                  {check.outcome}
                </span>
              </div>
              <p className="text-slate-700 leading-relaxed mt-1">{check.explanation}</p>
              {check.evidence && (
                <div className="mt-1.5 font-mono text-[11px] text-slate-600 bg-white/70 p-2 rounded border border-slate-200/50">
                  <span className="font-semibold text-slate-800">Evidence:</span> {check.evidence}
                </div>
              )}
              {check.recommended_action && (
                <p className="mt-1.5 text-slate-500 font-medium">
                  <span className="font-semibold text-slate-700">Recommended Action:</span> {check.recommended_action}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Renewal Dialog Modal */}
      {renewalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white max-w-md w-full rounded-2xl p-6 shadow-2xl border border-slate-100">
            <h3 className="text-base font-bold text-slate-900">Submit FDR Renewal Request</h3>
            <p className="text-xs text-slate-500 mt-1">
              Current Maturity Date: {fdr.maturity_date}
            </p>
            <form onSubmit={submitRenewal} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  New Extended Maturity Date
                </label>
                <input
                  type="date"
                  required
                  min={fdr.maturity_date}
                  value={newMaturityDate}
                  onChange={(e) => setNewMaturityDate(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Renewal Rationale / Statutory Purpose
                </label>
                <textarea
                  required
                  rows={3}
                  value={renewalRationale}
                  onChange={(e) => setRenewalRationale(e.target.value)}
                  placeholder="State the institutional reason for extension..."
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRenewalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs bg-blue-700 hover:bg-blue-800 text-white font-semibold rounded-lg shadow-xs"
                >
                  {actionLoading ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Release Dialog Modal */}
      {releaseOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white max-w-md w-full rounded-2xl p-6 shadow-2xl border border-slate-100">
            <h3 className="text-base font-bold text-slate-900">Submit Security Deposit Release Request</h3>
            <form onSubmit={submitRelease} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Clearance / NOC Reference Number
                </label>
                <input
                  type="text"
                  required
                  value={clearanceRef}
                  onChange={(e) => setClearanceRef(e.target.value)}
                  placeholder="e.g. NOC-AICTE-2026-XXXX"
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Justification / Regulatory Clearance Notes
                </label>
                <textarea
                  required
                  rows={3}
                  value={releaseRationale}
                  onChange={(e) => setReleaseRationale(e.target.value)}
                  placeholder="Details of fulfilled obligations..."
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReleaseOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs bg-purple-700 hover:bg-purple-800 text-white font-semibold rounded-lg shadow-xs"
                >
                  {actionLoading ? 'Submitting...' : 'Submit Release Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review Decision Modal */}
      {decisionOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white max-w-md w-full rounded-2xl p-6 shadow-2xl border border-slate-100">
            <h3 className="text-base font-bold text-slate-900">Record Review Decision</h3>
            <form onSubmit={submitDecision} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Action Decision Type
                </label>
                <select
                  value={decisionType}
                  onChange={(e) => setDecisionType(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                >
                  <option value="APPROVE">Approve FDR Record</option>
                  <option value="RENEW">Approve Renewal Request</option>
                  <option value="RELEASE">Approve Security Deposit Release</option>
                  <option value="REQUEST_INFO">Request Additional Information</option>
                  <option value="REJECT">Reject Record / Request</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Official Decision Reason & Commentary
                </label>
                <textarea
                  required
                  rows={3}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="Record justification for official audit log..."
                  className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setDecisionOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 text-xs bg-blue-700 hover:bg-blue-800 text-white font-semibold rounded-lg shadow-xs"
                >
                  {actionLoading ? 'Recording...' : 'Record Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
