import React from 'react';
import { AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

export default function Toast({ toast, onClose }) {
  if (!toast) return null;

  const styles = {
    success: { badge: 'cyber-badge-green', Icon: CheckCircle },
    error:   { badge: 'cyber-badge-pink',  Icon: AlertTriangle },
    info:    { badge: 'cyber-badge-cyan',  Icon: Info },
  };

  const s = styles[toast.type] || styles.info;
  const Icon = s.Icon;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce-short">
      <div className={`cyber-badge ${s.badge} py-3 px-5 flex items-center gap-3 text-xs shadow-[5px_5px_0px_#000]`}>
        <Icon size={18} />
        <span className="font-mono font-extrabold">{toast.message}</span>
        <button onClick={onClose} className="ml-2 p-1 hover:opacity-75">
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
