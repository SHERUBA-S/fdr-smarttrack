import React, { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { ShieldCheck, KeyRound, ArrowRight, Lock, Mail, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isRegisteredSuccess = searchParams.get('registered') === '1';
  const { login, mfaChallenge } = useAuth();

  const [email, setEmail] = useState('admin@smarttrack.gov.in');
  const [password, setPassword] = useState('AdminPassword@123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // MFA Challenge State
  const [mfaPending, setMfaPending] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [useRecovery, setUseRecovery] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (res.requires_mfa) {
        setMfaPending(true);
        setTempToken(res.temp_mfa_token);
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMFAChallenge = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await mfaChallenge(
        tempToken,
        useRecovery ? undefined : totpCode,
        useRecovery ? recoveryCode : undefined
      );
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'MFA validation failed');
    } finally {
      setLoading(false);
    }
  };

  const setDemoAccount = (demEmail: string, demPass: string) => {
    setEmail(demEmail);
    setPassword(demPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg mb-3">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          FDR Guardian Portal
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Intelligent Security Deposit & FDR Lifecycle Management (SIH26265)
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-100">
          {isRegisteredSuccess && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Registration completed! Please sign in with your registered email and password.</span>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!mfaPending ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                    placeholder="official@smarttrack.gov.in"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Sign In'}
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>
          ) : (
            /* MFA Challenge Modal View */
            <form onSubmit={handleMFAChallenge} className="space-y-4">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center gap-2">
                <KeyRound className="w-5 h-5 shrink-0 text-blue-600" />
                <span>Two-Factor Authentication is active on your account.</span>
              </div>

              {!useRecovery ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Authenticator Code (6 Digits)
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    required
                    autoFocus
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value)}
                    className="w-full text-center tracking-widest text-lg font-mono py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                    placeholder="123456"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Backup Recovery Code (e.g. A1B2-C3D4)
                  </label>
                  <input
                    type="text"
                    required
                    autoFocus
                    value={recoveryCode}
                    onChange={(e) => setRecoveryCode(e.target.value)}
                    className="w-full text-center font-mono py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                    placeholder="XXXX-XXXX"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Verify Code & Sign In'}
              </button>

              <button
                type="button"
                onClick={() => setUseRecovery(!useRecovery)}
                className="w-full text-center text-xs text-blue-600 hover:underline pt-2 block"
              >
                {useRecovery ? 'Use Authenticator Code Instead' : 'Lost device? Use a Backup Recovery Code'}
              </button>
            </form>
          )}

          {/* Registration Link */}
          <div className="mt-4 pt-3 text-center border-t border-slate-100">
            <p className="text-xs text-slate-600">
              Need access?{' '}
              <Link to="/register" className="text-blue-700 hover:text-blue-800 font-semibold hover:underline">
                Create new FDR Officer or Reviewer account
              </Link>
            </p>
          </div>

          {/* Quick Demo Credentials Switcher */}
          <div className="mt-5 pt-4 border-t border-slate-200">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Select Demo Persona (Click to autofill)
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoAccount('admin@smarttrack.gov.in', 'AdminPassword@123')}
                className="p-2 border border-slate-200 rounded-lg text-left hover:border-blue-500 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-semibold text-slate-800">Super Admin</div>
                <div className="text-[10px] text-slate-500">Full platform controls</div>
              </button>

              <button
                type="button"
                onClick={() => setDemoAccount('reviewer@smarttrack.gov.in', 'ReviewerPassword@123')}
                className="p-2 border border-slate-200 rounded-lg text-left hover:border-blue-500 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-semibold text-slate-800">Reviewer</div>
                <div className="text-[10px] text-slate-500">Verification & queue</div>
              </button>

              <button
                type="button"
                onClick={() => setDemoAccount('institution@smarttrack.gov.in', 'DemoPassword@123')}
                className="p-2 border border-slate-200 rounded-lg text-left hover:border-blue-500 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-semibold text-slate-800">Institution</div>
                <div className="text-[10px] text-slate-500">Tenant-isolated user</div>
              </button>

              <button
                type="button"
                onClick={() => setDemoAccount('auditor@smarttrack.gov.in', 'AuditorPassword@123')}
                className="p-2 border border-slate-200 rounded-lg text-left hover:border-blue-500 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-semibold text-slate-800">Auditor</div>
                <div className="text-[10px] text-slate-500">Read-only audit trail</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
