import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, Legend } from 'recharts';
import { AlertTriangle, ShieldAlert, TrendingUp, Layers } from 'lucide-react';

export default function Visualizations({ zoneStats, timeHeatmap, zoneScores, selectedZone, setSelectedZone, recommendations, generateAnalysis, isGenerating, monthlyTrend, crimeTypesByZone }) {
  // Sort zoneStats by count
  const sortedStats = [...(zoneStats || [])].sort((a, b) => b.count - a.count);
  
  // Prepare Heatmap data structure (hours on Y, days on X)
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const maxHeatmapVal = Math.max(...(timeHeatmap || []).map(d => d.count), 1);
  
  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WHERE */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-blue-500/20 flex items-center justify-center text-blue-400">📍</span>
            Geographic Hotspots
          </h3>
          <div style={{ height: `${Math.max(240, sortedStats.length * 44)}px` }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sortedStats} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="zone_id" type="category" stroke="#94a3b8" tick={{fontSize: 10}} width={80} />
                <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155'}} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {sortedStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={`hsl(217, 90%, ${Math.max(40, 70 - index*3)}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* WHEN */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl overflow-hidden">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center text-emerald-400">🕒</span>
            Incident Timing Patterns
          </h3>
          <div className="flex gap-2 text-xs text-slate-400 mb-2">
            <div className="w-8"></div>
            {days.map(d => <div key={d} className="flex-1 text-center font-medium">{d}</div>)}
          </div>
          <div className="h-60 overflow-y-auto pr-2 custom-scrollbar">
            {Array.from({length: 24}).map((_, h) => (
              <div key={h} className="flex gap-2 mb-1">
                <div className="w-8 text-xs text-slate-500 flex items-center justify-end pr-2">{h}:00</div>
                {days.map((_, d) => {
                  const cell = (timeHeatmap || []).find(x => x.hour === h && x.day === d);
                  const count = cell ? cell.count : 0;
                  const intensity = count / maxHeatmapVal;
                  return (
                    <div 
                      key={`${h}-${d}`} 
                      className="flex-1 h-6 rounded-sm relative group"
                      style={{ backgroundColor: count === 0 ? 'rgba(30, 41, 59, 0.5)' : `hsl(${120 - (intensity * 120)}, 90%, ${Math.max(40, 50 - (intensity * 10))}%)` }}
                    >
                      <div className="absolute inset-0 bg-white/0 hover:bg-white/20 transition-colors rounded-sm cursor-crosshair z-10" title={`${days[d]} ${h}:00 - ${count} incidents`}></div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MONTHLY TREND */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-purple-500/20 flex items-center justify-center text-purple-400"><TrendingUp size={18}/></span>
            Monthly Crime Trend (2020-2024)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyTrend || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="month" stroke="#94a3b8" tick={{fontSize: 10}} minTickGap={30} />
                <YAxis stroke="#94a3b8" tick={{fontSize: 10}} />
                <Tooltip 
                  cursor={{stroke: '#475569', strokeWidth: 1, strokeDasharray: '4 4'}} 
                  contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem'}}
                  itemStyle={{color: '#c084fc', fontWeight: 'bold'}}
                />
                <Line type="monotone" dataKey="count" name="Incidents" stroke="#c084fc" strokeWidth={3} dot={false} activeDot={{r: 6, fill: '#c084fc', stroke: '#fff', strokeWidth: 2}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CRIME TYPES BY ZONE */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-pink-500/20 flex items-center justify-center text-pink-400"><Layers size={18}/></span>
            Crime Composition by Area
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={crimeTypesByZone || []} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" tick={{fontSize: 10}} />
                <YAxis dataKey="zone_id" type="category" stroke="#94a3b8" tick={{fontSize: 10}} width={80} tickFormatter={(v) => String(v).split('_').slice(-2).join(' ')} />
                <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155'}} />
                <Legend iconType="circle" wrapperStyle={{fontSize: '11px', paddingTop: '10px'}} />
                <Bar dataKey="Violent Crime" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Other Crime" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Fire Accident" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
                <Bar dataKey="Traffic Fatality" stackId="a" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* UNSAFE PLACES */}
      <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-xl">
         <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <span className="w-8 h-8 rounded bg-orange-500/20 flex items-center justify-center text-orange-400">⚠️</span>
            Zone Safety Analysis
          </h3>
          
          <div className="flex gap-4 mb-6">
             <select 
               value={selectedZone || ""} 
               onChange={e => setSelectedZone(e.target.value)}
               className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none w-full md:w-1/3"
             >
               <option value="" disabled>Select a Zone to Analyze</option>
               {[...(zoneScores || [])].sort((a,b) => b.score - a.score).map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_id} (Score: {z.score})</option>)}
             </select>
             
             <button
               onClick={generateAnalysis}
               disabled={!selectedZone || isGenerating}
               className={`px-6 py-2 rounded-lg font-semibold transition-all ${!selectedZone ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : isGenerating ? 'bg-blue-600/50 text-blue-200 cursor-wait' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/30'}`}
             >
               {isGenerating ? 'Generating...' : 'Run Action Plan'}
             </button>

             {selectedZone && (
                 <a 
                   href={`http://localhost:8000/reports/zone/${selectedZone}/pdf`}
                   download
                   className="px-6 py-2 rounded-lg font-semibold transition-all bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 flex items-center justify-center"
                 >
                   Export Zone PDF
                 </a>
             )}
             
             {zoneScores && zoneScores.length > 0 && (
                 <a 
                   href={`http://localhost:8000/reports/city/${zoneScores[0].zone_id.split('_')[0]}/pdf`}
                   download
                   className="px-6 py-2 rounded-lg font-semibold transition-all bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 flex items-center justify-center"
                 >
                   Export City PDF
                 </a>
             )}
          </div>

          {/* ACTION PLAN CARD */}
          {selectedZone && recommendations && recommendations.shap_summary && (
            <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-700 mt-6 grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2">
                <h4 className="text-xl font-bold text-blue-400 mb-3 flex items-center gap-2">
                  <ShieldAlert size={20} /> Zone Action Plan
                </h4>
                <div className="bg-slate-800/80 p-5 rounded-lg border-l-4 border-blue-500">
                  <p className="text-lg text-slate-200 leading-relaxed font-medium">
                    {recommendations.sentence}
                  </p>
                </div>
                <div className="mt-6 flex flex-wrap gap-4 text-sm text-slate-400">
                  <div className="bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
                    <strong className="text-emerald-400">#1 Survey Concern:</strong> {recommendations.top_concern}
                  </div>
                  <div className="bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
                    <strong className="text-blue-400">Top Request:</strong> {recommendations.top_improvement}
                  </div>
                </div>
              </div>
              
              <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700">
                 <h5 className="font-semibold text-slate-300 mb-4 pb-2 border-b border-slate-700 text-sm">SHAP Feature Impacts (Global RF Model)</h5>
                 <div className="space-y-3">
                   {Object.entries(recommendations.shap_summary.impacts)
                      .sort(([,a], [,b]) => b - a)
                      .slice(0, 5)
                      .map(([feature, impact]) => (
                     <div key={feature}>
                       <div className="flex justify-between text-xs mb-1">
                         <span className="text-slate-400 font-mono">{feature}</span>
                         <span className="text-slate-300 font-mono">{(impact*100).toFixed(1)}%</span>
                       </div>
                       <div className="w-full bg-slate-900 rounded-full h-1.5">
                         <div className={`h-1.5 rounded-full ${feature === recommendations.shap_summary.top_feature ? 'bg-red-500' : 'bg-slate-600'}`} style={{width: `${Math.min(100, impact*300)}%`}}></div>
                       </div>
                     </div>
                   ))}
                 </div>
              </div>
            </div>
          )}
          {selectedZone && recommendations && !recommendations.shap_summary && (
              <div className="mt-6 text-slate-500">Model generating SHAP explainer for this zone...</div>
          )}
      </div>
    </div>
  );
}
