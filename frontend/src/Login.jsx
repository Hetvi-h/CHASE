import React from 'react';
import { supabase } from './supabaseClient';
import { ShieldAlert } from 'lucide-react';

export default function Login() {
  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin
      }
    });
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 items-center justify-center font-sans">
      <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700 shadow-2xl max-w-md w-full text-center">
        <ShieldAlert size={48} className="mx-auto text-blue-500 mb-6" />
        <h1 className="text-3xl font-display font-extrabold text-white mb-2">CHASE</h1>
        <p className="text-slate-400 mb-8 font-medium">Crime Hotspot Analytics System</p>
        
        <button 
          onClick={handleLogin}
          className="w-full bg-white text-slate-900 hover:bg-slate-100 font-semibold py-3 px-4 rounded-xl transition-all shadow-lg flex items-center justify-center gap-3"
        >
          <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-5 h-5" />
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
