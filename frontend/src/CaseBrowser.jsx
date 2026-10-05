import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Plus, X } from 'lucide-react';

export default function CaseBrowser({ token, selectedCity, zoneScores }) {
  const [cases, setCases] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [domains, setDomains] = useState([]);
  
  // Filters
  const [zoneFilter, setZoneFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  
  const [expandedId, setExpandedId] = useState(null);
  
  // Add Case Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCase, setNewCase] = useState({
    date_of_occurrence: '',
    time_of_occurrence: '',
    zone_id: '',
    crime_domain: '',
    crime_description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const limit = 20;

  // Fetch distinct crime domains once
  useEffect(() => {
    fetch('http://localhost:8000/crime-domains')
      .then(r => r.json())
      .then(data => setDomains(data.domains || []), { headers: { 'Authorization': `Bearer ${token}` } });
  }, []);

  // Reset page when city changes
  useEffect(() => {
    setPage(0);
    setZoneFilter('');
    setTypeFilter('');
  }, [selectedCity]);

  const loadCases = () => {
    let url = `http://localhost:8000/cases?city=${selectedCity}&limit=${limit}&offset=${page * limit}`;
    if (zoneFilter) url += `&zone_id=${zoneFilter}`;
    if (typeFilter) url += `&crime_domain=${typeFilter}`;
    
    fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        setCases(data.cases || []);
        setTotal(data.total || 0);
      });
  };

  useEffect(() => {
    loadCases();
  }, [selectedCity, page, zoneFilter, typeFilter]);

  const handleAddCase = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        ...newCase,
        city: selectedCity,
        time_of_occurrence: newCase.time_of_occurrence.length === 5 ? newCase.time_of_occurrence + ':00' : newCase.time_of_occurrence
      };
      
      const res = await fetch('http://localhost:8000/cases', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setShowAddModal(false);
        setNewCase({ date_of_occurrence: '', time_of_occurrence: '', zone_id: '', crime_domain: '', crime_description: '' });
        loadCases(); // reload the data
      } else {
        alert('Failed to add case');
      }
    } catch (err) {
      console.error(err);
      alert('Error adding case');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          Case Browser Database
        </h2>
        <button 
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
        >
          <Plus size={18} /> Add New Case
        </button>
      </div>
      
      {/* Controls */}
      <div className="flex flex-wrap gap-4 bg-slate-800 p-4 rounded-xl border border-slate-700 items-center justify-between shadow-xl">
        <div className="flex gap-4 w-full md:w-auto">
          <select 
            value={zoneFilter} 
            onChange={e => {setZoneFilter(e.target.value); setPage(0);}}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 outline-none text-sm w-full md:w-48"
          >
            <option value="">All Zones</option>
            {(zoneScores || []).map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_id}</option>)}
          </select>
          
          <select 
            value={typeFilter} 
            onChange={e => {setTypeFilter(e.target.value); setPage(0);}}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 outline-none text-sm w-full md:w-48"
          >
            <option value="">All Crime Types</option>
            {domains.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        
        <div className="text-sm text-slate-400 font-medium">
          Showing {total > 0 ? page * limit + 1 : 0} - {Math.min((page + 1) * limit, total)} of {total} cases
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/50 border-b border-slate-700 text-slate-300">
                <th className="p-4 font-semibold text-sm">Case ID</th>
                <th className="p-4 font-semibold text-sm">Date & Time</th>
                <th className="p-4 font-semibold text-sm">Zone</th>
                <th className="p-4 font-semibold text-sm">Domain</th>
                <th className="p-4 font-semibold text-sm w-10"></th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <React.Fragment key={c.id}>
                  <tr 
                    className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
                    onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}
                  >
                    <td className="p-4 font-mono text-blue-400">#{c.id}</td>
                    <td className="p-4">{c.date} <span className="text-slate-500">{c.time}</span></td>
                    <td className="p-4">{c.zone_id}</td>
                    <td className="p-4 font-medium">{c.type}</td>
                    <td className="p-4 text-slate-400">
                      {expandedId === c.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </td>
                  </tr>
                  {expandedId === c.id && (
                    <tr className="bg-slate-900/40 border-b border-slate-700">
                      <td colSpan="5" className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          <div className="md:col-span-2">
                            <h4 className="text-xs uppercase text-slate-500 font-semibold mb-2 tracking-wider">Incident Report Description</h4>
                            <p className="text-sm text-slate-300 bg-slate-900/80 p-4 rounded-xl border border-slate-700/50 leading-relaxed min-h-[80px]">
                              {c.description || 'No detailed description available.'}
                            </p>
                          </div>
                          <div className="space-y-4">
                            <div>
                              <h4 className="text-xs uppercase text-slate-500 font-semibold mb-2 tracking-wider">Report Details</h4>
                              <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-700/50 text-sm space-y-2">
                                <div className="flex justify-between"><span className="text-slate-500">City:</span> <span className="font-medium">{selectedCity}</span></div>
                                <div className="flex justify-between"><span className="text-slate-500">Zone ID:</span> <span className="font-medium text-blue-400">{c.zone_id}</span></div>
                                <div className="flex justify-between"><span className="text-slate-500">Category:</span> <span className="font-medium">{c.type}</span></div>
                                <div className="flex justify-between"><span className="text-slate-500">Weapon Info:</span> <span className="font-medium text-slate-400 italic">See Description</span></div>
                              </div>
                            </div>
                            <div>
                               <h4 className="text-xs uppercase text-slate-500 font-semibold mb-2 tracking-wider">Data Provenance</h4>
                               <div className="text-sm font-medium">
                                 {c.synthetic ? 
                                   <span className="text-blue-400 bg-blue-500/10 px-3 py-2 rounded-lg border border-blue-500/20 block text-center">NCRB-Rescaled (Synthetic Position)</span> : 
                                   <span className="text-emerald-400 bg-emerald-500/10 px-3 py-2 rounded-lg border border-emerald-500/20 block text-center">Field / Manual Record</span>
                                 }
                               </div>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {cases.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-500">No cases found matching these filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="p-4 flex items-center justify-between bg-slate-900/50">
          <button 
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
            className="px-4 py-2 flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:hover:bg-slate-800 rounded-lg transition-colors text-sm font-medium border border-slate-700"
          >
            <ChevronLeft size={16} /> Previous
          </button>
          
          <button 
            disabled={(page + 1) * limit >= total}
            onClick={() => setPage(page + 1)}
            className="px-4 py-2 flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:hover:bg-slate-800 rounded-lg transition-colors text-sm font-medium border border-slate-700"
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center p-6 border-b border-slate-700">
              <h3 className="text-xl font-bold">Add New Case Record</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white transition-colors">
                <X size={24} />
              </button>
            </div>
            
            <form onSubmit={handleAddCase} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm text-slate-400 font-medium">Date <span className="text-red-400">*</span></label>
                  <input type="date" required 
                    value={newCase.date_of_occurrence}
                    onChange={e => setNewCase({...newCase, date_of_occurrence: e.target.value})}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm text-slate-400 font-medium">Time <span className="text-red-400">*</span></label>
                  <input type="time" required 
                    value={newCase.time_of_occurrence}
                    onChange={e => setNewCase({...newCase, time_of_occurrence: e.target.value})}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>
              
              <div className="space-y-1">
                <label className="text-sm text-slate-400 font-medium">Zone <span className="text-red-400">*</span></label>
                <select required 
                  value={newCase.zone_id}
                  onChange={e => setNewCase({...newCase, zone_id: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="">Select Zone in {selectedCity}</option>
                  {(zoneScores || []).map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_id}</option>)}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-slate-400 font-medium">Crime Domain <span className="text-red-400">*</span></label>
                <select required 
                  value={newCase.crime_domain}
                  onChange={e => setNewCase({...newCase, crime_domain: e.target.value})}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="">Select Crime Type</option>
                  {domains.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-slate-400 font-medium">Description (Optional)</label>
                <textarea 
                  rows={3}
                  value={newCase.crime_description}
                  onChange={e => setNewCase({...newCase, crime_description: e.target.value})}
                  placeholder="Enter detailed incident description, suspects, etc."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 outline-none focus:border-blue-500 transition-colors resize-none"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 rounded-lg font-medium hover:bg-slate-700 transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
                  {isSubmitting ? 'Saving...' : 'Save Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
