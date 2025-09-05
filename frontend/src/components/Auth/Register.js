import React, { useState } from 'react';
import { useAuth } from '../../hooks/userAuth';
import { useNavigate, Link } from 'react-router-dom';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const Register = () => {
    const [formData, setFormData] = useState({
        monthly_income: '',
        savings_goal: '',
        target_amount: '',
        target_date: ''
    });

    const { register, loading, error } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Prevent submission if target_date is in the past
        const todayStr = new Date().toISOString().split('T')[0];
        const isPastDate = formData.target_date && new Date(formData.target_date) < new Date(todayStr);
        if (isPastDate) {
            // Do not submit; UI already shows an error message conditionally
            return;
        }

        try {
            const userData = {
                monthly_income: parseFloat(formData.monthly_income),
                savings_goal: formData.savings_goal,
                target_amount: parseFloat(formData.target_amount),
                target_date: formData.target_date
            };

            await register(userData);
            navigate('/dashboard');
        } catch (err) {
            console.error('Registration failed:', err);
        }
    };

    if (loading) return <Loader />;

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2 className="auth-title">Create Your Profile</h2>
                    <p className="auth-subtitle">Set up your personal finance assistant</p>
                </div>
        
                {error && <ErrorMessage message={error} />}
        
                {/* Client-side validation for past target date */}
                {formData.target_date && new Date(formData.target_date) < new Date(new Date().toISOString().split('T')[0]) && (
                    <ErrorMessage message="Target date cannot be in the past" />
                )}
        
                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="monthly_income" className="form-label">Monthly Income ($)</label>
                        <input
                            type="number"
                            id="monthly_income"
                            name="monthly_income"
                            className="form-input"
                            value={formData.monthly_income}
                            onChange={handleChange}
                            step="100"
                            min="0"
                            required
                            placeholder="e.g., 5000"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="savings_goal" className="form-label">Savings Goal</label>
                        <textarea
                            id="savings_goal"
                            name="savings_goal"
                            className="form-input form-textarea"
                            value={formData.savings_goal}
                            onChange={handleChange}
                            required
                            minLength="5"
                            placeholder="e.g., Save for a house down payment"
                            rows="2"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="target_amount" className="form-label">Target Amount ($)</label>
                        <input
                            type="number"
                            id="target_amount"
                            name="target_amount"
                            className="form-input"
                            value={formData.target_amount}
                            onChange={handleChange}
                            step="100"
                            min="0"
                            required
                            placeholder="e.g., 10000"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="target_date" className="form-label">Target Date</label>
                        <input
                            type="date"
                            id="target_date"
                            name="target_date"
                            className="form-input"
                            value={formData.target_date}
                            onChange={handleChange}
                            required
                            min={new Date().toISOString().split('T')[0]}
                        />
                    </div>

                    <button type="submit" className="auth-button" disabled={loading}>
                        Create Profile
                    </button>
                </form>

                <div className="auth-footer">
                    <div className="auth-link">
                        Already have an account? <Link to="/login">Login here</Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;