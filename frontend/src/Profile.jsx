import React, { useEffect, useState } from 'react';
import { supabase } from './supabaseClient';

export default function Profile() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        supabase.from('profiles').select('*').eq('id', user.id).single().then(({ data, error }) => {
          if (error) {
            console.error("Profile fetch error:", error);
            // Fallback to minimal profile if not found in DB yet
            setProfile({ full_name: user.user_metadata?.full_name || 'User', email: user.email, role: 'viewer', created_at: new Date().toISOString() });
          } else {
            setProfile(data);
          }
        });
      }
    });
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  if (!profile) return <div className="p-8 text-slate-400">Loading profile...</div>;

  return (
    <div className="p-8 animate-in fade-in duration-500">
      <h2 className="text-2xl font-display font-bold text-white mb-6">User Profile</h2>
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl max-w-2xl">
        <div className="space-y-4 mb-8">
          <div>
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Name</label>
            <p className="text-lg text-slate-200">{profile.full_name}</p>
          </div>
          <div>
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Email</label>
            <p className="text-lg text-slate-200">{profile.email}</p>
          </div>
          <div>
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Role</label>
            <p className="text-lg text-blue-400 font-medium capitalize">{profile.role}</p>
          </div>
          <div>
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Joined</label>
            <p className="text-md text-slate-300">{new Date(profile.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        <button 
          onClick={handleSignOut}
          className="bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors px-6 py-2 rounded-lg font-medium"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}
