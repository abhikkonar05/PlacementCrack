import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Play, Code2, AlertTriangle, CheckCircle, Terminal, History } from 'lucide-react';

interface Problem {
  id: string;
  title: string;
  difficulty: string;
  description: string;
  template: string;
}

interface Submission {
  id: string;
  problem_id: string;
  language: string;
  code: string;
  status: string;
  space_complexity: string;
  time_complexity: string;
  feedback: string;
  date: string;
}

const CodingTest: React.FC = () => {
  const { token, apiUrl, refreshUser } = useAuth();
  
  const [problems, setProblems] = useState<Problem[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
  const [code, setCode] = useState('');
  
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState<any | null>(null);
  const [error, setError] = useState('');
  
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loadingProblems, setLoadingProblems] = useState(true);

  useEffect(() => {
    fetchProblems();
    fetchSubmissions();
  }, []);

  const fetchProblems = async () => {
    if (!token) return;
    try {
      setError('');
      const res = await fetch(`${apiUrl}/api/coding/problems`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        throw new Error(`Failed to load problems: ${res.statusText}`);
      }
      const data = await res.json();
      setProblems(data);
      if (data.length > 0) {
        setSelectedProblem(data[0]);
        setCode(data[0].template);
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Failed to load problems";
      setError(errorMsg);
      console.error("Failed to load problems:", e);
    } finally {
      setLoadingProblems(false);
    }
  };

  const fetchSubmissions = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiUrl}/api/coding/submissions`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        throw new Error(`Failed to load submissions: ${res.statusText}`);
      }
      const data = await res.json();
      setSubmissions(data);
    } catch (e) {
      console.error("Failed to load submissions:", e);
    }
  };

  const handleSelectProblem = (prob: Problem) => {
    setSelectedProblem(prob);
    setCode(prob.template);
    setRunResult(null);
  };

  const handleSubmitCode = async () => {
    if (!selectedProblem || !token) {
      setError('Missing problem or authentication token');
      return;
    }
    setRunning(true);
    setRunResult(null);
    setError('');

    try {
      const res = await fetch(`${apiUrl}/api/coding/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          problem_id: selectedProblem.id,
          code: code,
          language: 'python'
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to submit code');
      }
      
      const data = await res.json();
      setRunResult(data);
      fetchSubmissions(); // Reload submission list
      refreshUser(); // Update profile score
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Could not connect to code compiler sandbox';
      setError(errorMsg);
      setRunResult({
        status: 'Error',
        message: errorMsg,
        feedback: 'Please ensure the Python backend is running and try again.'
      });
    } finally {
      setRunning(false);
    }
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case 'easy': return 'var(--color-easy)';
      case 'medium': return 'var(--color-medium)';
      case 'hard': return 'var(--color-hard)';
      default: return 'white';
    }
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1600px', margin: '0 auto' }}>
      
      {/* Page Title */}
      <div style={{ marginBottom: '24px' }}>
        <h1 className="glow-text" style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '4px' }}>
          DSA Practice Sandbox
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Code, run, compile, and evaluate code complexities in isolated python shell.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '320px 1fr',
        gap: '30px',
        alignItems: 'start'
      }}>
        
        {/* Left Side Column: Problems List & Submission History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Challenges List Card */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Code2 size={18} color="var(--accent-purple)" />
              Coding Tasks
            </h3>
            
            {loadingProblems ? (
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Loading challenges...</span>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {problems.map(prob => (
                  <div 
                    key={prob.id}
                    onClick={() => handleSelectProblem(prob)}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      border: selectedProblem?.id === prob.id ? '1px solid var(--accent-violet)' : '1px solid var(--border-light)',
                      background: selectedProblem?.id === prob.id ? 'rgba(139, 92, 246, 0.06)' : 'rgba(255, 255, 255, 0.01)',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.85rem', color: selectedProblem?.id === prob.id ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                        {prob.title}
                      </span>
                    </div>
                    <span style={{ 
                      fontSize: '0.75rem', 
                      color: getDifficultyColor(prob.difficulty), 
                      fontWeight: 700,
                      textTransform: 'uppercase'
                    }}>
                      {prob.difficulty}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Submissions History Card */}
          <div className="glass-card" style={{ padding: '20px', maxHeight: '350px', overflowY: 'auto' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={18} color="var(--accent-purple)" />
              My Submissions
            </h3>
            
            {submissions.length === 0 ? (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No previous compilations.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {submissions.map(sub => {
                  const probName = problems.find(p => p.id === sub.problem_id)?.title || sub.problem_id;
                  return (
                    <div key={sub.id} style={{
                      padding: '10px',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderLeft: `3px solid ${sub.status === 'Pass' ? 'var(--success)' : 'var(--error)'}`
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{probName}</span>
                        <span style={{ color: sub.status === 'Pass' ? 'var(--success)' : 'var(--error)', fontWeight: 700 }}>
                          {sub.status}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                        <span>Python</span>
                        <span>{new Date(sub.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

        {/* Right Side Column: Code Workspace Split Screen */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          
          {error && (
            <div style={{
              backgroundColor: 'var(--error-glow)',
              border: '1px solid var(--error)',
              color: 'var(--text-primary)',
              padding: '14px',
              borderRadius: '8px',
              fontSize: '0.9rem',
              marginBottom: '10px'
            }}>
              <strong>Error:</strong> {error}
            </div>
          )}
          
          {selectedProblem && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>
              
              {/* Problem Description Panel */}
              <div className="glass-card" style={{ minHeight: '520px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>{selectedProblem.title}</h2>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: getDifficultyColor(selectedProblem.difficulty),
                    backgroundColor: `${getDifficultyColor(selectedProblem.difficulty)}1a`,
                    border: `1px solid ${getDifficultyColor(selectedProblem.difficulty)}`,
                    padding: '4px 8px',
                    borderRadius: '4px',
                    textTransform: 'uppercase'
                  }}>
                    {selectedProblem.difficulty}
                  </span>
                </div>
                
                <hr style={{ borderColor: 'var(--border-light)', marginBottom: '14px' }} />
                
                {/* Formatted Text Description */}
                <div style={{
                  color: 'var(--text-secondary)',
                  fontSize: '0.9rem',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'var(--font-body)',
                  flexGrow: 1,
                  overflowY: 'auto'
                }}>
                  {selectedProblem.description}
                </div>
              </div>

              {/* Code Editor Panel */}
              <div className="glass-card" style={{ minHeight: '520px', display: 'flex', flexDirection: 'column', padding: '0' }}>
                {/* Editor Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 24px',
                  background: 'rgba(255,255,255,0.02)',
                  borderBottom: '1px solid var(--border-light)',
                  borderTopLeftRadius: '16px',
                  borderTopRightRadius: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 600 }}>
                    <Terminal size={16} color="var(--accent-purple)" />
                    <span>solution.py</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Language: Python 3</span>
                </div>
                
                {/* Editor Code Textarea */}
                <div style={{ flexGrow: 1, position: 'relative' }}>
                  <textarea
                    value={code}
                    onChange={e => setCode(e.target.value)}
                    spellCheck="false"
                    style={{
                      width: '100%',
                      height: '380px',
                      background: 'transparent',
                      color: '#a7f3d0', // nice code green
                      fontFamily: 'Consolas, Monaco, monospace',
                      fontSize: '0.9rem',
                      padding: '20px',
                      border: 'none',
                      outline: 'none',
                      resize: 'none',
                      lineHeight: '1.5'
                    }}
                  />
                </div>

                {/* Editor Footer Toolbar */}
                <div style={{
                  padding: '12px 24px',
                  background: 'rgba(255,255,255,0.02)',
                  borderTop: '1px solid var(--border-light)',
                  borderBottomLeftRadius: '16px',
                  borderBottomRightRadius: '16px',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  alignItems: 'center'
                }}>
                  <button
                    className="btn-primary"
                    onClick={handleSubmitCode}
                    disabled={running}
                    style={{
                      padding: '8px 20px',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    <Play size={14} fill="white" />
                    <span>{running ? 'Running...' : 'Run Submissions'}</span>
                  </button>
                </div>

              </div>

            </div>
          )}

          {/* Execution Result Log Console */}
          {runResult && (
            <div className="glass-card fade-in" style={{
              borderLeft: `4px solid ${
                runResult.status === 'Pass' ? 'var(--success)' : 
                runResult.status === 'Fail' ? 'var(--warning)' : 'var(--error)'
              }`
            }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
                {runResult.status === 'Pass' ? (
                  <CheckCircle size={20} color="var(--success)" />
                ) : (
                  <AlertTriangle size={20} color={runResult.status === 'Fail' ? 'var(--warning)' : 'var(--error)'} />
                )}
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                  Compiler Status: <span style={{
                    color: runResult.status === 'Pass' ? 'var(--success)' :
                           runResult.status === 'Fail' ? 'var(--warning)' : 'var(--error)'
                  }}>{runResult.status}</span>
                </h3>
              </div>

              {/* Console logs */}
              <div style={{
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                padding: '14px',
                borderRadius: '8px',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
                marginBottom: '14px',
                border: '1px solid var(--border-light)',
                whiteSpace: 'pre-wrap'
              }}>
                {runResult.message}
              </div>

              {/* Complexity Metrics if Pass */}
              {runResult.status === 'Pass' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', margin: '14px 0' }}>
                  <div className="glass-card" style={{ padding: '12px', textAlign: 'center', background: 'rgba(255,255,255,0.01)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Estimated Time Complexity</span>
                    <h4 style={{ fontSize: '1.2rem', color: 'var(--accent-purple)', fontWeight: 700, marginTop: '4px' }}>
                      {runResult.time_complexity}
                    </h4>
                  </div>
                  <div className="glass-card" style={{ padding: '12px', textAlign: 'center', background: 'rgba(255,255,255,0.01)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auxiliary Space Complexity</span>
                    <h4 style={{ fontSize: '1.2rem', color: 'var(--accent-purple)', fontWeight: 700, marginTop: '4px' }}>
                      {runResult.space_complexity}
                    </h4>
                  </div>
                </div>
              )}

              {/* AI Feedback */}
              {runResult.feedback && (
                <div>
                  <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
                    💡 Sandbox Optimization Review
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                    {runResult.feedback}
                  </p>
                </div>
              )}

            </div>
          )}

        </div>

      </div>

    </div>
  );
};

export default CodingTest;
