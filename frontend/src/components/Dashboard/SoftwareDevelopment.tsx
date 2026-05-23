import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Terminal, Award, Search, Map, ChevronDown, ChevronUp, ExternalLink, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Question {
  id: string;
  title: string;
  difficulty: string;
  topic: string;
  platform: string;
  link: string;
  tags: string[];
  company_tags: string[];
}

interface Roadmap {
  id: string;
  role: string;
  description: string;
  steps: { phase: string; topics: string[] }[];
}

const SoftwareDevelopment: React.FC = () => {
  const { token, apiUrl } = useAuth();
  const navigate = useNavigate();

  // Questions States
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [topic, setTopic] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Roadmaps States
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  const [loadingRoadmaps, setLoadingRoadmaps] = useState(true);
  const [expandedRoadmap, setExpandedRoadmap] = useState<string | null>(null);

  // Constants
  const topics = ['Arrays', 'Strings', 'Linked List', 'Trees', 'Dynamic Programming', 'Graphs'];
  const difficulties = ['Beginner', 'Intermediate', 'Advanced'];

  useEffect(() => {
    fetchQuestions();
  }, [page, difficulty, topic]);

  useEffect(() => {
    fetchRoadmaps();
  }, []);

  const fetchQuestions = async () => {
    if (!token) return;
    setLoadingQuestions(true);
    try {
      let url = `${apiUrl}/api/software-development/questions?page=${page}&limit=8`;
      if (difficulty) url += `&difficulty=${encodeURIComponent(difficulty)}`;
      if (topic) url += `&topic=${encodeURIComponent(topic)}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setQuestions(data.questions);
        setTotalPages(data.total_pages);
        setTotalItems(data.total_items);
      }
    } catch (e) {
      console.error("Failed to load DSA questions:", e);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const fetchRoadmaps = async () => {
    if (!token) return;
    setLoadingRoadmaps(true);
    try {
      const res = await fetch(`${apiUrl}/api/software-development/roadmaps`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setRoadmaps(data.roadmaps);
        if (data.roadmaps.length > 0) {
          setExpandedRoadmap(data.roadmaps[0].role); // Expand first by default
        }
      }
    } catch (e) {
      console.error("Failed to load roadmaps:", e);
    } finally {
      setLoadingRoadmaps(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuestions();
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case 'Beginner': return 'var(--success)';
      case 'Intermediate': return '#3b82f6';
      case 'Advanced': return 'var(--error)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Back to Dashboard */}
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
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(217, 70, 239, 0.04) 100%)',
        border: '1px solid var(--border-glow)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
          <Terminal size={32} color="var(--accent-purple)" />
          <h1 className="glow-text" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
            Software Development Track
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '800px', margin: 0 }}>
          Accelerate your dev competencies. Practice from the vetted LeetCode and GeeksforGeeks sheets, follow modern career roadmaps, and build production-ready projects.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '40px',
        alignItems: 'flex-start'
      }}>
        
        {/* LEFT COLUMN: DSA PRACTICE SHEET */}
        <div style={{ flex: 2 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Award size={22} color="var(--success)" />
              Vetted DSA Problem Sheet
            </h2>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              {totalItems} challenges available
            </span>
          </div>

          {/* Filter Toolbar */}
          <div className="glass-card" style={{ padding: '20px', marginBottom: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px' }}>
              <div className="input-wrapper" style={{ flexGrow: 1 }}>
                <Search size={18} className="input-icon" />
                <input 
                  type="text" 
                  placeholder="Search problem title, tags, or companies..." 
                  value={search} 
                  onChange={e => setSearch(e.target.value)}
                  style={{ paddingLeft: '44px' }}
                />
              </div>
              <button type="submit" className="btn-primary" style={{ padding: '0 24px' }}>Search</button>
            </form>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {/* Topic Filters */}
              <select 
                value={topic} 
                onChange={e => { setTopic(e.target.value); setPage(1); }}
                style={{
                  padding: '10px 14px',
                  borderRadius: '10px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-light)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="">All Topics</option>
                {topics.map(t => <option key={t} value={t}>{t}</option>)}
              </select>

              {/* Difficulty Filters */}
              <select 
                value={difficulty} 
                onChange={e => { setDifficulty(e.target.value); setPage(1); }}
                style={{
                  padding: '10px 14px',
                  borderRadius: '10px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-light)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="">All Difficulties</option>
                {difficulties.map(d => <option key={d} value={d}>{d}</option>)}
              </select>

              {(topic || difficulty || search) && (
                <button 
                  onClick={() => {
                    setTopic('');
                    setDifficulty('');
                    setSearch('');
                    setPage(1);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-purple)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>

          {/* Questions Grid */}
          {loadingQuestions ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[...Array(4)].map((_, idx) => (
                <div key={idx} className="glass-card" style={{ height: '80px', animation: 'pulse 1.5s infinite' }}></div>
              ))}
            </div>
          ) : questions.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No practice problems found matching these criteria.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {questions.map((q) => (
                <div key={q.id} className="glass-card" style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '20px 24px',
                  transition: 'transform 0.2s ease, border-color 0.2s ease',
                  border: '1px solid var(--border-light)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-glow)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-light)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        color: getDifficultyColor(q.difficulty)
                      }}>
                        {q.difficulty}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', backgroundColor: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                        {q.topic}
                      </span>
                    </div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'white' }}>{q.title}</h3>
                    
                    {/* Tags */}
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
                      {q.company_tags.map((comp, cidx) => (
                        <span key={cidx} style={{ fontSize: '0.7rem', color: 'var(--text-muted)', border: '1px solid rgba(255,255,255,0.1)', padding: '1px 6px', borderRadius: '4px' }}>
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>

                  <a 
                    href={q.link} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="btn-secondary"
                    style={{
                      padding: '8px 16px',
                      fontSize: '0.8rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      borderRadius: '8px'
                    }}
                  >
                    <span>Solve on {q.platform}</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              ))}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px' }}>
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
          )}
        </div>

        {/* RIGHT COLUMN: CAREER ROADMAPS */}
        <div style={{ flex: 1, minWidth: '320px' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Map size={22} color="var(--accent-purple)" />
            Learning Roadmaps
          </h2>

          {loadingRoadmaps ? (
            <div className="glass-card" style={{ height: '200px', animation: 'pulse 1.5s infinite' }}></div>
          ) : roadmaps.length === 0 ? (
            <div className="glass-card" style={{ padding: '30px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No roadmaps available currently.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {roadmaps.map((r) => {
                const isExpanded = expandedRoadmap === r.role;
                return (
                  <div key={r.id} className="glass-card" style={{
                    border: isExpanded ? '1px solid var(--accent-purple)' : '1px solid var(--border-light)',
                    padding: '24px',
                    transition: 'all 0.2s ease'
                  }}>
                    <div 
                      onClick={() => setExpandedRoadmap(isExpanded ? null : r.role)}
                      style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                    >
                      <div>
                        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'white' }}>{r.role}</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '4px', lineHeight: '1.4' }}>
                          {r.description}
                        </p>
                      </div>
                      {isExpanded ? <ChevronUp size={20} color="var(--text-secondary)" /> : <ChevronDown size={20} color="var(--text-secondary)" />}
                    </div>

                    {/* Steps / Phases */}
                    {isExpanded && (
                      <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '20px', borderLeft: '2px solid rgba(139, 92, 246, 0.2)', paddingLeft: '16px', marginLeft: '6px' }}>
                        {r.steps.map((step, sidx) => (
                          <div key={sidx} style={{ position: 'relative' }}>
                            {/* Dot on line */}
                            <div style={{
                              position: 'absolute',
                              left: '-23px',
                              top: '2px',
                              width: '12px',
                              height: '12px',
                              borderRadius: '50%',
                              backgroundColor: 'var(--accent-purple)',
                              border: '2px solid var(--bg-main)'
                            }}></div>
                            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-purple)', marginBottom: '6px' }}>
                              {step.phase}
                            </h4>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                              {step.topics.map((top, tidx) => (
                                <span key={tidx} style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', backgroundColor: 'rgba(255,255,255,0.03)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                  {top}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default SoftwareDevelopment;
