import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  Upload, Sparkles, History, ListChecks 
} from 'lucide-react';

interface ATSCheckResult {
  id: string;
  score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  suggestions: string[];
  date: string;
}

const ResumeChecker: React.FC = () => {
  const { token, apiUrl, refreshUser } = useAuth();
  
  const [role, setRole] = useState('Software Development');
  const [file, setFile] = useState<File | null>(null);
  
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<ATSCheckResult | null>(null);
  const [error, setError] = useState('');
  
  const [history, setHistory] = useState<ATSCheckResult[]>([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    if (!token) return;
    try {
      setError('');
      const res = await fetch(`${apiUrl}/api/ats/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch history: ${res.statusText}`);
      }
      const data = await res.json();
      setHistory(data);
    } catch (e) {
      console.error("Error fetching history:", e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== 'application/pdf') {
        setError('Only PDF file formats are supported for parsing resume text.');
        setFile(null);
      } else {
        setFile(selectedFile);
        setError('');
      }
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) {
      setError('Please upload a PDF resume file first.');
      return;
    }

    setAnalyzing(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('role', role);
    formData.append('file', file);

    try {
      const res = await fetch(`${apiUrl}/api/ats/check`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Resume analysis failed');
      }
      
      const data = await res.json();
      setResult(data);
      fetchHistory();
      refreshUser(); // Update profile score
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Could not connect to ATS server';
      setError(errorMsg);
    } finally {
      setAnalyzing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--success)';
    if (score >= 50) return 'var(--warning)';
    return 'var(--error)';
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <h1 className="glow-text" style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '4px' }}>
          ATS Resume Checker
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Test your resume compatibility against automated tracking system criteria.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '30px', alignItems: 'start' }}>
        
        {/* Main Work Section */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Upload and Selection form */}
          <div className="glass-card">
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ListChecks size={20} color="var(--accent-purple)" />
              Scan Parameters
            </h2>

            {error && (
              <div style={{
                backgroundColor: 'var(--error-glow)',
                border: '1px solid var(--error)',
                color: 'var(--text-primary)',
                padding: '12px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '20px'
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleAnalyze} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Role Select */}
              <div>
                <label className="input-label">Target Role Profile</label>
                <select
                  value={role}
                  onChange={e => setRole(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-light)',
                    color: 'white',
                    padding: '14px',
                    borderRadius: '12px',
                    outline: 'none',
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.95rem'
                  }}
                >
                  <option value="Software Development">Software Development</option>
                  <option value="Data Science">Data Science</option>
                  <option value="AI/ML">AI / Machine Learning</option>
                </select>
              </div>

              {/* Upload Drag Box */}
              <div>
                <label className="input-label">Upload Resume PDF</label>
                <div style={{
                  border: '2px dashed var(--border-light)',
                  borderRadius: '12px',
                  padding: '40px 20px',
                  textAlign: 'center',
                  backgroundColor: 'rgba(255,255,255,0.01)',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s'
                }}>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      opacity: 0,
                      cursor: 'pointer'
                    }}
                  />
                  <Upload size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                  {file ? (
                    <div>
                      <p style={{ color: 'white', fontWeight: 600, fontSize: '0.95rem' }}>{file.name}</p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px' }}>
                        {(file.size / 1024 / 1024).toFixed(2)} MB • PDF Format
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p style={{ color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.9rem' }}>
                        Drag & Drop or Click to browse
                      </p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px' }}>
                        Supports only text-based PDF files up to 5MB
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={analyzing}
                style={{
                  padding: '14px',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: '8px',
                  marginTop: '10px'
                }}
              >
                <span>{analyzing ? 'Scanning Resume Content...' : 'Analyze ATS Compatibility'}</span>
                <Sparkles size={16} />
              </button>

            </form>
          </div>

          {/* Results Analysis scorecard view */}
          {result && (
            <div className="glass-card fade-in" style={{
              borderLeft: `4px solid ${getScoreColor(result.score)}`
            }}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>ATS Scanner Report</h3>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '2.2rem', fontWeight: 800, color: getScoreColor(result.score) }}>
                    {result.score}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>/100</span>
                </div>
              </div>

              <hr style={{ borderColor: 'var(--border-light)', marginBottom: '20px' }} />

              {/* Keywords comparison list pills */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                
                {/* Matched */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--success)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '10px' }}>
                    Matched Skills ({result.matched_keywords.length})
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {result.matched_keywords.map((kw, idx) => (
                      <span key={idx} style={{
                        fontSize: '0.75rem',
                        color: 'var(--success)',
                        backgroundColor: 'var(--success-glow)',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        border: '1px solid rgba(16, 185, 129, 0.2)'
                      }}>
                        {kw}
                      </span>
                    ))}
                    {result.matched_keywords.length === 0 && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>None matched.</span>
                    )}
                  </div>
                </div>

                {/* Missing */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '10px' }}>
                    Missing Keywords ({result.missing_keywords.length})
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {result.missing_keywords.map((kw, idx) => (
                      <span key={idx} style={{
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)',
                        backgroundColor: 'rgba(255,255,255,0.03)',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        border: '1px solid var(--border-light)'
                      }}>
                        {kw}
                      </span>
                    ))}
                    {result.missing_keywords.length === 0 && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--success)' }}>None! Skillset is perfect.</span>
                    )}
                  </div>
                </div>

              </div>

              {/* Suggestions */}
              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-purple)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '12px' }}>
                  Recommendations
                </h4>
                <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {result.suggestions.map((s, idx) => (
                    <li key={idx} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

            </div>
          )}

        </div>

        {/* Right Side Column: History Logs */}
        <div className="glass-card" style={{ padding: '20px', maxHeight: '550px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} color="var(--accent-purple)" />
            Scan History
          </h3>

          {history.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No previous resume evaluations.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {history.map(item => (
                <div 
                  key={item.id}
                  onClick={() => setResult(item)}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.01)',
                    border: '1px solid var(--border-light)',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>
                    <span style={{ color: 'white' }}>Score</span>
                    <span style={{ color: getScoreColor(item.score) }}>{item.score}%</span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {new Date(item.date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  );
};

export default ResumeChecker;
