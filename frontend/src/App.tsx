import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Shared/Navbar';
import AuthPage from './components/Auth/AuthPage';
import Dashboard from './components/Dashboard/Dashboard';
import CodingTest from './components/CodingTest/CodingTest';
import InterviewRoom from './components/Interview/InterviewRoom';
import ResumeChecker from './components/ResumeChecker/ResumeChecker';
import JobFinder from './components/JobFinder/JobFinder';
import SoftwareDevelopment from './components/Dashboard/SoftwareDevelopment';
import AptitudeTest from './components/Dashboard/AptitudeTest';
import MockInterviewPrep from './components/Dashboard/MockInterviewPrep';
import OpportunitiesList from './components/Dashboard/OpportunitiesList';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'var(--bg-main)',
        color: 'var(--text-secondary)',
        fontSize: '1rem',
        fontFamily: 'var(--font-heading)'
      }}>
        Initializing PlacementCrack secure gateway...
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <Router>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/coding" element={<CodingTest />} />
            <Route path="/interview" element={<InterviewRoom />} />
            <Route path="/resume" element={<ResumeChecker />} />
            <Route path="/jobs" element={<JobFinder />} />
            <Route path="/software-development" element={<SoftwareDevelopment />} />
            <Route path="/aptitude" element={<AptitudeTest />} />
            <Route path="/interview-prep" element={<MockInterviewPrep />} />
            <Route path="/opportunities" element={<OpportunitiesList />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
