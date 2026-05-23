import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Brain, Search, HelpCircle, Check, X, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Question {
  id: string;
  question: string;
  options: string[];
  answer: string;
  explanation: string;
  category: string;
  difficulty: string;
}

const AptitudeTest: React.FC = () => {
  const { token, apiUrl } = useAuth();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('Quantitative');
  const [difficulty, setDifficulty] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // States to keep track of user selections and toggle explanations
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
  const [showExplanations, setShowExplanations] = useState<Record<string, boolean>>({});

  const categories = ['Quantitative', 'Logical', 'Verbal'];
  const difficulties = ['Beginner', 'Intermediate', 'Advanced'];

  useEffect(() => {
    fetchQuestions();
    // Clear responses on category change
    setSelectedOptions({});
    setShowExplanations({});
  }, [page, category, difficulty]);

  const fetchQuestions = async () => {
    if (!token) return;
    setLoading(true);
    try {
      let url = `${apiUrl}/api/aptitude/questions?page=${page}&limit=5`;
      if (category) url += `&category=${encodeURIComponent(category)}`;
      if (difficulty) url += `&difficulty=${encodeURIComponent(difficulty)}`;
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
      console.error("Failed to load aptitude questions:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuestions();
  };

  const handleOptionSelect = (questionId: string, option: string) => {
    // Only allow selection once per question
    if (selectedOptions[questionId]) return;
    
    setSelectedOptions(prev => ({ ...prev, [questionId]: option }));
    setShowExplanations(prev => ({ ...prev, [questionId]: true }));
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

      {/* Header */}
      <div className="glass-card-glow" style={{
        padding: '30px 40px',
        borderRadius: '16px',
        marginBottom: '40px',
        background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%)',
        border: '1px solid var(--border-glow)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
          <Brain size={32} color="var(--accent-magenta)" />
          <h1 className="glow-text" style={{ fontSize: '2.2rem', fontWeight: 800 }}>
            Aptitude & Reasoning Practice
          </h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', margin: 0 }}>
          Sharpen your cognitive skills for high-stakes screening rounds. Select categories, take practice sheets, and analyze step-by-step mathematical explanations.
        </p>
      </div>

      {/* Categories Tabs */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '30px', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px' }}>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => { setCategory(cat); setPage(1); }}
            className={category === cat ? 'btn-primary' : 'btn-secondary'}
            style={{
              padding: '10px 24px',
              borderRadius: '10px',
              fontSize: '0.9rem',
              fontWeight: 600,
              background: category === cat ? 'linear-gradient(135deg, var(--accent-magenta) 0%, #f43f5e 100%)' : undefined,
              boxShadow: category === cat ? '0 4px 15px rgba(217, 70, 239, 0.2)' : undefined
            }}
          >
            {cat} Ability
          </button>
        ))}
      </div>

      {/* Filtering Toolbar */}
      <div className="glass-card" style={{ padding: '20px', marginBottom: '30px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '12px', flexGrow: 1 }}>
          <div className="input-wrapper" style={{ flexGrow: 1 }}>
            <Search size={18} className="input-icon" />
            <input 
              type="text" 
              placeholder="Search question text..." 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '44px' }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ padding: '0 20px', background: 'linear-gradient(135deg, var(--accent-magenta) 0%, #f43f5e 100%)' }}>Search</button>
        </form>

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
      </div>

      {/* Questions list */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {[...Array(3)].map((_, idx) => (
            <div key={idx} className="glass-card" style={{ height: '180px', animation: 'pulse 1.5s infinite' }}></div>
          ))}
        </div>
      ) : questions.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No aptitude questions available matching these filters currently.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
          {questions.map((q, idx) => {
            const userSelection = selectedOptions[q.id];
            const isExplanationVisible = showExplanations[q.id];
            
            return (
              <div key={q.id} className="glass-card" style={{ padding: '30px', border: '1px solid var(--border-light)' }}>
                {/* Header info */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                    Question {(page - 1) * 5 + idx + 1}
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: getDifficultyColor(q.difficulty)
                  }}>
                    {q.difficulty}
                  </span>
                </div>

                {/* Question Statement */}
                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'white', lineHeight: '1.5', marginBottom: '20px' }}>
                  {q.question}
                </h3>

                {/* Options Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                  {q.options.map((opt, oidx) => {
                    const isSelected = userSelection === opt;
                    const isCorrectAnswer = opt === q.answer;
                    
                    let cardBorderColor = 'var(--border-light)';
                    let cardBg = 'var(--bg-input)';
                    let icon = null;

                    if (userSelection) {
                      if (isCorrectAnswer) {
                        cardBorderColor = 'var(--success)';
                        cardBg = 'rgba(16, 185, 129, 0.08)';
                        icon = <Check size={16} color="var(--success)" />;
                      } else if (isSelected) {
                        cardBorderColor = 'var(--error)';
                        cardBg = 'rgba(248, 113, 113, 0.08)';
                        icon = <X size={16} color="var(--error)" />;
                      }
                    }

                    return (
                      <div 
                        key={oidx}
                        onClick={() => handleOptionSelect(q.id, opt)}
                        style={{
                          border: `1px solid ${cardBorderColor}`,
                          backgroundColor: cardBg,
                          borderRadius: '10px',
                          padding: '14px 18px',
                          cursor: userSelection ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          transition: 'all 0.15s ease'
                        }}
                        onMouseEnter={(e) => {
                          if (!userSelection) {
                            e.currentTarget.style.borderColor = 'var(--accent-purple)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!userSelection) {
                            e.currentTarget.style.borderColor = cardBorderColor;
                          }
                        }}
                      >
                        <span style={{ fontSize: '0.9rem', color: isSelected ? 'white' : 'var(--text-primary)' }}>{opt}</span>
                        {icon}
                      </div>
                    );
                  })}
                </div>

                {/* Toggleable explanation */}
                {isExplanationVisible && (
                  <div className="fade-in" style={{
                    marginTop: '20px',
                    padding: '20px',
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    borderRadius: '10px',
                    borderLeft: `4px solid ${userSelection === q.answer ? 'var(--success)' : 'var(--error)'}`
                  }}>
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.92rem', fontWeight: 700, color: 'white', marginBottom: '8px' }}>
                      <HelpCircle size={16} />
                      <span>{userSelection === q.answer ? 'Correct Solution!' : `Incorrect. The correct answer is: ${q.answer}`}</span>
                    </h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.6', whiteSpace: 'pre-line', margin: 0 }}>
                      {q.explanation}
                    </p>
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

export default AptitudeTest;
