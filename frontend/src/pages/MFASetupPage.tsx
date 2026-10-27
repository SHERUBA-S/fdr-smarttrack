import React, { useState } from 'react';
import { KeyRound, ShieldCheck, CheckCircle2, Copy, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const MFASetupPage: React.FC = () => {
  const { user, refreshUser } = useAuth();

  const [setupData, setSetupData] = useState<{
    secret: string;
    provisioning_uri: string;
    qr_code_base64: string;
    manual_setup_key: string;
  } | null>(null);

  const [verificationCode, setVerificationCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleStartSetup = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.setupMFA();
      setSetupData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to initiate MFA enrollment');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!setupData || !verificationCode) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.verifyMFAEnrollment(setupData.secret, verificationCode.trim());
      setBackupCodes(res.backup_recovery_codes);
      setSuccess(true);
      await refreshUser();
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check the code in your authenticator.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          Two-Factor Authentication (2FA / TOTP)
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Secure administrative access using standard authenticator apps (Google Authenticator, Microsoft Authenticator)
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-5">
        {/* Status Card */}
        <div className="p-4 rounded-xl border flex items-center justify-between bg-slate-50 border-slate-200">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${user?.is_mfa_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                MFA Status: {user?.is_mfa_enabled ? 'Enabled' : 'Disabled'}
              </h4>
              <p className="text-xs text-slate-500 mt-0.5">
                {user?.is_mfa_enabled
                  ? 'Your account is protected by time-based one-time passwords.'
                  : 'Add an extra layer of protection to your regulatory account.'}
              </p>
            </div>
          </div>
          {!user?.is_mfa_enabled && !setupData && !success && (
            <button
              onClick={handleStartSetup}
              disabled={loading}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Set Up Authenticator'}
            </button>
          )}
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Enrollment Step */}
        {setupData && !success && (
          <div className="space-y-5 pt-3 border-t border-slate-100">
            <div className="text-xs text-slate-600 space-y-1">
              <span className="font-bold text-slate-800">Step 1:</span> Scan the QR code below with your authenticator app (e.g. Google Authenticator or Microsoft Authenticator).
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <img
                src={setupData.qr_code_base64}
                alt="TOTP Enrollment QR Code"
                className="w-40 h-40 bg-white p-2 rounded-lg border border-slate-200 shadow-xs"
              />
              <div className="space-y-2 text-xs">
                <p className="font-semibold text-slate-800">Can't scan the QR code?</p>
                <p className="text-slate-500">
                  Manually enter this 32-character key into your app:
                </p>
                <div className="p-2 bg-white rounded border border-slate-300 font-mono text-[11px] select-all flex items-center justify-between">
                  <span>{setupData.manual_setup_key}</span>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(setupData.manual_setup_key)}
                    className="ml-2 text-slate-400 hover:text-slate-700"
                    title="Copy Key"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            <form onSubmit={handleVerify} className="space-y-3 pt-2">
              <div className="text-xs text-slate-600">
                <span className="font-bold text-slate-800">Step 2:</span> Enter the 6-digit confirmation code generated by your app:
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  maxLength={6}
                  required
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="123456"
                  className="w-48 text-center text-lg font-mono tracking-widest border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs"
                >
                  {loading ? 'Activating...' : 'Verify & Enable 2FA'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Success & Backup Recovery Codes Display */}
        {success && backupCodes.length > 0 && (
          <div className="space-y-4 pt-3 border-t border-slate-100">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <h4 className="font-bold text-sm">Two-Factor Authentication is Active!</h4>
                <p className="mt-0.5">
                  Save these 8 one-time backup recovery codes in a safe place. If you ever lose your authenticator app, you can use these codes to log in.
                </p>
              </div>
            </div>

            <div className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs space-y-2">
              <div className="grid grid-cols-2 gap-2">
                {backupCodes.map((c, idx) => (
                  <div key={idx} className="bg-slate-800 p-2 rounded text-center font-bold tracking-wider">
                    {c}
                  </div>
                ))}
              </div>
            </div>

            <p className="text-[11px] text-slate-500">
              Note: Each recovery code can only be used once. They are stored as SHA-256 hashes on the server.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
