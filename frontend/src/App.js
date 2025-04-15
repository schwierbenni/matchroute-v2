import React from 'react';
import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom';
import LoginPage from './components/LoginForm/LoginForm';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import NavBar from './components/NavBar/NavBar';
import RoutePlanPage from './pages/RoutePlanPage';

const App = () => {
  const isLoggedIn = () => !!localStorage.getItem('access_token');

  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to={isLoggedIn() ? "/dashboard" : "/login"} />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={isLoggedIn() ? <DashboardPage /> : <Navigate to="/login" />} />
        <Route path="/routenplanung" element={isLoggedIn() ? <RoutePlanPage /> : <Navigate to="/login" />} />
      </Routes>
    </Router>
  );
};

export default App;