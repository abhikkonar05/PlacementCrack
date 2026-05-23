import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MessageSquare, Search, Award, HelpCircle, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Question {
  id: string;
  company_name: string;
  role: string;
  interview_type: string;
  question: string;
  answer: string;
  experience: string;
  category: string;
}

const MockInterviewPrep: React.FC = () => {
  const { token, apiUrl } = useAuth();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [interviewType, setInterviewType] = useState('Technical');
  const [company, setCompany] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // States to toggle answer blocks
  const [expandedAnswers, setExpandedAnswers] = useState<Record<string, boolean>>({});

  const interviewTypes = ['Technical', 'HR', 'Behavioral'];

  useEffect(() => {
    fetchQuestions();
    setExpandedAnswers({});
  }, [page, interviewType, company]);

  const fetchQuestions = async () => {
    if (!token) return;
    setLoading(true);
    try {
      let url = `${apiUrl}/api/interview/questions?page=${page}&limit=5`;
      if (interviewType) url += `&interview_type=${encodeURIComponent(interviewType)}`;
      if (company) url += `&company=${encodeURIComponent(company)}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        setQuestions(data.questions);
        setTotalPages(data.total_pages);
      }
    } catch (e) {
      console.error("Failed to load interview questions:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuestions();
  };

  const toggleAnswer = (qId: string) => {
    setExpandedAnswers(prev => ({ ...prev, [qId]: !prev[qId] }));
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1000px', margin: '0 auto' }}>
      
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
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(217, 70, 239, 0.04) 100%)',
        border: '1px solid var(--border-glow)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
          <MessageSquare size={32} color="var(--accent-violet)" />
          <h1 className="glow-text" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
            Mock Interview Prep Track
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', margin: 0 }}>
          Excel in your technical and behavioral assessment rounds. Browse genuine company-wise question logs, formulate structured answers, and inspect developer experience files.
        </p>
      </div>

      {/* Interview Types Tabs */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '30px', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px' }}>
        {interviewTypes.map(type => (
          <button
            key={type}
            onClick={() => { setInterviewType(type); setPage(1); }}
            className={interviewType === type ? 'btn-primary' : 'btn-secondary'}
            style={{
              padding: '10px 24px',
              borderRadius: '10px',
              fontSize: '0.9rem',
              fontWeight: 600
            }}
          >
            {type} Round
          </button>
        ))}
      </div>

      {/* Filter toolbar */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '30px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px', flexGrow: 1 }}>
          <div className="input-wrapper" style={{ flexGrow: 1 }}>
            <Search size={18} className="input-icon" />
            <input 
              type="text" 
              placeholder="Search keyword in questions..." 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '44px' }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ padding: '0 20px' }}>Search</button>
        </form>

        <input 
          type="text" 
          placeholder="Filter by Company (e.g. Google)..." 
          value={company}
          onChange={e => { setCompany(e.target.value); setPage(1); }}
          style={{
            padding: '10px 14px',
            borderRadius: '10px',
            backgroundColor: 'var(--bg-input)',
            border: '1px solid var(--border-light)',
            color: 'var(--text-primary)',
            outline: 'none',
            fontSize: '0.9rem',
            width: '240px'
          }}
        />
      </div>

      {/* Questions list */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {[...Array(3)].map((_, idx) => (
            <div key={idx} className="glass-card" style={{ height: '160px', animation: 'pulse 1.5s infinite' }}></div>
          ))}
        </div>
      ) : questions.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No interview questions matching these criteria.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {questions.map((q) => {
            const isAnswerOpen = expandedAnswers[q.id];
            
            return (
              <div key={q.id} className="glass-card" style={{ padding: '30px', border: '1px solid var(--border-light)' }}>
                {/* Meta details header */}
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)', padding: '3px 10px', borderRadius: '6px' }}>
                    {q.company_name}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', backgroundColor: 'rgba(255,255,255,0.05)', padding: '3px 10px', borderRadius: '6px' }}>
                    {q.role}
                  </span>
                </div>

                {/* Question Statement */}
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'white', lineHeight: '1.5', marginBottom: '20px' }}>
                  Q: {q.question}
                </h3>

                {/* Toggle Button */}
                <button
                  onClick={() => toggleAnswer(q.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-purple)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.88rem',
                    padding: 0
                  }}
                >
                  <span>{isAnswerOpen ? 'Hide Suggested Answer & Experience' : 'View Suggested Answer & Experience'}</span>
                  {isAnswerOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {/* Answer and Experience blocks */}
                {isAnswerOpen && (
                  <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
                    {/* Suggested Answer */}
                    <div style={{ padding: '20px', backgroundColor: 'rgba(255,255,255,0.01)', borderRadius: '8px', borderLeft: '3px solid var(--accent-violet)' }}>
                      <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'white', marginBottom: '6px' }}>
                        <HelpCircle size={15} color="var(--accent-purple)" />
                        <span>Suggested Answer Framework</span>
                      </h4>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.6', margin: 0 }}>
                        {q.answer}
                      </p>
                    </div>

                    {/* Candidate Experience */}
                    {q.experience && (
                      <div style={{ padding: '20px', backgroundColor: 'rgba(255,255,255,0.01)', borderRadius: '8px', borderLeft: '3px solid var(--success)' }}>
                        <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'white', marginBottom: '6px' }}>
                          <Award size={15} color="var(--success)" />
                          <span>Candidate Experience Log</span>
                        </h4>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.6', margin: 0 }}>
                          {q.experience}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

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
  );
};

export default MockInterviewPrep;
