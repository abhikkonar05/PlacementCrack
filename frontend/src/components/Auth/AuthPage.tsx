import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Mail, Lock, User, ShieldCheck, ArrowRight, Activity, Timer } from 'lucide-react';

const AuthPage: React.FC = () => {
  const { login, apiUrl } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form Registration States
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // OTP Verification States
  const [showOtpField, setShowOtpField] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [resendTimer, setResendTimer] = useState(60);
  const [isResendDisabled, setIsResendDisabled] = useState(true);

  // MFA Login Key States
  const [showLoginKeyField, setShowLoginKeyField] = useState(false);
  const [loginKey, setLoginKey] = useState('');

  // Countdown timer effect for OTP resend
  useEffect(() => {
    let interval: any;
    if (showOtpField && resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => prev - 1);
      }, 1000);
    } else if (resendTimer === 0) {
      setIsResendDisabled(false);
    }
    return () => clearInterval(interval);
  }, [showOtpField, resendTimer]);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName || !lastName || !email || !password || !confirmPassword) {
      setError('Please fill in all registration fields first.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await fetch(`${apiUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          confirm_password: confirmPassword
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        setShowOtpField(true);
        setResendTimer(60);
        setIsResendDisabled(true);
        setSuccessMsg('Account request created! Check email for the 6-digit OTP code.');
      } else {
        setError(data.detail || 'Failed to register. Email may be already registered.');
      }
    } catch (e) {
      setError('Connection to backend failed. Make sure FastAPI backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${apiUrl}/api/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: otpCode })
      });
      const data = await res.json();
      
      if (res.ok) {
        setSuccessMsg('Email verified successfully! Redirecting you to Login...');
        setTimeout(() => {
          setIsLogin(true);
          setShowOtpField(false);
          setOtpCode('');
          setPassword('');
          setConfirmPassword('');
          setSuccessMsg('Verification successful. Please sign in now!');
        }, 1500);
      } else {
        setError(data.detail || 'Invalid or expired OTP code.');
      }
    } catch (e) {
      setError('Verification request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError('');
    setSuccessMsg('');
    setResendTimer(60);
    setIsResendDisabled(true);

    try {
      const res = await fetch(`${apiUrl}/api/auth/resend-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg('A new verification code has been dispatched to your email.');
      } else {
        setError(data.detail || 'Failed to resend OTP.');
        setIsResendDisabled(false);
        setResendTimer(0);
      }
    } catch (e) {
      setError('Network error. Failed to resend code.');
      setIsResendDisabled(false);
      setResendTimer(0);
    }
  };

  const handleInitiateLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      
      if (res.ok) {
        if (data.key_sent) {
          setShowLoginKeyField(true);
          setSuccessMsg('Step 1 Complete! A secure Login Key was sent to your email.');
        }
      } else {
        setError(data.detail || 'Invalid email address or password.');
      }
    } catch (e) {
      setError('Backend connection failed. Is the server running?');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyLoginKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginKey) {
      setError('Please enter your unique login key.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, login_key: loginKey })
      });
      const data = await res.json();
      
      if (res.ok) {
        login(data.access_token, data.user);
      } else {
        setError(data.detail || 'Invalid or expired secure login key.');
      }
    } catch (e) {
      setError('Network request failed during MFA verification.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '90vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px'
    }}>
      <div className="glass-card fade-in" style={{
        width: '100%',
        maxWidth: '480px',
        padding: '40px',
        border: '1px solid var(--border-glow)',
        boxShadow: 'var(--shadow-glow)'
      }}>
        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--accent-violet) 0%, var(--accent-magenta) 100%)',
            width: '50px',
            height: '50px',
            borderRadius: '12px',
            display: 'inline-flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontWeight: 'bold',
            color: 'white',
            fontSize: '1.6rem',
            boxShadow: '0 4px 15px rgba(139, 92, 246, 0.4)',
            marginBottom: '12px'
          }}>
            P
          </div>
          <h2 className="glow-text" style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '6px' }}>
            {isLogin ? (showLoginKeyField ? 'MFA Verification' : 'Welcome Back') : (showOtpField ? 'Email Verification' : 'Get Placement Ready')}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {isLogin 
              ? (showLoginKeyField ? 'Confirm the secure key sent to your inbox' : 'Enter details to access your dashboard') 
              : (showOtpField ? `Enter the 6-digit OTP code sent to ${email}` : 'Create a secure account to begin mock tests')}
          </p>
        </div>

        {error && (
          <div style={{
            backgroundColor: 'var(--error-glow)',
            border: '1px solid var(--error)',
            color: 'var(--text-primary)',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '20px',
            lineHeight: '1.4'
          }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{
            backgroundColor: 'var(--success-glow)',
            border: '1px solid var(--success)',
            color: 'var(--success)',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '20px'
          }}>
            {successMsg}
          </div>
        )}


        {/* Form elements */}
        <form onSubmit={
          isLogin 
            ? (showLoginKeyField ? handleVerifyLoginKey : handleInitiateLogin)
            : (showOtpField ? handleVerifyOtp : handleSendOtp)
        }>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            {/* REGISTER FIELDS */}
            {!isLogin && !showOtpField && (
              <>
                <div style={{ display: 'flex', gap: '16px' }}>
                  {/* First Name */}
                  <div style={{ flex: 1 }}>
                    <label className="input-label">First Name</label>
                    <div className="input-wrapper">
                      <User size={18} className="input-icon" />
                      <input 
                        type="text" 
                        placeholder="Abhik" 
                        value={firstName} 
                        onChange={e => setFirstName(e.target.value)} 
                        required 
                      />
                    </div>
                  </div>

                  {/* Last Name */}
                  <div style={{ flex: 1 }}>
                    <label className="input-label">Last Name</label>
                    <div className="input-wrapper">
                      <User size={18} className="input-icon" />
                      <input 
                        type="text" 
                        placeholder="Konar" 
                        value={lastName} 
                        onChange={e => setLastName(e.target.value)} 
                        required 
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* EMAIL (Only visible if not verifying OTP/Key or if logging in initially) */}
            {((!showOtpField && !showLoginKeyField) || isLogin) && (
              <div>
                <label className="input-label">Email Address</label>
                <div className="input-wrapper">
                  <Mail size={18} className="input-icon" />
                  <input 
                    type="email" 
                    placeholder="name@email.com" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    required 
                    disabled={showLoginKeyField}
                  />
                </div>
              </div>
            )}

            {/* PASSWORD (Only visible if not verifying OTP/Key) */}
            {!showOtpField && !showLoginKeyField && (
              <div>
                <label className="input-label">Password</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input 
                    type="password" 
                    placeholder="••••••••" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    required 
                  />
                </div>
              </div>
            )}

            {/* CONFIRM PASSWORD (Only visible in Register) */}
            {!isLogin && !showOtpField && (
              <div>
                <label className="input-label">Confirm Password</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input 
                    type="password" 
                    placeholder="••••••••" 
                    value={confirmPassword} 
                    onChange={e => setConfirmPassword(e.target.value)} 
                    required 
                  />
                </div>
              </div>
            )}

            {/* OTP VERIFICATION VIEW */}
            {!isLogin && showOtpField && (
              <>
                <div>
                  <label className="input-label" style={{ color: 'var(--success)' }}>Enter Verification OTP</label>
                  <div className="input-wrapper" style={{ borderColor: 'var(--success)' }}>
                    <ShieldCheck size={18} className="input-icon" style={{ color: 'var(--success)' }} />
                    <input 
                      type="text" 
                      placeholder="6-digit code" 
                      value={otpCode} 
                      onChange={e => setOtpCode(e.target.value)} 
                      maxLength={6}
                      required 
                    />
                  </div>
                </div>

                {/* Countdown & Resend Option */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <Timer size={14} />
                    <span>
                      {resendTimer > 0 ? `Resend code in ${resendTimer}s` : 'You can now resend'}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={isResendDisabled}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: isResendDisabled ? 'var(--text-muted)' : 'var(--accent-purple)',
                      fontWeight: 600,
                      cursor: isResendDisabled ? 'not-allowed' : 'pointer',
                      fontSize: '0.8rem'
                    }}
                  >
                    Resend OTP
                  </button>
                </div>
              </>
            )}

            {/* LOGIN KEY MFA VERIFICATION VIEW */}
            {isLogin && showLoginKeyField && (
              <>
                <div>
                  <label className="input-label" style={{ color: '#10b981' }}>Enter Secure Login Key</label>
                  <div className="input-wrapper" style={{ borderColor: '#10b981' }}>
                    <ShieldCheck size={18} className="input-icon" style={{ color: '#10b981' }} />
                    <input 
                      type="text" 
                      placeholder="Format: X1234" 
                      value={loginKey} 
                      onChange={e => setLoginKey(e.target.value.toUpperCase())} 
                      maxLength={5}
                      required 
                    />
                  </div>
                </div>
                <div style={{ textAlign: 'right', marginTop: '-4px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowLoginKeyField(false);
                      setLoginKey('');
                      setSuccessMsg('');
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      textDecoration: 'underline'
                    }}
                  >
                    Back to password login
                  </button>
                </div>
              </>
            )}

            {/* SUBMIT BUTTON */}
            <button 
              type="submit" 
              className="btn-primary" 
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '8px',
                marginTop: '10px'
              }}
              disabled={loading}
            >
              {loading ? (
                <span>Processing...</span>
              ) : isLogin ? (
                showLoginKeyField ? (
                  <>
                    <span>Verify & Sign In</span>
                    <ArrowRight size={18} />
                  </>
                ) : (
                  <>
                    <span>Request Login Key</span>
                    <Activity size={18} />
                  </>
                )
              ) : showOtpField ? (
                <>
                  <span>Verify Email</span>
                  <ArrowRight size={18} />
                </>
              ) : (
                <>
                  <span>Register Account</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </form>

        {/* SWITCH TABS (Login / Register Toggle) */}
        {(!showOtpField && !showLoginKeyField) && (
          <div style={{ textAlign: 'center', marginTop: '24px' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              {isLogin ? "Don't have an account? " : "Already have an account? "}
            </span>
            <button 
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setSuccessMsg('');
                setFirstName('');
                setLastName('');
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--accent-purple)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              {isLogin ? 'Register now' : 'Sign In'}
            </button>
          </div>
        )}
      </div>

      </div>
  );
};

export default AuthPage;

