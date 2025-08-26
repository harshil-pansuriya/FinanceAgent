import React, { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { analysisAPI, transactionAPI, authAPI } from '../../services/api';
import { parseAmount, formatCurrency } from '../../utils/helpers';
import Charts from './Charts';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const Insights = ({ refreshTrigger }) => {
    const { user } = useAuthContext();
    const [insights, setInsights] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedPeriod, setSelectedPeriod] = useState('this month');

    const fetchInsights = useCallback(async () => {
    if (!user?.user_id) return;

    setLoading(true);
    setError(null);

    try {
        // Always calculate basic metrics from frontend data
        
        // Fetch user data to get monthly income
        const userResponse = await authAPI.getUser(user.user_id);
        const monthlyIncome = parseFloat(userResponse.data.monthly_income) || 0;

        // Fetch transactions
        const transactionsResponse = await transactionAPI.getTransactions(user.user_id);
        const allTransactions = transactionsResponse.data || [];
        
        if (allTransactions.length === 0) {
            setInsights(null);
            return;
        }

        // Filter transactions based on selected period
        const now = new Date();
        const transactions = allTransactions.filter(transaction => {
            const transactionDate = new Date(transaction.transaction_date);
            
            switch (selectedPeriod) {
                case 'this month':
                    return transactionDate.getMonth() === now.getMonth() && 
                           transactionDate.getFullYear() === now.getFullYear();
                
                case 'last month':
                    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                    return transactionDate.getMonth() === lastMonth.getMonth() && 
                           transactionDate.getFullYear() === lastMonth.getFullYear();
                
                case 'last 3 months':
                    const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 2, 1);
                    const endOfCurrentMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                    return transactionDate >= threeMonthsAgo && transactionDate <= endOfCurrentMonth;
                
                default:
                    return transactionDate.getMonth() === now.getMonth() && 
                           transactionDate.getFullYear() === now.getFullYear();
            }
        });

        if (transactions.length === 0) {
            setInsights(null);
            return;
        }

        // Calculate basic metrics from current month transactions only
        const totalExpenses = transactions
            .reduce((sum, t) => {
                const amount = parseAmount(t.amount);
                return sum + amount;
            }, 0);

        // Calculate period-appropriate income
        let totalIncome = monthlyIncome;
        if (selectedPeriod === 'last 3 months') {
            totalIncome = monthlyIncome * 3; // 3 months of income
        }
        // For 'this month' and 'last month', use monthly income as is
        const netBalance = totalIncome - totalExpenses;
        
        // Group by category
        const categorySpending = {};
        transactions.forEach(t => {
            const category = t.category || 'Other';
            const amount = parseAmount(t.amount);
            categorySpending[category] = (categorySpending[category] || 0) + amount;
        });

        const categoryAnalysis = Object.entries(categorySpending)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([category, amount]) => ({
                category,
                amount
            }));

        // Try to get AI recommendations from backend
        let aiRecommendations = [];
        try {
            const aiResponse = await analysisAPI.getInsights(user.user_id, selectedPeriod);
            
            if (aiResponse.data && aiResponse.data.recommendations && Array.isArray(aiResponse.data.recommendations) && aiResponse.data.recommendations.length > 0) {
                aiRecommendations = aiResponse.data.recommendations;
            } else {
                aiRecommendations = [
                    {
                        title: "No AI Recommendations",
                        description: "Backend returned empty or invalid recommendations.",
                        impact: "Check backend response format"
                    }
                ];
            }
        } catch (aiError) {
            // Use fallback recommendations
            aiRecommendations = [
                {
                    title: "AI Analysis Unavailable",
                    description: "AI recommendations are currently unavailable. Please check your backend connection.",
                    impact: "Using basic calculation only"
                }
            ];
        }

        // Combine calculated metrics with AI recommendations
        const insightsData = {
            total_income: totalIncome,
            total_expenses: totalExpenses,
            net_balance: netBalance,
            transaction_count: transactions.length,
            category_analysis: categoryAnalysis,
            recommendations: aiRecommendations
        };
        
        setInsights(insightsData);
    } catch (err) {
        setError(err.response?.data?.message || 'Failed to load insights');
    } finally {
        setLoading(false);
    }
}, [user?.user_id, selectedPeriod, refreshTrigger]);

    useEffect(() => {
        fetchInsights();
    }, [fetchInsights]);

    const getProgressColor = (percentage) => {
        if (percentage >= 75) return 'success';
        if (percentage >= 50) return 'warning';
        return 'danger';
    };



    if (loading) return <Loader message="Analyzing your financial data..." />;
    if (error) return <ErrorMessage message={error} />;
    
    if (!insights) {
        const getPeriodText = () => {
            switch (selectedPeriod) {
                case 'this month': return 'this month';
                case 'last month': return 'last month';
                case 'last 3 months': return 'the last 3 months';
                default: return 'this period';
            }
        };

        return (
            <div className="insights">
                <div className="insights-header-small">
                    <div className="header-content-small">
                        <h4>📊 Financial Insights</h4>
                    </div>
                    <div className="insights-controls-small">
                        <select 
                            value={selectedPeriod} 
                            onChange={(e) => setSelectedPeriod(e.target.value)}
                            className="period-selector-small"
                        >
                            <option value="this month">This Month</option>
                            <option value="last month">Last Month</option>
                            <option value="last 3 months">Last 3 Months</option>
                        </select>
                        <button onClick={fetchInsights} className="refresh-button-small">
                            🔄 Refresh
                        </button>
                    </div>
                </div>
                
                <div className="no-insights">
                    <span className="no-insights-icon">📊</span>
                    <h4>No transaction data found</h4>
                    <p>No transactions found for {getPeriodText()}. Add some transactions to see your financial analysis!</p>
                </div>
            </div>
        );
    }

    return (
        <div className="insights">
            <div className="insights-header-small">
                <div className="header-content-small">
                    <h4>📊 Financial Insights</h4>
                </div>
                <div className="insights-controls-small">
                    <select 
                        value={selectedPeriod} 
                        onChange={(e) => setSelectedPeriod(e.target.value)}
                        className="period-selector-small"
                    >
                        <option value="this month">This Month</option>
                        <option value="last month">Last Month</option>
                        <option value="last 3 months">Last 3 Months</option>
                    </select>
                    <button onClick={fetchInsights} className="refresh-button-small">
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="metrics-section-small">
                <h5 className="section-title-small">Key Metrics</h5>
                <div className="metrics-grid-small">
                    <div className="metric-card-small">
                        <div className="metric-icon-small">💰</div>
                        <div className="metric-content-small">
                            <h6>Income</h6>
                            <p className="metric-value-small income">
                                {formatCurrency(insights.total_income)}
                            </p>
                        </div>
                    </div>

                    <div className="metric-card-small">
                        <div className="metric-icon-small">💸</div>
                        <div className="metric-content-small">
                            <h6>Expenses</h6>
                            <p className="metric-value-small expense">
                                {formatCurrency(insights.total_expenses)}
                            </p>
                        </div>
                    </div>

                    <div className="metric-card-small">
                        <div className="metric-icon-small">
                            {insights.net_balance >= 0 ? '📈' : '📉'}
                        </div>
                        <div className="metric-content-small">
                            <h6>Net Balance</h6>
                            <p className={`metric-value-small ${insights.net_balance >= 0 ? 'positive' : 'negative'}`}>
                                {formatCurrency(insights.net_balance)}
                            </p>
                        </div>
                    </div>

                    <div className="metric-card-small">
                        <div className="metric-icon-small">📊</div>
                        <div className="metric-content-small">
                            <h6>Transactions</h6>
                            <p className="metric-value-small">{insights.transaction_count}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Savings Progress */}
            {insights.savings_progress && (
                <div className="savings-progress">
                    <h4>Savings Goal Progress</h4>
                    <div className="progress-container">
                        <div className="progress-info">
                            <span className="progress-label">Current Savings</span>
                            <span className="progress-amount">
                                {formatCurrency(insights.savings_progress.current_savings)}
                            </span>
                        </div>
                        <div className="progress-bar">
                            <div 
                                className={`progress-fill ${getProgressColor(insights.savings_progress.progress_percentage)}`}
                                style={{ width: `${insights.savings_progress.progress_percentage}%` }}
                            ></div>
                        </div>
                        <div className="progress-details">
                            <span className="progress-percentage">
                                {insights.savings_progress.progress_percentage.toFixed(1)}%
                            </span>
                            <span className="progress-target">
                                Target: {formatCurrency(insights.savings_progress.target_amount)}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Category Analysis */}
            {insights.category_analysis && insights.category_analysis.length > 0 && (
                <div className="category-analysis-section-small">
                    <h5 className="section-title-small">🏷️ Top Categories</h5>
                    <div className="category-list-small">
                        {insights.category_analysis.slice(0, 5).map((category, index) => {
                            const percentage = ((category.amount / insights.total_expenses) * 100);
                            
                            return (
                                <div key={index} className="category-item-small">
                                    <div className="category-header-small">
                                        <span className="category-name-small">{category.category}</span>
                                        <span className="category-amount-small">
                                            {formatCurrency(category.amount)}
                                        </span>
                                    </div>
                                    <div className="category-bar-small">
                                        <div 
                                            className="category-fill-small"
                                            style={{ 
                                                width: `${percentage}%` 
                                            }}
                                        ></div>
                                    </div>
                                    <div className="category-percentage-small">
                                        {percentage.toFixed(1)}%
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Visual Analytics */}
            <div className="visual-analytics-section">
                <Charts insights={insights} />
            </div>

            {/* AI Recommendations */}
            {insights.recommendations && insights.recommendations.length > 0 && (
                <div className="recommendations-section-small">
                    <h5 className="section-title-small">💡 Recommendations</h5>
                    <div className="recommendations-list-small">
                        {insights.recommendations.slice(0, 3).map((rec, index) => (
                            <div key={index} className="recommendation-card-small">
                                <div className="recommendation-header-small">
                                    <span className="recommendation-icon-small">💡</span>
                                    <h6 className="recommendation-title-small">
                                        {rec.title || `${rec.category} Recommendation`}
                                    </h6>
                                    {rec.priority && (
                                        <span className={`priority-badge-small priority-${rec.priority}`}>
                                            {rec.priority.toUpperCase()}
                                        </span>
                                    )}
                                </div>
                                <p className="recommendation-description-small">
                                    {rec.description || rec.text}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Monthly Trends */}
            {insights.monthly_trends && (
                <div className="monthly-trends">
                    <h4>Monthly Trends</h4>
                    <div className="trends-grid">
                        <div className="trend-item">
                            <span className="trend-label">Average Monthly Income</span>
                            <span className="trend-value income">
                                {formatCurrency(insights.monthly_trends.avg_income)}
                            </span>
                        </div>
                        <div className="trend-item">
                            <span className="trend-label">Average Monthly Expenses</span>
                            <span className="trend-value expense">
                                {formatCurrency(insights.monthly_trends.avg_expenses)}
                            </span>
                        </div>
                        <div className="trend-item">
                            <span className="trend-label">Best Month</span>
                            <span className="trend-value">
                                {insights.monthly_trends.best_month}
                            </span>
                        </div>
                        <div className="trend-item">
                            <span className="trend-label">Highest Expense Month</span>
                            <span className="trend-value">
                                {insights.monthly_trends.highest_expense_month}
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Insights;