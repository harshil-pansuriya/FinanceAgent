import React, { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { authAPI, transactionAPI } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/helpers';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const Overview = ({ refreshTrigger, onNavigateToInsights }) => {
    const { user } = useAuthContext();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [userData, setUserData] = useState(null);
    const [transactions, setTransactions] = useState([]);
    const [financialSummary, setFinancialSummary] = useState({
        totalIncome: 0,
        totalExpenses: 0,
        netBalance: 0,
        savingsProgress: 0
    });

    const fetchOverviewData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch user data and transactions in parallel
            const [userResponse, transactionsResponse] = await Promise.allSettled([
                authAPI.getUser(user.user_id),
                transactionAPI.getTransactions(user.user_id)
            ]);

            // Handle user data
            if (userResponse.status === 'fulfilled') {
                setUserData(userResponse.value.data);
            }

            // Handle transactions
            if (transactionsResponse.status === 'fulfilled') {
                const transactionData = transactionsResponse.value.data;
                setTransactions(transactionData);
                calculateFinancialSummary(transactionData, userResponse.value?.data);
            }

        } catch (err) {
            setError('Failed to load overview data. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [user]);

    useEffect(() => {
        if (user?.user_id) {
            fetchOverviewData();
        }
    }, [user, refreshTrigger, fetchOverviewData]);

    const calculateFinancialSummary = (transactionData, userData) => {
        if (!transactionData || transactionData.length === 0) {
            setFinancialSummary({
                totalIncome: 0,
                totalExpenses: 0,
                netBalance: 0,
                savingsProgress: 0
            });
            return;
        }

        // Use monthly income from user data
        const monthlyIncome = parseFloat(userData?.monthly_income) || 0;
        
        // Get current month and year for filtering
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        
        // Filter transactions for current month only
        const currentMonthTransactions = transactionData.filter(transaction => {
            const transactionDate = new Date(transaction.transaction_date);
            return transactionDate.getMonth() === currentMonth && 
                   transactionDate.getFullYear() === currentYear;
        });
        
        // Calculate total expenses from current month transactions only
        const totalExpenses = currentMonthTransactions.reduce((sum, transaction) => {
            const amount = parseFloat(transaction.amount);
            if (!isNaN(amount)) {
                return sum + amount; // This includes both positive and negative amounts
            }
            return sum;
        }, 0);

        // Since expenses are stored as negative values, totalExpenses will be negative
        // We need the absolute value for display
        const absoluteExpenses = Math.abs(totalExpenses);
        
        const totalIncome = monthlyIncome;
        const netBalance = totalIncome - absoluteExpenses;
        
        // Calculate savings progress if user data is available
        let savingsProgress = 0;
        if (userData && userData.target_amount) {
            const targetAmount = parseFloat(userData.target_amount);
            savingsProgress = targetAmount > 0 ? (netBalance / targetAmount) * 100 : 0;
        }

        setFinancialSummary({
            totalIncome,
            totalExpenses: absoluteExpenses,
            netBalance,
            savingsProgress: Math.max(0, Math.min(100, savingsProgress))
        });
    };





    const getDaysUntilTarget = () => {
        if (!userData?.target_date) return null;
        const targetDate = new Date(userData.target_date);
        const today = new Date();
        const diffTime = targetDate - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    };

    if (loading) {
        return <Loader message="Loading overview..." />;
    }

    if (error) {
        return <ErrorMessage message={error} onClose={() => setError(null)} />;
    }

    const daysUntilTarget = getDaysUntilTarget();

    return (
        <div className="overview">
            {/* Financial Summary Cards */}
            <div className="dashboard-grid">
                {/* Monthly Income Card */}
                <div className="dashboard-card">
                    <div className="card-header">
                        <div className="card-icon">💰</div>
                        <h3 className="card-title">Monthly Income</h3>
                    </div>
                    <div className="card-value positive">
                        {formatCurrency(financialSummary.totalIncome)}
                    </div>
                    <p className="card-description">
                        Total income this month
                    </p>
                    {userData?.monthly_income && (
                        <div className="card-trend">
                            <span className="trend-icon">📊</span>
                            <span className="trend-text">
                                Target: {formatCurrency(userData.monthly_income)}
                            </span>
                        </div>
                    )}
                </div>

                {/* Monthly Expenses Card */}
                <div className="dashboard-card">
                    <div className="card-header">
                        <div className="card-icon">💸</div>
                        <h3 className="card-title">Monthly Expenses</h3>
                    </div>
                    <div className="card-value negative">
                        {formatCurrency(financialSummary.totalExpenses)}
                    </div>
                    <p className="card-description">
                        Total expenses this month
                    </p>
                    <div className="card-trend">
                        <span className="trend-icon">📈</span>
                        <span className="trend-text">
                            {transactions.length} transactions
                        </span>
                    </div>
                </div>

                {/* Net Balance Card */}
                <div className="dashboard-card">
                    <div className="card-header">
                        <div className="card-icon">⚖️</div>
                        <h3 className="card-title">Net Balance</h3>
                    </div>
                    <div className={`card-value ${financialSummary.netBalance >= 0 ? 'positive' : 'negative'}`}>
                        {formatCurrency(financialSummary.netBalance)}
                    </div>
                    <p className="card-description">
                        Remaining Balance this month
                    </p>
                    <div className="card-trend">
                        <span className={`trend-icon ${financialSummary.netBalance >= 0 ? 'trend-up' : 'trend-down'}`}>
                            {financialSummary.netBalance >= 0 ? '📈' : '📉'}
                        </span>
                        <span className="trend-text">
                            {financialSummary.netBalance >= 0 ? 'Surplus' : 'Deficit'}
                        </span>
                    </div>
                </div>

                {/* Savings Goal Card */}
                {userData && (
                    <div className="dashboard-card">
                        <div className="card-header">
                            <div className="card-icon">🎯</div>
                            <h3 className="card-title">Savings Goal</h3>
                        </div>
                        <div className="card-value neutral">
                            {formatCurrency(userData.target_amount)}
                        </div>
                        <p className="card-description">
                            {userData.savings_goal}
                        </p>
                        <div className="card-trend">
                            <span className="trend-icon">📅</span>
                            <span className="trend-text">
                                {daysUntilTarget !== null ? (
                                    daysUntilTarget > 0 ? 
                                        `${daysUntilTarget} days remaining` : 
                                        'Target date passed'
                                ) : 'No target date set'}
                            </span>
                        </div>
                        {/* Progress Bar */}
                        <div className="progress-container">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill"
                                    style={{ width: `${Math.min(100, financialSummary.savingsProgress)}%` }}
                                ></div>
                            </div>
                            <span className="progress-text">
                                {financialSummary.savingsProgress.toFixed(1)}% achieved
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Target Date Information */}
            {userData?.target_date && (
                <div className="target-info-card">
                    <div className="target-info-header">
                        <h3>🎯 Target Information</h3>
                    </div>
                    <div className="target-info-content">
                        <div className="target-info-item">
                            <span className="target-label">Target Date:</span>
                            <span className="target-value">{formatDate(userData.target_date)}</span>
                        </div>
                        <div className="target-info-item">
                            <span className="target-label">Target Amount:</span>
                            <span className="target-value">{formatCurrency(userData.target_amount)}</span>
                        </div>
                        <div className="target-info-item">
                            <span className="target-label">Goal:</span>
                            <span className="target-value">{userData.savings_goal}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Detailed Analysis Button */}
            <div className="detailed-analysis-section-small">
                <div className="analysis-card-small">
                    <div className="analysis-content-small">
                        <h5>View Detailed Analysis</h5>
                        <p>Get insights and recommendations</p>
                    </div>
                    <button 
                        className="detailed-analysis-btn-small"
                        onClick={() => onNavigateToInsights && onNavigateToInsights()}
                    >
                        <span className="btn-icon">📈</span>
                        View Analysis
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Overview;