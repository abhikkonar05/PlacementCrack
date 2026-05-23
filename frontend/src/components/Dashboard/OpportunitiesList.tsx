import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Briefcase, Search, Calendar, ExternalLink, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Opportunity {
  id: string;
  title: string;
  company: string;
  opportunity_type: string;
  eligibility: string;
  deadline: string;
  apply_link: string;
  location: string;
  logo: string;
}

const OpportunitiesList: React.FC = () => {
  const { token, apiUrl } = useAuth();
  const navigate = useNavigate();

  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const opportunityTypes = [
    { label: 'All Feeds', value: '' },
    { label: 'Hackathons', value: 'Hackathon' },
    { label: 'Internships', value: 'Internship' },
    { label: 'Coding Contests', value: 'Coding Contest' },
    { label: 'Open-Source', value: 'Open-Source Program' },
    { label: 'Remote Jobs', value: 'Remote Job' }
  ];

  useEffect(() => {
    fetchOpportunities();
  }, [page, typeFilter]);

  const fetchOpportunities = async () => {
    if (!token) return;
    setLoading(true);
    try {
      let url = `${apiUrl}/api/opportunities?page=${page}&limit=6`;
      if (typeFilter) url += `&opportunity_type=${encodeURIComponent(typeFilter)}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setOpportunities(data.opportunities);
        setTotalPages(data.total_pages);
      }
    } catch (e) {
      console.error("Failed to load opportunities:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchOpportunities();
  };

  const formatDeadline = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Back Button */}
      <button 
        onClick={() => navigate('/')} 
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          padding: '12px 0',
          fontWeight: 600,
          fontSize: '0.9rem',
          transition: 'color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent-purple)'}
        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
      >
        <ArrowLeft size={16} />
        <span>Back to Dashboard</span>
      </button>

      {/* Header Banner */}
      <div className="glass-card-glow" style={{
        padding: '30px 40px',
        borderRadius: '16px',
        marginBottom: '40px',
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%)',
        border: '1px solid var(--border-glow)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
          <Briefcase size={32} color="var(--success)" />
          <h1 className="glow-text" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
            Curated Career Opportunities
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', margin: 0 }}>
          Real-world student opportunities updated dynamically. Apply directly to open-source programs, student hackathons, international coding contests, and verified engineering internships.
        </p>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '30px', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px' }}>
        {opportunityTypes.map(type => (
          <button
            key={type.value}
            onClick={() => { setTypeFilter(type.value); setPage(1); }}
            className={typeFilter === type.value ? 'btn-primary' : 'btn-secondary'}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              background: typeFilter === type.value ? 'linear-gradient(135deg, var(--success) 0%, #10b981 100%)' : undefined,
              boxShadow: typeFilter === type.value ? '0 4px 15px rgba(16, 185, 129, 0.15)' : undefined
            }}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '30px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px' }}>
          <div className="input-wrapper" style={{ flexGrow: 1 }}>
            <Search size={18} className="input-icon" />
            <input 
              type="text" 
              placeholder="Search by role title or company..." 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '44px' }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ padding: '0 24px', background: 'linear-gradient(135deg, var(--success) 0%, #10b981 100%)' }}>Search</button>
        </form>
      </div>

      {/* Opportunities list */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {[...Array(6)].map((_, idx) => (
            <div key={idx} className="glass-card" style={{ height: '220px', animation: 'pulse 1.5s infinite' }}></div>
          ))}
        </div>
      ) : opportunities.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No recommended opportunities matching these filters currently.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '25px' }}>
          {opportunities.map((opp) => (
            <div 
              key={opp.id} 
              className="glass-card" 
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: '1px solid var(--border-light)',
                padding: '24px',
                minHeight: '220px',
                transition: 'all 0.2s ease-in-out'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--success)';
                e.currentTarget.style.transform = 'translateY(-3px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-light)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div>
                {/* Header */}
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
                  {opp.logo ? (
                    <img 
                      src={opp.logo} 
                      alt={opp.company} 
                      style={{ width: '38px', height: '38px', borderRadius: '6px', border: '1px solid var(--border-light)' }} 
                    />
                  ) : (
                    <div style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.04)',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      border: '1px solid var(--border-light)',
                      fontWeight: 'bold',
                      color: 'var(--text-secondary)'
                    }}>
                      {opp.company.substring(0, 1)}
                    </div>
                  )}
                  <div>
                    <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)' }}>{opp.company}</h4>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{opp.location}</span>
                  </div>
                </div>

                {/* Title */}
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'white', lineHeight: '1.4', marginBottom: '10px' }}>
                  {opp.title}
                </h3>

                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  backgroundColor: 'rgba(16, 185, 129, 0.12)',
                  color: 'var(--success)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  textTransform: 'uppercase'
                }}>
                  {opp.opportunity_type}
                </span>

                {/* Eligibility */}
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: '12px', lineHeight: '1.4' }}>
                  <strong>Eligibility:</strong> {opp.eligibility}
                </p>
              </div>

              {/* Bottom bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px', borderTop: '1px solid var(--border-light)', paddingTop: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <Calendar size={14} />
                  <span>Deadline: {formatDeadline(opp.deadline)}</span>
                </div>

                <a 
                  href={opp.apply_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nav-link"
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: 'var(--success)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>Apply Now</span>
                  <ExternalLink size={12} />
                </a>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {!loading && totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '30px' }}>
          <button 
            disabled={page === 1} 
            onClick={() => setPage(prev => prev - 1)}
            className="btn-secondary"
            style={{ padding: '8px 16px' }}
          >
            Previous
          </button>
          <span style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Page {page} of {totalPages}
          </span>
          <button 
            disabled={page === totalPages} 
            onClick={() => setPage(prev => prev + 1)}
            className="btn-secondary"
            style={{ padding: '8px 16px' }}
          >
            Next
          </button>
        </div>
      )}

    </div>
  );
};

export default OpportunitiesList;
