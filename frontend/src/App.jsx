import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Polygon as LeafletPolygon, Tooltip as MapTooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip as MapTooltipRecharts, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { Clock, ShieldAlert, Map as MapIcon, Info, Activity, ChevronRight, AlertTriangle, Database } from 'lucide-react';
import Visualizations from './Visualizations';
import CaseBrowser from './CaseBrowser';
import Chatbot from './Chatbot';
import PatrolPlanner from './PatrolPlanner';
import { Users, FileText, User as UserIcon } from 'lucide-react';
import Login from './Login';
import Profile from './Profile';
import AuditLogs from './AuditLogs';
import { supabase } from './supabaseClient';

const API_BASE = "http://localhost:8000";

// Component to dynamically change map view
function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

export default function App() {
  const [session, setSession] = useState(null);
  const [token, setToken] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    // Check for existing session (handles redirect back from Google OAuth)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setToken(session?.access_token || null);
      setAuthLoading(false);
    }).catch(err => {
      console.error("Auth session error:", err);
      setAuthLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);
      setToken(session?.access_token || null);
      setAuthLoading(false);
      if (session && _event === 'SIGNED_IN') {
        // Upsert profile on first sign-in
        await fetch(`${API_BASE}/auth/sync-profile`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        });
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const [activeTab, setActiveTab] = useState('map');
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState("All Cities");
  
  const [hotspots, setHotspots] = useState([]);
  const [zoneScores, setZoneScores] = useState([]);
  const [hour, setHour] = useState(12); // For time slider
  
  const [selectedZone, setSelectedZone] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [riskPrediction, setRiskPrediction] = useState(null);
  const [zoneStats, setZoneStats] = useState([]);
  const [timeHeatmap, setTimeHeatmap] = useState([]);
  const [zoneCircles, setZoneCircles] = useState([]);
  const [monthlyTrend, setMonthlyTrend] = useState([]);
  const [crimeTypesByZone, setCrimeTypesByZone] = useState([]);

  useEffect(() => {
    // Fetch all available cities
    fetch(`${API_BASE}/cities`, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        if(data.cities) setCities(data.cities);
      }).catch(err => console.error("Cities fetch error:", err));
  }, [token]);

  useEffect(() => {
    // Fetch hotspots for selected city and hour
    if (selectedCity && token) {
      const opts = { headers: { 'Authorization': `Bearer ${token}` } };
      fetch(`${API_BASE}/hotspots?city=${selectedCity}&hour=${hour}`, opts)
        .then(r => r.json())
        .then(data => setHotspots(data.hotspots || []));
        
      fetch(`${API_BASE}/zone-scores?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setZoneScores(data.scores || []));
        
      fetch(`${API_BASE}/stats/zones?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setZoneStats(data.zones || []));
        
      fetch(`${API_BASE}/stats/time-heatmap?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setTimeHeatmap(data.heatmap || []));

      // Fetch zone circles from zone_reference
      fetch(`${API_BASE}/zones?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setZoneCircles(data.zones || []));
        
      fetch(`${API_BASE}/stats/monthly-trend?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setMonthlyTrend(data.trend || []));
        
      fetch(`${API_BASE}/stats/crime-types-by-zone?city=${selectedCity}`, opts)
        .then(r => r.json())
        .then(data => setCrimeTypesByZone(data.data || []));
    }
  }, [selectedCity, hour, token]);

  const [isGenerating, setIsGenerating] = useState(false);

  const generateAnalysis = () => {
    if (selectedZone) {
      setIsGenerating(true);
      Promise.all([
        fetch(`${API_BASE}/recommendations/${selectedZone}`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
        fetch(`${API_BASE}/predict-risk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ zone_id: selectedZone, hour: hour, day_of_week: 1, month: 6 })
        }).then(r => r.json())
      ]).then(([recData, riskData]) => {
        setRecommendations(recData || null);
        setRiskPrediction(riskData);
        setIsGenerating(false);
      }).catch(() => setIsGenerating(false));
    }
  };

  // Wait for Supabase to resolve session before deciding what to render.
  // Without this, the app briefly shows Login on every OAuth redirect-back.
  if (authLoading) return (
    <div className="flex h-screen bg-slate-900 items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm font-medium">Authenticating...</p>
      </div>
    </div>
  );

  if (!session) return <Login />;

  const mapCenter = hotspots.length > 0 ? [hotspots[0].lat, hotspots[0].lng] : [28.6139, 77.2090];

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
      
      {/* Sidebar Navigation */}
      <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        <div className="p-6">
          <h1 className="text-3xl font-display font-extrabold text-blue-500 tracking-tight">
            CHASE
          </h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">Analytics</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <NavItem icon={<MapIcon size={18}/>} label="Live Map" active={activeTab==='map'} onClick={()=>setActiveTab('map')} />
          <NavItem icon={<Activity size={18}/>} label="Zone Rankings" active={activeTab==='rankings'} onClick={()=>setActiveTab('rankings')} />
          <NavItem icon={<ShieldAlert size={18}/>} label="Risk Predictor" active={activeTab==='predictor'} onClick={()=>setActiveTab('predictor')} />
          <NavItem icon={<Users size={18}/>} label="Patrol Planner" active={activeTab==='patrol'} onClick={()=>setActiveTab('patrol')} />
          <NavItem icon={<Database size={18}/>} label="Case Browser" active={activeTab==='cases'} onClick={()=>setActiveTab('cases')} />
        </nav>
        <div className="p-4 space-y-2 border-t border-slate-700">
          <NavItem icon={<FileText size={18}/>} label="Audit Logs" active={activeTab==='audit'} onClick={()=>setActiveTab('audit')} />
          <NavItem icon={<UserIcon size={18}/>} label="Profile" active={activeTab==='profile'} onClick={()=>setActiveTab('profile')} />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full relative">
        
        {/* Top Header Controls */}
        <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-6 z-10">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-slate-400">City View:</label>
            <select 
              value={selectedCity} 
              onChange={e => setSelectedCity(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="All Cities">All Cities</option>
              <option value="Delhi">Delhi</option>
              {cities.filter(c => c !== 'Delhi' && c !== 'All Cities').map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          
          {/* Time Slider */}
          <div className="flex items-center gap-4 w-96">
            <Clock size={16} className="text-blue-400"/>
            <input 
              type="range" min="0" max="23" value={hour} 
              onChange={e => setHour(parseInt(e.target.value))}
              className="w-full accent-blue-500"
            />
            <span className="text-sm font-mono bg-slate-800 px-2 py-1 rounded border border-slate-700 w-16 text-center">
              {hour.toString().padStart(2, '0')}:00
            </span>
          </div>
        </header>

        {/* Dynamic Content Views */}
        <div className="flex-1 overflow-auto p-6 relative">
          
          {activeTab === 'map' && (
            <div className="absolute inset-0 rounded-tl-2xl overflow-hidden">
                <MapContainer center={mapCenter} zoom={11} style={{ height: '100%', width: '100%' }}>
                  <ChangeView center={mapCenter} zoom={11} />
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  
                  {/* Zone Polygons/Circles from zone_reference */}
                  {zoneCircles.map((z, i) => {
                    const ZONE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#ef4444'];
                    const match = z.zone_id.match(/_(\d+)$/);
                    const zoneNum = match ? parseInt(match[1]) - 1 : i;
                    const zoneColor = ZONE_COLORS[zoneNum % ZONE_COLORS.length];
                    
                    if (z.polygon && z.polygon.length > 0) {
                      return (
                        <LeafletPolygon
                          key={`zone-${z.zone_id}`}
                          positions={z.polygon}
                          pathOptions={{ color: zoneColor, fillColor: zoneColor, fillOpacity: 0.15, weight: 2, dashArray: '6 4' }}
                        >
                          <MapTooltip direction="center" opacity={0.9} permanent className="bg-transparent border-none text-white font-bold text-base drop-shadow-md shadow-none">
                            {z.zone_id.replace(/_/g, ' ')}
                          </MapTooltip>
                        </LeafletPolygon>
                      );
                    }
                    
                    const radiusMeters = (z.radius_km || 2.5) * 1000;
                    return (
                      <Circle
                        key={`zone-${z.zone_id}`}
                        center={[z.lat, z.lng]}
                        radius={radiusMeters}
                        pathOptions={{ color: zoneColor, fillColor: zoneColor, fillOpacity: 0.15, weight: 2, dashArray: '6 4' }}
                      >
                        <MapTooltip direction="center" opacity={0.9} permanent className="bg-transparent border-none text-white font-bold text-base drop-shadow-md shadow-none">
                          {z.zone_id.replace(/_/g, ' ')}
                        </MapTooltip>
                      </Circle>
                    );
                  })}

                  {/* Incident Dots */}
                  {hotspots.map((pt, i) => (
                    <CircleMarker 
                      key={i} center={[pt.lat, pt.lng]} radius={3}
                      pathOptions={{ color: '#ef4444', fillOpacity: 0.6, weight: 1 }}
                    >
                      <MapTooltip direction="top" opacity={1} className="bg-slate-800 text-slate-100 border-none rounded shadow-xl">
                        <div className="p-1">
                          <p className="font-bold text-sm text-blue-400">Incident #{pt.id}</p>
                          <p className="text-xs font-bold uppercase mt-1 tracking-wider text-slate-300">{pt.zone_id || 'Unknown Zone'}</p>
                          <p className="font-medium mt-1">{pt.type}</p>
                          <p className="text-xs text-slate-300 mt-1">Time: {pt.time}</p>
                        </div>
                      </MapTooltip>
                    </CircleMarker>
                  ))}
               </MapContainer>
               
               {/* Map Legend Removed */}
            </div>
          )}

          {activeTab === 'rankings' && (
            <div className="max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-2xl font-bold mb-6">Zone Safety Rankings — {selectedCity}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6 shadow-lg">
                  <h3 className="text-lg font-semibold mb-4 text-slate-300">Composite Score Distribution</h3>
                  <div style={{ height: `${Math.max(280, (zoneScores?.length || 3) * 48)}px` }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={zoneScores} margin={{ top: 5, right: 10, left: 0, bottom: 30 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis 
                          dataKey="zone_id" 
                          stroke="#94a3b8" 
                          tick={{ fontSize: 11 }}
                          interval={0}
                          tickFormatter={(v) => v.split('_').slice(-2).join(' ')}
                          angle={-35}
                          textAnchor="end"
                        />
                        <YAxis stroke="#94a3b8" domain={[0, 100]} />
                        <MapTooltipRecharts 
                          contentStyle={{backgroundColor: '#1e293b', borderColor: '#334155'}}
                          formatter={(v, n, p) => [v, 'score']}
                          labelFormatter={(l) => l}
                        />
                        <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {[...zoneScores].sort((a,b) => b.score - a.score).map((z, idx) => (
                    <div key={z.zone_id} 
                         onClick={() => { setSelectedZone(z.zone_id); setActiveTab('predictor'); }}
                         className="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-blue-500 transition-all cursor-pointer flex items-center justify-between group">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg
                          ${idx === 0 ? 'bg-emerald-500/20 text-emerald-400' : 
                            idx === zoneScores.length-1 ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                          #{idx + 1}
                        </div>
                        <div>
                          <h4 className="font-semibold text-slate-200">{z.zone_id}</h4>
                          <p className="text-xs text-slate-400">Score: {z.score} / 100</p>
                        </div>
                      </div>
                      <ChevronRight size={20} className="text-slate-500 group-hover:text-blue-400 transition-colors" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'predictor' && (
            <Visualizations 
              zoneStats={zoneStats} 
              timeHeatmap={timeHeatmap} 
              zoneScores={zoneScores} 
              selectedZone={selectedZone} 
              setSelectedZone={setSelectedZone} 
              recommendations={recommendations} 
              generateAnalysis={generateAnalysis}
              isGenerating={isGenerating}
              monthlyTrend={monthlyTrend}
              crimeTypesByZone={crimeTypesByZone}
              token={token}
            />
          )}

          {activeTab === 'cases' && (
            <CaseBrowser 
              selectedCity={selectedCity}
              zoneScores={zoneScores}
              token={token}
            />
          )}

          {activeTab === 'patrol' && (
            <PatrolPlanner 
              selectedCity={selectedCity}
              zoneScores={zoneScores}
              token={token}
            />
          )}

          {activeTab === 'profile' && <Profile />}
          {activeTab === 'audit' && <AuditLogs token={token} />}

        </div>
        
        {/* Chatbot Overlay */}
        <Chatbot selectedCity={selectedCity} token={token} />
      </div>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
        ${active 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' 
          : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'}`}
    >
      {icon}
      <span className="font-medium text-sm">{label}</span>
    </button>
  );
}
