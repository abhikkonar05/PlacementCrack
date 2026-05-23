import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  Brain, Mic, MicOff, Send, Award, History, ArrowRight, Loader2 
} from 'lucide-react';

interface InterviewSession {
  id: string;
  role: string;
  questions: string[];
  answers: string[];
  current_question_index: number;
  completed: boolean;
  score: number;
  feedback: string | null;
  date: string;
}

const InterviewRoom: React.FC = () => {
  const { token, apiUrl, refreshUser } = useAuth();
  
  const [role, setRole] = useState('Software Development');
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [grading, setGrading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<InterviewSession[]>([]);
  
  // Web Speech API states
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [micStatus, setMicStatus] = useState('Ready for voice input');
  const [interimTranscript, setInterimTranscript] = useState('');
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    fetchHistory();
    // Initialize Web Speech API if supported
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';
      
      rec.onresult = (event: any) => {
        let finalTranscript = '';
        let liveTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + ' ';
          } else {
            liveTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setCurrentAnswer(prev => `${prev}${finalTranscript}`);
        }
        setInterimTranscript(liveTranscript);
      };

      rec.onerror = (e: any) => {
        console.error("Speech recognition error:", e);
        const messageMap: Record<string, string> = {
          'not-allowed': 'Microphone permission was blocked. Allow microphone access from the browser address bar.',
          'audio-capture': 'No microphone was detected. Connect a mic and try again.',
          'network': 'Speech recognition service is unavailable. You can still type your answer.',
          'no-speech': 'No speech detected. Try again closer to the mic.',
          'aborted': 'Voice capture stopped.',
        };
        setMicStatus(messageMap[e.error] || 'Voice capture stopped. You can type your answer.');
        setIsRecording(false);
        setInterimTranscript('');
      };

      rec.onstart = () => {
        setMicStatus('Listening... speak clearly.');
      };

      rec.onend = () => {
        setIsRecording(false);
        setInterimTranscript('');
        setMicStatus('Voice capture stopped. Review or continue your answer.');
      };

      recognitionRef.current = rec;
    } else {
      setSpeechSupported(
        typeof navigator.mediaDevices?.getUserMedia === 'function' &&
        typeof window.MediaRecorder !== 'undefined'
      );
      setMicStatus('Browser live dictation is unavailable. Use recorded voice transcription or type your answer.');
    }
  }, []);

  const uploadRecordedAudio = async (audioBlob: Blob) => {
    if (!token) return;
    setMicStatus('Transcribing recorded answer with Hugging Face...');
    const formData = new FormData();
    formData.append('file', audioBlob, 'interview-answer.webm');

    try {
      const res = await fetch(`${apiUrl}/api/interview/transcribe`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to transcribe audio');
      }
      
      const data = await res.json();
      if (data.transcript) {
        setCurrentAnswer(prev => `${prev}${prev ? ' ' : ''}${data.transcript}`);
        setMicStatus('Voice answer transcribed. Review it before submitting.');
      } else {
        setMicStatus('Voice transcription failed. Type your answer instead.');
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Could not reach the transcription service';
      setMicStatus(`${errorMsg}. Type your answer instead.`);
    }
  };

  const fetchHistory = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiUrl}/api/interview/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) {
        throw new Error(`Failed to fetch history: ${res.statusText}`);
      }
      
      const data = await res.json();
      setHistory(data.filter((s: any) => s.completed));
    } catch (e) {
      console.error("Failed to load interview history:", e);
    }
  };

  const handleStartInterview = async () => {
    if (!token) return;
    setLoading(true);
    setSession(null);
    setError('');
    try {
      const res = await fetch(`${apiUrl}/api/interview/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ role })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to start interview');
      }
      
      const data = await res.json();
      setSession(data);
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Failed to start interview. Check your connection.";
      setError(errorMsg);
      console.error("Error starting interview:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRecord = async () => {
    if (!recognitionRef.current) {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setSpeechSupported(false);
        setMicStatus("Voice capture is not supported by this browser. Please type your answer or use Chrome.");
        return;
      }

      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = recorder;
        recorder.ondataavailable = event => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };
        recorder.onstop = () => {
          stream.getTracks().forEach(track => track.stop());
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          if (audioBlob.size > 0) {
            uploadRecordedAudio(audioBlob);
          } else {
            setMicStatus('No voice was captured. Try again or type your answer.');
          }
        };
        recorder.start();
        setIsRecording(true);
        setMicStatus('Recording voice answer... click Stop Listening when done.');
      } catch (e) {
        setIsRecording(false);
        setMicStatus('Microphone permission is blocked or unavailable. Allow mic access, then try again.');
      }
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      try {
        if (navigator.mediaDevices?.getUserMedia) {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach(track => track.stop());
        }
        setInterimTranscript('');
        setIsRecording(true);
        setMicStatus('Starting microphone...');
        recognitionRef.current.start();
      } catch (e) {
        setIsRecording(false);
        setMicStatus('Microphone permission is blocked or unavailable. Allow mic access, then try again.');
      }
    }
  };

  const handleSubmitAnswer = async () => {
    if (!session || !token) {
      setError('Missing session or authentication token');
      return;
    }
    
    // Stop recording if active
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    const isLastQuestion = session.current_question_index === session.questions.length - 1;
    if (isLastQuestion) {
      setGrading(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      const res = await fetch(`${apiUrl}/api/interview/submit-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          interview_id: session.id,
          question_index: session.current_question_index,
          answer: currentAnswer || "Candidate bypassed or gave no verbal answer."
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to submit answer');
      }
      
      const data = await res.json();
      setSession(data);
      setCurrentAnswer('');
      
      if (data.completed) {
        fetchHistory();
        refreshUser(); // update score
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Error submitting answer. Check your connection.";
      setError(errorMsg);
      console.error("Error submitting answer:", e);
    } finally {
      setLoading(false);
      setGrading(false);
    }
  };

  const parseDetailedFeedback = (feedbackStr: string | null) => {
    if (!feedbackStr) return [];
    
    // Split the custom structured text response
    const lines = feedbackStr.split('\n');
    const evaluations: any[] = [];
    
    let currentItem: any = null;
    
    for (const line of lines) {
      if (line.startsWith('Q') && line.includes(':')) {
        if (currentItem) evaluations.push(currentItem);
        currentItem = {
          number: line.split(':')[0],
          question: line.substring(line.indexOf(':') + 1).trim(),
          answer: '',
          score: '',
          feedback: ''
        };
      } else if (line.startsWith('Candidate:')) {
        if (currentItem) currentItem.answer = line.replace('Candidate:', '').trim();
      } else if (line.startsWith('Score:')) {
        if (currentItem) currentItem.score = line.replace('Score:', '').trim();
      } else if (line.startsWith('Feedback:')) {
        if (currentItem) currentItem.feedback = line.replace('Feedback:', '').trim();
      } else if (currentItem && line.trim() !== '') {
        // Append additional feedback lines if present
        currentItem.feedback += ' ' + line.trim();
      }
    }
    if (currentItem) evaluations.push(currentItem);
    return evaluations;
  };

  return (
    <div style={{ padding: '0 40px 40px 40px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <h1 className="glow-text" style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '4px' }}>
          AI Mock Interview Room
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Practice technical and behavioural interviews. Answers are evaluated dynamically by our AI model.
        </p>
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

      {/* Grading pulse loader */}
      {grading && (
        <div className="glass-card animate-pulse-glow" style={{
          padding: '60px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
          marginTop: '40px'
        }}>
          <Loader2 size={48} className="animate-spin" style={{ color: 'var(--accent-violet)' }} />
          <div>
            <h2 className="glow-text" style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '8px' }}>
              Generating AI Analytical Feedback...
            </h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '450px', fontSize: '0.9rem', lineHeight: '1.5' }}>
              The AI Evaluator is analyzing your response length, keywords, grammatical flow, and subject matter expertise. This may take up to 15 seconds.
            </p>
          </div>
        </div>
      )}

      {/* Active Question Simulator Room */}
      {!grading && session && !session.completed && (
        <div className="glass-card fade-in" style={{
          border: '1px solid var(--border-glow)',
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(0, 0, 0, 0) 100%)',
          minHeight: '480px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          marginTop: '20px'
        }}>
          {/* Header Progress indicator */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', fontWeight: 700, textTransform: 'uppercase' }}>
              {session.role} Interview
            </span>
            <span style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              background: 'rgba(255,255,255,0.04)',
              padding: '4px 10px',
              borderRadius: '99px'
            }}>
              Question {session.current_question_index + 1} of {session.questions.length}
            </span>
          </div>

          {/* Core Interview Question card */}
          <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start', margin: '30px 0' }}>
            <div style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              background: 'var(--glass-gradient)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              border: '1px solid var(--border-glow)',
              flexShrink: 0
            }}>
              <Brain size={20} color="var(--accent-purple)" />
            </div>
            
            <div style={{ flexGrow: 1 }}>
              <p style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.25rem',
                fontWeight: 600,
                color: 'white',
                lineHeight: '1.5'
              }}>
                {session.questions[session.current_question_index]}
              </p>
            </div>
          </div>

          {/* Answer Inputs Box */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <label style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              Your Response
            </label>
            
            <div style={{ position: 'relative' }}>
              <textarea
                value={currentAnswer}
                onChange={e => setCurrentAnswer(e.target.value)}
                placeholder="Type your response here, or click the mic button below to dictate..."
                style={{
                  width: '100%',
                  height: '150px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '12px',
                  padding: '20px',
                  color: 'white',
                  fontSize: '0.95rem',
                  outline: 'none',
                  resize: 'none',
                  fontFamily: 'var(--font-body)',
                  lineHeight: '1.6'
                }}
                  />
              
              {/* Dictation Indicator status tag */}
              {(isRecording || micStatus) && (
                <div style={{
                  position: 'absolute',
                  bottom: '15px',
                  left: '20px',
                  right: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.75rem',
                  color: isRecording ? 'var(--error)' : 'var(--text-muted)'
                }}>
                  {isRecording && (
                    <span style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: 'var(--error)',
                      borderRadius: '50%',
                      display: 'inline-block',
                      animation: 'pulseGlow 1.5s infinite',
                      flexShrink: 0
                    }} />
                  )}
                  <span>{interimTranscript ? `Heard: ${interimTranscript}` : micStatus}</span>
                </div>
              )}
            </div>

            {/* Actions Panel */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                type="button"
                onClick={handleToggleRecord}
                disabled={!speechSupported}
                className={isRecording ? 'btn-primary' : 'btn-secondary'}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 20px',
                  borderRadius: '10px',
                  background: isRecording ? 'linear-gradient(135deg, var(--error) 0%, #fda4af 100%)' : undefined,
                  boxShadow: isRecording ? '0 4px 15px rgba(244, 63, 94, 0.3)' : undefined
                }}
              >
                {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
                <span>{isRecording ? 'Stop Listening' : 'Start Speaking'}</span>
              </button>

              <button
                onClick={handleSubmitAnswer}
                disabled={loading}
                className="btn-primary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 24px',
                  borderRadius: '10px'
                }}
              >
                <span>{loading ? 'Submitting...' : 'Submit Answer'}</span>
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Completed Session Analytical scorecard screen */}
      {!grading && session && session.completed && (
        <div className="glass-card fade-in" style={{ marginTop: '20px' }}>
          
          {/* Card header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', fontWeight: 700, textTransform: 'uppercase' }}>
                AI Analysis Report
              </span>
              <h2 className="glow-text" style={{ fontSize: '1.6rem', fontWeight: 800 }}>Interview Scorecard</h2>
            </div>
            
            <button 
              className="btn-secondary" 
              onClick={() => setSession(null)}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              Take Another Interview
            </button>
          </div>

          <hr style={{ borderColor: 'var(--border-light)', marginBottom: '24px' }} />

          {/* Average metrics card */}
          <div className="glass-card-glow" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '24px 30px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(0, 0, 0, 0) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            marginBottom: '30px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                backgroundColor: 'var(--success-glow)',
                padding: '12px',
                borderRadius: '50%',
                color: 'var(--success)',
                border: '1px solid var(--success)'
              }}>
                <Award size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white' }}>Average Score</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Based on technical evaluation metrics.</p>
              </div>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--success)' }}>
              {session.score.toFixed(1)}<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/100</span>
            </div>
          </div>

          {/* Conversation Transcript Timeline */}
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>Interview Question Breakdown</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {parseDetailedFeedback(session.feedback).map((item: any, idx: number) => (
              <div key={idx} className="glass-card" style={{
                padding: '20px',
                background: 'rgba(255,255,255,0.01)',
                borderLeft: `3px solid var(--accent-violet)`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'white' }}>{item.number}: {item.question}</h4>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--success)' }}>Score: {item.score}</span>
                </div>
                
                <div style={{ marginBottom: '12px' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                    Your Answer
                  </span>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: '1.5' }}>
                    "{item.answer}"
                  </p>
                </div>

                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                    AI Feedback Review
                  </span>
                  <p style={{ fontSize: '0.85rem', color: '#a78bfa', lineHeight: '1.5' }}>
                    {item.feedback}
                  </p>
                </div>
              </div>
            ))}
          </div>

        </div>
      )}

      {/* Start Setup Config Screen */}
      {!session && !grading && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '30px', marginTop: '20px' }}>
          
          {/* Start Card */}
          <div className="glass-card" style={{ padding: '35px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Brain size={22} color="var(--accent-purple)" />
              Setup Mock Session
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '30px' }}>
              <div>
                <label className="input-label">Select Candidate Role Profile</label>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                  marginTop: '8px'
                }}>
                  {['Software Development', 'Data Science', 'AI/ML'].map(r => (
                    <button
                      key={r}
                      onClick={() => setRole(r)}
                      className={role === r ? 'btn-primary' : 'btn-secondary'}
                      style={{ padding: '14px 10px', fontSize: '0.85rem', borderRadius: '10px' }}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button 
              className="btn-primary" 
              onClick={handleStartInterview}
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                fontSize: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <span>{loading ? 'Initializing Session...' : 'Start AI Interview Session'}</span>
              <ArrowRight size={18} />
            </button>
          </div>

          {/* History Card */}
          <div className="glass-card" style={{ padding: '24px', maxHeight: '420px', overflowY: 'auto' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={18} color="var(--accent-purple)" />
              Interview Logs
            </h3>
            
            {history.length === 0 ? (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No completed interviews.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {history.map(item => (
                  <div 
                    key={item.id}
                    onClick={() => setSession(item)}
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
                      <span style={{ color: 'white' }}>{item.role}</span>
                      <span style={{ color: 'var(--success)' }}>{item.score.toFixed(1)}/100</span>
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
      )}

      <style>{`
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
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

export default InterviewRoom;
