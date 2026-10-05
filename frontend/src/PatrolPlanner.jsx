import React, { useState, useEffect } from 'react';
import { Users, AlertTriangle } from 'lucide-react';

export default function PatrolPlanner({ token,  selectedCity, zoneScores }) {
  const [totalUnits, setTotalUnits] = useState(50);
  const [allocations, setAllocations] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [isCalculating, setIsCalculating] = useState(false);

  // Auto-fetch gaps
  useEffect(() => {
    fetch(`http://localhost:8000/resourcing-gap?city=${selectedCity}`)
      .then(r => r.json())
      .then(data => setGaps(data.gaps || []), { headers: { 'Authorization': `Bearer ${token}` } });
  }, [selectedCity]);

  const handleAllocate = () => {
    setIsCalculating(true);
    fetch(`http://localhost:8000/allocate-patrols`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`,  'Content-Type': 'application/json' },
      body: JSON.stringify({ city: selectedCity, total_units: parseInt(totalUnits) || 0 })
    })
      .then(r => r.json())
      .then(data => {
        setAllocations(data.allocations || []);
        setIsCalculating(false);
      })
      .catch(() => setIsCalculating(false));
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
        Resource Optimization
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PATROL PLANNER */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-slate-200">
            <span className="w-8 h-8 rounded bg-indigo-500/20 flex items-center justify-center text-indigo-400"><Users size={18} /></span>
            Patrol Allocation Optimizer
          </h3>

          <div className="flex gap-4 mb-6 items-end">
            <div className="flex-1">
              <label className="block text-sm text-slate-400 mb-2">Total Patrol Units Available</label>
              <input
                type="number"
                value={totalUnits}
                onChange={e => setTotalUnits(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={handleAllocate}
              disabled={isCalculating}
              className="px-6 py-2 rounded-lg font-semibold transition-all bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30"
            >
              {isCalculating ? 'Calculating...' : 'Calculate Optimal Allocation'}
            </button>
          </div>

          {allocations.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Allocation Results</h4>
              {allocations.map(a => (
                <div key={a.zone_id} className="flex justify-between items-center p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                  <div>
                    <span className="font-medium text-slate-200 block">{a.zone_id}</span>
                    <span className="text-xs text-slate-500">Risk Score: {a.risk_score}</span>
                  </div>
                  <div className="bg-indigo-500/20 text-indigo-400 font-bold px-4 py-1.5 rounded text-lg">
                    {a.units_assigned} Units
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RESOURCING GAPS */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-slate-200">
            <span className="w-8 h-8 rounded bg-red-500/20 flex items-center justify-center text-red-400"><AlertTriangle size={18} /></span>
            Resourcing Gap Analysis
          </h3>

          <div className="space-y-4">
            <div className="grid grid-cols-4 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 border-b border-slate-700 pb-2">
              <div className="col-span-1">Zone</div>
              <div className="text-center">Risk</div>
              <div className="text-center">Current Patrols</div>
              <div className="text-right">Gap Score</div>
            </div>

            {gaps.map(g => (
              <div key={g.zone_id} className="grid grid-cols-4 items-center text-sm">
                <div className="col-span-1 font-medium text-slate-300">{g.zone_id}</div>
                <div className="text-center text-orange-400">{g.risk_score}</div>
                <div className="text-center text-slate-400">{g.avg_police_deployed}</div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded ${g.gap_score > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                    {g.gap_score > 0 ? '+' : ''}{g.gap_score}
                  </span>
                </div>
              </div>
            ))}
            {gaps.length === 0 && <div className="text-slate-500 text-center py-8">Loading gap data...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
