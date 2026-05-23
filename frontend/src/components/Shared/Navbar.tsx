import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Trophy, Award, BookOpen, MessageSquare, FileText, Briefcase, User as UserIcon } from 'lucide-react';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const isActive = (path: string) => {
    return location.pathname === path ? 'active-nav-link' : '';
  };

  return (
    <nav className="glass-card" style={{
      borderRadius: '0 0 16px 16px',
      margin: '0 0 24px 0',
      padding: '16px 40px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderTop: 'none',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }} onClick={() => navigate('/')}>
        <div style={{
          background: 'linear-gradient(135deg, var(--accent-violet) 0%, var(--accent-magenta) 100%)',
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontWeight: 'bold',
          color: 'white',
          fontSize: '1.2rem',
          boxShadow: '0 0 10px rgba(139, 92, 246, 0.4)'
        }}>
          P
        </div>
        <span className="glow-text" style={{
          fontFamily: 'var(--font-heading)',
          fontWeight: 800,
          fontSize: '1.4rem',
          letterSpacing: '-0.03em',
          background: 'linear-gradient(to right, #ffffff, var(--accent-purple))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          PlacementCrack
        </span>
      </div>

      <div style={{ display: 'flex', gap: '30px', alignItems: 'center' }}>
        <Link to="/" className={`nav-link ${isActive('/')}`}>
          <BookOpen size={16} />
          Dashboard
        </Link>
        <Link to="/coding" className={`nav-link ${isActive('/coding')}`}>
          <Trophy size={16} />
          Coding Test
        </Link>
        <Link to="/interview" className={`nav-link ${isActive('/interview')}`}>
          <MessageSquare size={16} />
          Mock Interview
        </Link>
        <Link to="/resume" className={`nav-link ${isActive('/resume')}`}>
          <FileText size={16} />
          ATS Checker
        </Link>
        <Link to="/jobs" className={`nav-link ${isActive('/jobs')}`}>
          <Briefcase size={16} />
          Job Finder
        </Link>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* User profile score representation */}
        <div className="glass-card-glow" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '99px',
          boxShadow: 'none',
          border: '1px solid rgba(139, 92, 246, 0.3)'
        }}>
          <Award size={16} color="var(--success)" />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Score:</span>
          <span style={{ fontWeight: 'bold', color: 'var(--success)', fontSize: '0.95rem' }}>
            {user.profile_score?.toFixed(1) || '0.0'}
          </span>
        </div>

        {/* User name display */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            border: '1px solid var(--border-light)'
          }}>
            <UserIcon size={14} color="var(--text-secondary)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {user.name}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {user.university}
            </span>
          </div>
        </div>

        <button 
          onClick={logout} 
          className="btn-secondary" 
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.85rem'
          }}
        >
          <LogOut size={14} />
          Exit
        </button>
      </div>

      <style>{`
        .nav-link {
          color: var(--text-secondary);
          text-decoration: none;
          font-family: var(--font-heading);
          font-size: 0.95rem;
          font-weight: 500;
          display: flex;
          alignItems: center;
          gap: 6px;
          transition: all 0.2s ease;
          padding: 6px 12px;
          border-radius: 8px;
        }
        .nav-link:hover {
          color: var(--text-primary);
          background: rgba(255, 255, 255, 0.03);
        }
        .active-nav-link {
          color: var(--accent-violet) !important;
          background: rgba(139, 92, 246, 0.08) !important;
          font-weight: 600;
        }
      `}</style>
    </nav>
  );
};

export default Navbar;
