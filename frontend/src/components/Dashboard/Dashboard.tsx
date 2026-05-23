import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  MessageSquare, FileText, Briefcase, Award, 
  Terminal, Sparkles, Brain, ArrowRight, ExternalLink,
  Calendar, Code, CheckCircle
} from 'lucide-react';

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

interface DSAQuestion {
  id: string;
  title: string;
  difficulty: string;
  topic: string;
  platform: string;
  link: string;
  tags: string[];
}

interface InterviewQuestion {
  id: string;
  company_name: string;
  role: string;
  interview_type: string;
  question: string;
  category: string;
}

const Dashboard: React.FC = () => {
  const { user, token, apiUrl, refreshUser } = useAuth();
  const navigate = useNavigate();
  
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loadingOpportunities, setLoadingOpportunities] = useState(true);
  const [oppFilter, setOppFilter] = useState('All');

  const [dsaQuestions, setDsaQuestions] = useState<DSAQuestion[]>([]);
  const [interviewQuestions, setInterviewQuestions] = useState<InterviewQuestion[]>([]);
  const [loadingResources, setLoadingResources] = useState(true);

  const [stats, setStats] = useState({
    interviewsCount: 0,
    submissionsCount: 0,
    atsCount: 0,
    lastAtsScore: 0.0,
    lastInterviewScore: 0.0
  });

  useEffect(() => {
    refreshUser();
    fetchStats();
  }, []);

  useEffect(() => {
    if (token) {
      fetchOpportunities();
    }
  }, [oppFilter, token]);

  useEffect(() => {
    if (token) {
      fetchTrendingResources();
    }
  }, [token]);

  const fetchStats = async () => {
    if (!token) return;
    try {
      // Fetch coding submissions count
      const codingRes = await fetch(`${apiUrl}/api/coding/submissions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const codingData = await codingRes.json();
      
      // Fetch interview history count
      const interviewRes = await fetch(`${apiUrl}/api/interview/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const interviewData = await interviewRes.json();

      // Fetch ATS checker count
      const atsRes = await fetch(`${apiUrl}/api/ats/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const atsData = await atsRes.json();

      const passedCoding = codingData.filter((s: any) => s.status === 'Pass').length;
      const lastAts = atsData.length > 0 ? atsData[0].score : 0.0;
      const completedInterviews = interviewData.filter((i: any) => i.completed);
      const lastInterview = completedInterviews.length > 0 ? completedInterviews[0].score : 0.0;

      setStats({
        interviewsCount: completedInterviews.length,
        submissionsCount: passedCoding,
        atsCount: atsData.length,
        lastAtsScore: lastAts,
        lastInterviewScore: lastInterview
      });
    } catch (e) {
      console.error("Failed to load dashboard statistics:", e);
    }
  };

  const fetchOpportunities = async () => {
    if (!token) return;
    setLoadingOpportunities(true);
    try {
      let url = `${apiUrl}/api/opportunities?limit=4`;
      if (oppFilter !== 'All') {
        url += `&opportunity_type=${encodeURIComponent(oppFilter)}`;
      }
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setOpportunities(data.opportunities || []);
      }
    } catch (e) {
      console.error("Failed to fetch opportunities:", e);
    } finally {
      setLoadingOpportunities(false);
    }
  };

  const fetchTrendingResources = async () => {
    if (!token) return;
    setLoadingResources(true);
    try {
      const dsaRes = await fetch(`${apiUrl}/api/software-development/questions?limit=3`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const dsaData = await dsaRes.json();
      if (dsaData.success) {
        setDsaQuestions(dsaData.questions || []);
      }

      const interviewRes = await fetch(`${apiUrl}/api/interview/questions?limit=3`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const interviewData = await interviewRes.json();
      if (interviewData.success) {
        setInterviewQuestions(interviewData.questions || []);
      }
    } catch (e) {
      console.error("Failed to fetch trending resources:", e);
    } finally {
      setLoadingResources(false);
    }
  };

  const getDifficultyColor = (diff: string) => {
    const d = diff.toLowerCase();
    if (d === 'beginner' || d === 'easy') return { text: 'var(--success)', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)' };
    if (d === 'intermediate' || d === 'medium') return { text: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)' };
    return { text: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.3)' };
  };

  const getOppTypeColor = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('hackathon')) return { text: '#60a5fa', bg: 'rgba(59, 130, 246, 0.12)' };
    if (t.includes('internship')) return { text: 'var(--accent-purple)', bg: 'rgba(139, 92, 246, 0.12)' };
    if (t.includes('contest')) return { text: 'var(--success)', bg: 'rgba(16, 185, 129, 0.12)' };
    if (t.includes('open-source')) return { text: 'var(--accent-magenta)', bg: 'rgba(217, 70, 239, 0.12)' };
    return { text: '#fb923c', bg: 'rgba(251, 146, 60, 0.12)' };
  };

  if (!user) return null;

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Welcome Section */}
      <div className="glass-card-glow" style={{
        padding: '30px 40px',
        borderRadius: '16px',
        marginBottom: '30px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(217, 70, 239, 0.04) 100%)',
        border: '1px solid var(--border-glow)'
      }}>
        <div>
          <span style={{
            fontSize: '0.85rem',
            color: 'var(--accent-purple)',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Prep Accelerator Dashboard
          </span>
          <h1 className="glow-text" style={{ fontSize: '2.2rem', fontWeight: 800, marginTop: '4px', marginBottom: '8px' }}>
            Welcome, {user.name}! 🚀
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '600px' }}>
            Elevate your placement readiness. Master coding tracks, practice aptitude sheets, prepare for company-specific interview logs, and find curated opportunities.
          </p>
        </div>
        
        {/* Profile score overview card */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
            <Award size={24} color="var(--success)" />
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)' }}>
              {user.profile_score?.toFixed(1) || '0.0'}
            </span>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Placement Readiness Score</span>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '20px',
        marginBottom: '40px'
      }}>
        
        {/* DSA Solved Card */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px', cursor: 'pointer' }} onClick={() => navigate('/software-development')}>
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid var(--success)',
            borderRadius: '12px',
            padding: '16px',
            color: 'var(--success)'
          }}>
            <Terminal size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 700 }}>{stats.submissionsCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>DSA Challenges Solved</span>
          </div>
        </div>

        {/* Mock Interviews Card */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px', cursor: 'pointer' }} onClick={() => navigate('/interview-prep')}>
          <div style={{
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            border: '1px solid var(--accent-violet)',
            borderRadius: '12px',
            padding: '16px',
            color: 'var(--accent-violet)'
          }}>
            <MessageSquare size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 700 }}>{stats.interviewsCount}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Mock Prep Challenges</span>
          </div>
        </div>

        {/* ATS Resume Scan Card */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px', cursor: 'pointer' }} onClick={() => navigate('/resume')}>
          <div style={{
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid #3b82f6',
            borderRadius: '12px',
            padding: '16px',
            color: '#3b82f6'
          }}>
            <FileText size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 700 }}>{stats.lastAtsScore > 0 ? `${stats.lastAtsScore}%` : 'N/A'}</h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Latest Resume ATS Match</span>
          </div>
        </div>

      </div>

      {/* Prepare by Track / Core Features */}
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Brain size={22} color="var(--accent-purple)" />
        Select Your Career Track
      </h2>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '25px',
        marginBottom: '45px'
      }}>
        
        {/* Software Development Track */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '240px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{
                background: 'rgba(139, 92, 246, 0.15)',
                color: 'var(--accent-purple)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                Development
              </div>
              <Terminal size={20} color="var(--text-muted)" />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>Software Development</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Master OOPs, systems design, and DSA algorithms. Access structured developer roadmaps, interactive sheet targets, and verified coding links.
            </p>
          </div>
          <button 
            className="btn-primary" 
            onClick={() => {
              navigate('/software-development');
            }}
            style={{
              padding: '10px 16px',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginTop: '20px'
            }}
          >
            <span>Explore Dev Track</span>
            <ArrowRight size={16} />
          </button>
        </div>

        {/* Aptitude Prep Track */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '240px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                Aptitude
              </div>
              <Brain size={20} color="var(--text-muted)" />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>Aptitude Practice</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Test your Quantitative, Logical, and Verbal abilities. Check your solutions with instant green/red logs and toggle detailed mathematical breakdowns.
            </p>
          </div>
          <button 
            className="btn-primary" 
            onClick={() => {
              navigate('/aptitude');
            }}
            style={{
              background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
              boxShadow: '0 4px 15px rgba(37, 99, 235, 0.3)',
              padding: '10px 16px',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginTop: '20px'
            }}
          >
            <span>Practice Aptitude</span>
            <ArrowRight size={16} />
          </button>
        </div>

        {/* Mock Interview Prep Track */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '240px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{
                background: 'rgba(217, 70, 239, 0.15)',
                color: 'var(--accent-magenta)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                Interview Prep
              </div>
              <MessageSquare size={20} color="var(--text-muted)" />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>Mock Interview Center</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>
              Study actual FAANG mock logs, HR questions, technical questionnaires, and behavior answers categorized beautifully by corporate targets.
            </p>
          </div>
          <button 
            className="btn-primary" 
            onClick={() => {
              navigate('/interview-prep');
            }}
            style={{
              background: 'linear-gradient(135deg, var(--accent-magenta) 0%, #f43f5e 100%)',
              boxShadow: '0 4px 15px rgba(217, 70, 239, 0.3)',
              padding: '10px 16px',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginTop: '20px'
            }}
          >
            <span>Explore Prep Center</span>
            <ArrowRight size={16} />
          </button>
        </div>

      </div>

      {/* Dynamic Side/Detail Widgets: Trending Placement Prep Resources */}
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Sparkles size={22} color="var(--accent-purple)" />
        🔥 Hot Placement Prep Resources
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
        gap: '25px',
        marginBottom: '45px'
      }}>
        {/* DSA Trending Questions */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Code size={18} color="var(--success)" />
              Recent Coding Questions
            </h3>
            <button className="nav-link" onClick={() => navigate('/software-development')} style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>View All</span>
              <ArrowRight size={12} />
            </button>
          </div>

          {loadingResources ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading curated coding challenges...
            </div>
          ) : dsaQuestions.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No recent questions available.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {dsaQuestions.map((q) => {
                const diffStyle = getDifficultyColor(q.difficulty);
                return (
                  <a
                    key={q.id}
                    href={q.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="glass-card-hover"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                      textDecoration: 'none',
                      transition: 'transform 0.2s ease, border-color 0.2s ease'
                    }}
                  >
                    <div style={{ flex: 1, marginRight: '15px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                          {q.platform} • {q.topic}
                        </span>
                      </div>
                      <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'white' }}>{q.title}</h4>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color: diffStyle.text,
                        background: diffStyle.bg,
                        border: `1px solid ${diffStyle.border}`,
                        padding: '4px 10px',
                        borderRadius: '6px',
                        textTransform: 'capitalize'
                      }}>
                        {q.difficulty}
                      </span>
                      <ExternalLink size={14} color="var(--text-muted)" />
                    </div>
                  </a>
                );
              })}
            </div>
          )}
        </div>

        {/* Featured Interview Prep */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={18} color="var(--accent-purple)" />
              Featured Interview Questions
            </h3>
            <button className="nav-link" onClick={() => navigate('/interview-prep')} style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>View All</span>
              <ArrowRight size={12} />
            </button>
          </div>

          {loadingResources ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Loading verified company interview cards...
            </div>
          ) : interviewQuestions.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No recent interview prep sheets.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {interviewQuestions.map((q) => (
                <div
                  key={q.id}
                  onClick={() => navigate('/interview-prep')}
                  className="glass-card-hover"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '14px 18px',
                    borderRadius: '10px',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    cursor: 'pointer',
                    transition: 'transform 0.2s ease, border-color 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: 'var(--accent-purple)',
                      background: 'rgba(139, 92, 246, 0.1)',
                      padding: '2px 8px',
                      borderRadius: '6px'
                    }}>
                      {q.company_name}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {q.interview_type} • {q.role}
                    </span>
                  </div>
                  <p style={{
                    fontSize: '0.9rem',
                    color: 'white',
                    fontWeight: 500,
                    lineHeight: '1.4',
                    margin: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {q.question}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recommended Opportunities */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Briefcase size={22} color="var(--accent-purple)" />
          Recommended Opportunities
        </h2>
        
        {/* Scraped opportunity filter options */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {['All', 'Internship', 'Hackathon', 'Coding Contest', 'Open-Source Program', 'Remote Job'].map(type => (
            <button
              key={type}
              onClick={() => setOppFilter(type)}
              className={oppFilter === type ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '6px 14px', fontSize: '0.8rem', borderRadius: '8px' }}
            >
              {type === 'All' ? 'All Opportunities' : type}
            </button>
          ))}
        </div>
      </div>

      {loadingOpportunities ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          🔍 Scraping active hackathons, contests, and internships from Devfolio and GitHub feeds...
        </div>
      ) : opportunities.length === 0 ? (
        <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No active opportunities found matching this filter category. Check back shortly!
        </div>
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px'
          }}>
            {opportunities.map((opp) => {
              const badgeStyle = getOppTypeColor(opp.opportunity_type);
              return (
                <div key={opp.id} className="glass-card" style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  position: 'relative',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  borderRadius: '12px',
                  padding: '22px',
                  minHeight: '260px'
                }}>
                  <div>
                    {/* Header Logo + Info */}
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
                      {opp.logo ? (
                        <img 
                          src={opp.logo} 
                          alt={opp.company} 
                          style={{ width: '40px', height: '40px', borderRadius: '8px', border: '1px solid var(--border-light)', objectFit: 'contain', backgroundColor: 'rgba(255, 255, 255, 0.05)' }} 
                        />
                      ) : (
                        <div style={{
                          width: '40px',
                          height: '40px',
                          borderRadius: '8px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          border: '1px solid var(--border-light)',
                          fontWeight: 'bold',
                          color: 'var(--text-secondary)'
                        }}>
                          {opp.company.substring(0, 1).toUpperCase()}
                        </div>
                      )}
                      <div style={{ overflow: 'hidden' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                          {opp.company}
                        </h4>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{opp.location}</span>
                      </div>
                    </div>

                    {/* Badge */}
                    <div style={{ marginBottom: '12px' }}>
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color: badgeStyle.text,
                        background: badgeStyle.bg,
                        padding: '4px 10px',
                        borderRadius: '6px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.02em'
                      }}>
                        {opp.opportunity_type}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '12px', color: 'white', lineHeight: '1.4' }}>
                      {opp.title}
                    </h3>

                    {/* Eligibility details */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                      <CheckCircle size={14} color="var(--success)" />
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {opp.eligibility}
                      </span>
                    </div>
                  </div>

                  {/* Apply / Details bottom strip */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar size={14} color="#f43f5e" />
                      <span style={{ fontSize: '0.75rem', color: '#f43f5e', fontWeight: 600 }}>
                        {opp.deadline ? `Till: ${opp.deadline}` : 'Apply soon'}
                      </span>
                    </div>
                    
                    <a 
                      href={opp.apply_link} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="nav-link"
                      style={{
                        fontSize: '0.8rem',
                        padding: '4px 8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        color: 'var(--accent-purple)'
                      }}
                    >
                      <span>Apply Now</span>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>

          {/* View All CTA */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '30px' }}>
            <button 
              className="btn-secondary" 
              onClick={() => navigate('/opportunities')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                fontSize: '0.95rem',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-light)',
                borderRadius: '8px',
                cursor: 'pointer',
                color: 'white',
                fontWeight: 600,
                transition: 'background-color 0.2s ease, border-color 0.2s ease'
              }}
            >
              <span>View All Opportunities</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
