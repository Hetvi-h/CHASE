import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, ShieldCheck, User } from 'lucide-react';

const ACTION_STYLES = {
  login:             { color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: 'Login' },
  risk_prediction:   { color: 'bg-purple-500/15 text-purple-400 border-purple-500/30',   label: 'Risk Prediction' },
  chatbot_query:     { color: 'bg-blue-500/15 text-blue-400 border-blue-500/30',          label: 'Chatbot Query' },
  patrol_allocation: { color: 'bg-amber-500/15 text-amber-400 border-amber-500/30',       label: 'Patrol Plan' },
  pdf_download:      { color: 'bg-pink-500/15 text-pink-400 border-pink-500/30',          label: 'PDF Download' },
  added_case:        { color: 'bg-red-500/15 text-red-400 border-red-500/30',             label: 'Case Filed' },
  viewed_action_plan:{ color: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',          label: 'Action Plan' },
};

export default function AuditLogs({ token }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchLogs = useCallback(() => {
    if (!token) return;
    setLoading(true);
    fetch('http://localhost:8000/audit-logs', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(r => {
      if (!r.ok) throw new Error('Unauthorized');
      return r.json();
    })
    .then(data => {
      setLogs(data.logs || []);
      setIsAdmin(data.logs && data.logs.length > 0 && data.logs.some(l => l.user_email !== data.logs[0].user_email));
      setLastRefresh(new Date());
      setLoading(false);
    })
    .catch(() => {
      setLogs([]);
      setLoading(false);
    });
  }, [token]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const getActionStyle = (action) => {
    return ACTION_STYLES[action] || { color: 'bg-slate-500/15 text-slate-400 border-slate-500/30', label: action };
  };

  const formatTime = (ts) => {
    try {
      return new Date(ts).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    } catch { return ts; }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="text-blue-400" size={24} />
            System Audit Logs
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {isAdmin ? 'Viewing all users (admin mode)' : 'Showing your activity history'} 
            {lastRefresh && <span className="ml-2 text-slate-500">· Last refreshed {lastRefresh.toLocaleTimeString()}</span>}
          </p>
        </div>
        <button
          onClick={fetchLogs}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Summary chips */}
      {logs.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(
            logs.reduce((acc, l) => { acc[l.action] = (acc[l.action] || 0) + 1; return acc; }, {})
          ).map(([action, count]) => {
            const style = getActionStyle(action);
            return (
              <span key={action} className={`text-xs px-3 py-1 rounded-full border font-medium ${style.color}`}>
                {style.label} × {count}
              </span>
            );
          })}
        </div>
      )}

      <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/50 text-slate-400 uppercase tracking-wider text-xs border-b border-slate-700">
              <tr>
                <th className="p-4 font-semibold">Timestamp</th>
                <th className="p-4 font-semibold">User</th>
                <th className="p-4 font-semibold">Action</th>
                <th className="p-4 font-semibold">Details</th>
                <th className="p-4 font-semibold">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                Array.from({length: 5}).map((_, i) => (
                  <tr key={i}>
                    <td colSpan="5" className="p-4">
                      <div className="h-4 bg-slate-700/50 rounded animate-pulse w-full" />
                    </td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-12 text-center">
                    <User size={36} className="text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400 font-medium">No activity logged yet</p>
                    <p className="text-slate-500 text-xs mt-1">Actions like running risk predictions, chatbot queries, and filing cases will appear here.</p>
                  </td>
                </tr>
              ) : logs.map(l => {
                const style = getActionStyle(l.action);
                return (
                  <tr key={l.id} className="hover:bg-slate-700/20 transition-colors">
                    <td className="p-4 font-mono text-xs whitespace-nowrap text-slate-400">{formatTime(l.created_at)}</td>
                    <td className="p-4 text-xs">{l.user_email || '—'}</td>
                    <td className="p-4">
                      <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${style.color}`}>
                        {style.label}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-xs text-slate-400 max-w-xs truncate" title={l.details}>{l.details}</td>
                    <td className="p-4 font-mono text-xs text-slate-500">{l.ip_address || '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
