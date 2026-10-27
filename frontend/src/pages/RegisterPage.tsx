import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, UserCheck, Lock, Mail, User, Building2, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { Institution, UserRole } from '../types';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'INSTITUTION_USER' | 'REVIEWING_OFFICIAL'>('INSTITUTION_USER');
  const [institutionId, setInstitutionId] = useState('');
  const [institutions, setInstitutions] = useState<Institution[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const loadInstitutions = async () => {
      try {
        const instList = await api.getPublicInstitutions();
        setInstitutions(instList);
        if (instList.length > 0) {
          setInstitutionId(instList[0].id);
        }
      } catch (err) {
        console.warn('Could not load public institutions:', err);
      }
    };
    loadInstitutions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setLoading(true);
    try {
      const cleanInstId = institutionId ? institutionId.trim() : '';
      await api.register({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role: role as UserRole,
        institution_id: (role === 'INSTITUTION_USER' && cleanInstId) ? cleanInstId : undefined
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/login?registered=1');
      }, 1800);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
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
          Create an official account for FDR lifecycle and deposit compliance (SIH26265)
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-100">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>Account registered in PostgreSQL! Redirecting to Sign In...</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Full Name *
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  placeholder="e.g. Dr. Rajesh Kumar"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Email Address *
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  placeholder="officer@institution.edu.in"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Designated Operational Role *
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('INSTITUTION_USER')}
                  className={`p-2.5 rounded-lg border text-left transition-colors ${
                    role === 'INSTITUTION_USER'
                      ? 'border-blue-600 bg-blue-50/50 text-blue-900 font-semibold ring-1 ring-blue-600'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="text-xs font-bold">FDR Officer</div>
                  <div className="text-[10px] text-slate-500">Institution deposit submitter</div>
                </button>

                <button
                  type="button"
                  onClick={() => setRole('REVIEWING_OFFICIAL')}
                  className={`p-2.5 rounded-lg border text-left transition-colors ${
                    role === 'REVIEWING_OFFICIAL'
                      ? 'border-blue-600 bg-blue-50/50 text-blue-900 font-semibold ring-1 ring-blue-600'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="text-xs font-bold">Reviewer</div>
                  <div className="text-[10px] text-slate-500">Verification & clearance</div>
                </button>
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                Note: Super Administrator privileges can only be provisioned by existing system admins.
              </p>
            </div>

            {role === 'INSTITUTION_USER' && institutions.length > 0 && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Affiliated Institution *
                </label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden bg-white"
                  >
                    <option value="">-- Select Institution (Optional) --</option>
                    {institutions.map((i) => (
                      <option key={i.id} value={i.id}>
                        {i.name} ({i.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password * (min 8 characters)
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  placeholder="Create secure password"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Confirm Password *
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  placeholder="Re-enter password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full py-2.5 px-4 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50 mt-2"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4" />}
              {loading ? 'Registering Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-5 text-center pt-4 border-t border-slate-200">
            <p className="text-xs text-slate-600">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-700 hover:text-blue-800 font-semibold hover:underline">
                Sign In here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
