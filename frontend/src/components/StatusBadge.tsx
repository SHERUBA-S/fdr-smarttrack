import React from 'react';
import { FDRStatus, VerificationOutcome } from '../types';

interface StatusBadgeProps {
  status: FDRStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (status) {
    case 'Approved':
    case 'Verified by Authorized Source':
    case 'Passed':
      colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'Submitted':
    case 'Under Review':
    case 'Manually Reviewed':
      colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'Renewal Pending':
    case 'Release Requested':
      colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
    case 'Additional Information Required':
    case 'Warning':
      colorClasses = 'bg-orange-50 text-orange-700 border-orange-200';
      break;
    case 'Rejected':
    case 'Expired':
    case 'Failed':
      colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
      break;
    case 'Awaiting External Verification':
      colorClasses = 'bg-purple-50 text-purple-700 border-purple-200';
      break;
    default:
      colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  }

  const px = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${px} ${colorClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-70" />
      {status}
    </span>
  );
};
