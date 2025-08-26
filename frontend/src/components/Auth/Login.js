import React, { useState } from 'react';
import { useAuth } from '../../hooks/userAuth';
import { useNavigate, Link } from 'react-router-dom';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const Login = () => {
    const [userId, setUserId] = useState('');
    const { login, loading, error } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
    e.preventDefault();
    try {
        await login({ user_id: userId });
        navigate('/dashboard');
    } catch (err) {
        console.error('Login failed:', err);
    }
    };

    if (loading) return <Loader />;

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2 className="auth-title">Welcome Back!</h2>
                    <p className="auth-subtitle">Enter your User ID to access your finance dashboard</p>
                </div>
        
                {error && <ErrorMessage message={error} />}
        
                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="user_id" className="form-label">User ID</label>
                        <input
                            type="text"
                            id="user_id"
                            className="form-input"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            required
                            maxLength="20"
                            placeholder="Enter your User ID"
                            autoComplete="username"
                        />
                    </div>

                    <button type="submit" className="auth-button" disabled={loading || !userId.trim()}>
                        Login
                    </button>
                </form>

                <div className="auth-footer">
                    <div className="auth-link">
                        Don't have an account? <Link to="/register">Create one here</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;