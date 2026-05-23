import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MapPin, Search, ExternalLink, Calendar, RefreshCw } from 'lucide-react';

interface Job {
  title: string;
  company: string;
  url: string;
  location: string;
  logo: string;
  date: string;
  type: string;
}

const JobFinder: React.FC = () => {
  const { token, apiUrl } = useAuth();
  
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [track, setTrack] = useState('Software Development');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchJobs();
  }, [track]);

  const fetchJobs = async () => {
    if (!token) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${apiUrl}/api/jobs?role=${encodeURIComponent(track)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) {
        throw new Error(`Failed to fetch jobs: ${res.statusText}`);
      }
      
      const data = await res.json();
      if (data.success) {
        setJobs(data.jobs);
      } else {
        throw new Error(data.message || 'Failed to load jobs');
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Failed to load jobs. Check your connection.";
      setError(errorMsg);
      console.error("Failed to load jobs:", e);
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job => 
    job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Title */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="glow-text" style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '4px' }}>
            Active Remote Directory
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Real-time scraping results of active remote jobs and internship placements.
          </p>
        </div>
        
        <button 
          onClick={fetchJobs} 
          disabled={loading}
          className="btn-secondary" 
          style={{
            padding: '8px 14px',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Toolbar */}
      <div className="glass-card" style={{
        padding: '16px 24px',
        marginBottom: '30px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        
        {/* Track Selector Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          {['Software Development', 'Data Science', 'AI/ML'].map(role => (
            <button
              key={role}
              onClick={() => setTrack(role)}
              className={track === role ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '8px 16px', fontSize: '0.85rem', borderRadius: '8px' }}
            >
              {role}
            </button>
          ))}
        </div>

        {/* Search input field */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-light)',
          borderRadius: '8px',
          padding: '4px 12px',
          width: '320px',
          maxWidth: '100%'
        }}>
          <Search size={16} color="var(--text-muted)" style={{ marginRight: '8px' }} />
          <input
            type="text"
            placeholder="Search keywords, companies..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'white',
              outline: 'none',
              padding: '8px 0',
              fontSize: '0.85rem',
              width: '100%',
              fontFamily: 'var(--font-body)'
            }}
          />
        </div>

      </div>

      {error && (
        <div style={{
          backgroundColor: 'var(--error-glow)',
          border: '1px solid var(--error)',
          color: 'var(--text-primary)',
          padding: '14px',
          borderRadius: '8px',
          fontSize: '0.9rem',
          marginBottom: '20px'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Grid of job listings */}
      {loading ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          🔍 Scraping live listings from WeWorkRemotely...
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No job matches found matching your filters. Try adjusting search queries.
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '24px'
        }}>
          {filteredJobs.map((job, idx) => (
            <div key={idx} className="glass-card fade-in" style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '200px'
            }}>
              <div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
                  {job.logo ? (
                    <img 
                      src={job.logo} 
                      alt={job.company} 
                      style={{ width: '42px', height: '42px', borderRadius: '8px', border: '1px solid var(--border-light)' }} 
                    />
                  ) : (
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.05)',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      border: '1px solid var(--border-light)',
                      fontWeight: 'bold',
                      color: 'var(--text-secondary)',
                      fontSize: '1rem'
                    }}>
                      {job.company.substring(0, 1)}
                    </div>
                  )}
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'white' }}>{job.company}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} />
                      {job.location}
                    </span>
                  </div>
                </div>
                
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'white', lineHeight: '1.4', marginBottom: '10px' }}>
                  {job.title}
                </h3>
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderTop: '1px solid var(--border-light)',
                paddingTop: '14px',
                marginTop: '20px'
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 500 }}>
                  <Calendar size={12} />
                  {job.date}
                </span>

                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary"
                  style={{
                    fontSize: '0.8rem',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    boxShadow: 'none'
                  }}
                >
                  <span>Apply</span>
                  <ExternalLink size={12} />
                </a>
              </div>

            </div>
          ))}
        </div>
      )}

      <style>{`
        .animate-spin {
          animation: spin 1.5s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

    </div>
  );
};

export default JobFinder;
