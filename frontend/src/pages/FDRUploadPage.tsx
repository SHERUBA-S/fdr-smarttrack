import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowLeft,
  RefreshCw, Check, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { FDRRecord } from '../types';

export const FDRUploadPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isJustCreated = searchParams.get('created') === '1';

  const [fdr, setFdr] = useState<FDRRecord | null>(null);
  const [loadingFdr, setLoadingFdr] = useState(true);

  // Upload states
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('FDR_RECEIPT');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const data = await api.getFDR(id);
        setFdr(data);
      } catch (err: any) {
        setError(err.message || 'Failed loading FDR');
      } finally {
        setLoadingFdr(false);
      }
    };
    load();
  }, [id]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !file) return;

    setUploading(true);
    setError(null);

    try {
      const res = await api.uploadDocument(id, file, docType);
      setUploadSuccess(res);
    } catch (err: any) {
      setError(err.message || 'Upload processing failed');
    } finally {
      setUploading(false);
    }
  };

  if (loadingFdr) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mb-2" />
        <p className="text-sm">Loading record details...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to={id ? `/fdrs/${id}` : '/fdrs'}
          className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Upload Supporting FDR Document
          </h1>
          <p className="text-xs text-slate-500 font-mono">
            Attaching document to FDR #{fdr?.fdr_number} ({fdr?.bank_name})
          </p>
        </div>
      </div>

      {isJustCreated && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>FDR record registered! Now upload the official scanned PDF/image for automated verification.</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!uploadSuccess ? (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
          <form onSubmit={handleUpload} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Document Classification
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
              >
                <option value="FDR_RECEIPT">Original Fixed Deposit Receipt (FDR)</option>
                <option value="RENEWAL_LETTER">Bank Renewal / Extension Letter</option>
                <option value="RELEASE_APPROVAL">Clearance / Release NOC Certificate</option>
                <option value="BANK_CONFIRMATION">Bank Official Confirmation Letter</option>
                <option value="OTHER">Other Regulatory Deposit Document</option>
              </select>
            </div>

            {/* Drag & Drop Area */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Select File (PDF, PNG, JPEG &bull; Max 10MB)
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-xl hover:border-blue-500 transition-colors bg-slate-50/50">
                <div className="space-y-1 text-center">
                  <UploadCloud className="mx-auto h-10 w-10 text-slate-400" />
                  <div className="flex text-xs text-slate-600 justify-center">
                    <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-hidden">
                      <span>Click to choose file</span>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={handleFileChange}
                        className="sr-only"
                      />
                    </label>
                    <p className="pl-1 text-slate-500">or drag and drop here</p>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    PDF with selectable text or high-resolution scanned receipt
                  </p>
                </div>
              </div>

              {file && (
                <div className="mt-3 p-3 bg-blue-50/60 rounded-lg border border-blue-200 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-slate-800 font-medium">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span>{file.name}</span>
                    <span className="text-[11px] text-slate-400">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
              <Link
                to={id ? `/fdrs/${id}` : '/fdrs'}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Skip for Now
              </Link>
              <button
                type="submit"
                disabled={!file || uploading}
                className="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Executing OCR Extraction...
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    Upload & Run AI-Assisted OCR
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      ) : (
        /* Upload & OCR Results Review */
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center gap-3 text-emerald-700 bg-emerald-50 p-4 rounded-xl border border-emerald-200">
            <CheckCircle2 className="w-6 h-6 shrink-0" />
            <div>
              <h4 className="font-bold text-sm">Upload & OCR Extraction Completed!</h4>
              <p className="text-xs text-emerald-600 mt-0.5">
                File hash verified &bull; Structured fields parsed &bull; Integrity checks executed
              </p>
            </div>
          </div>

          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Extracted Fields Preview ({uploadSuccess.extracted_fields?.length || 0} fields detected)
            </h4>
            <div className="space-y-2">
              {uploadSuccess.extracted_fields?.map((f: any) => (
                <div key={f.id} className="bg-white p-2.5 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700 capitalize">
                    {f.field_name.replace('_', ' ')}
                  </span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-slate-900">{f.extracted_value || '<None>'}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-sans font-bold">
                      {Math.round(f.confidence * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => { setUploadSuccess(null); setFile(null); }}
              className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100"
            >
              Upload Another Document
            </button>
            <button
              onClick={() => navigate(`/fdrs/${id}`)}
              className="px-5 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            >
              Go to FDR Record Detail <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
