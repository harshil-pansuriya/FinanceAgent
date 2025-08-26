import React, { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { transactionAPI, authAPI } from '../../services/api';
import { formatDate, getCategoryIcon } from '../../utils/helpers';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const TransactionList = ({ refreshTrigger }) => {
    const { user } = useAuthContext();
    const [transactions, setTransactions] = useState([]);
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortBy, setSortBy] = useState('date');

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const fetchTransactions = useCallback(async () => {
        if (!user?.user_id) return;

        setLoading(true);
        setError(null);

        try {
            // Fetch both transactions and user data
            const [transactionsResponse, userResponse] = await Promise.all([
                transactionAPI.getTransactions(user.user_id),
                authAPI.getUser(user.user_id)
            ]);
            
            setTransactions(transactionsResponse.data || []);
            setUserData(userResponse.data || {});
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    }, [user?.user_id, refreshTrigger]);

    useEffect(() => {
        fetchTransactions();
    }, [fetchTransactions]);

    const getFilteredTransactions = () => {
        let filtered = transactions;

        // Sort transactions (no type filter since backend doesn't have transaction_type)
        filtered.sort((a, b) => {
            switch (sortBy) {
                case 'date':
                    return new Date(b.transaction_date) - new Date(a.transaction_date);
                case 'amount':
                    return parseFloat(b.amount) - parseFloat(a.amount);
                case 'category':
                    return a.category.localeCompare(b.category);
                default:
                    return 0;
            }
        });

        return filtered;
    };

    if (loading) return <Loader message="Loading transactions..." />;
    if (error) return <ErrorMessage message={error} />;

    const filteredTransactions = getFilteredTransactions();
    
    // Calculate totals for summary (same as Overview component)
    // Use monthly income from user data
    
    // Calculate total expenses from all transactions
    const totalExpenses = filteredTransactions.reduce((sum, transaction) => {
        const amount = parseFloat(transaction.amount);
        if (!isNaN(amount)) {
            return sum + amount; // This includes both positive and negative amounts
        }
        return sum;
    }, 0);

    // Since expenses are stored as negative values, totalExpenses will be negative
    // We need the absolute value for display
    const absoluteExpenses = Math.abs(totalExpenses);
    


    return (
        <div className="transaction-list">
            <div className="list-header">
                <h3>Transaction History</h3>
                <div className="list-controls">
                    <div className="sort-group">
                        <label htmlFor="sort">Sort by:</label>
                        <select
                            id="sort"
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="sort-select"
                        >
                            <option value="date">Date</option>
                            <option value="amount">Amount</option>
                            <option value="category">Category</option>
                        </select>
                    </div>

                    <button onClick={fetchTransactions} className="refresh-button">
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {filteredTransactions.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-icon">📭</span>
                    <h4>No transactions found</h4>
                    <p>Start by adding your first transaction!</p>
                </div>
                ) : (
                <div className="transactions-container">
                    <div className="transactions-summary">
                        <div className="summary-item">
                            <span className="summary-label">Total Expenses:</span>
                            <span className="summary-value expense">
                                ${absoluteExpenses.toFixed(2)}
                            </span>
                        </div>
                    </div>

                    <div className="transactions-grid">
                        {filteredTransactions.map((transaction, index) => (
                            <div key={index} className="transaction-card">
                                <div className="transaction-header">
                                    <div className="transaction-icon">
                                        {getCategoryIcon(transaction.category)}
                                    </div>
                                    <div className="transaction-info">
                                        <h4 className="transaction-category">{transaction.category}</h4>
                                        <p className="transaction-date">
                                            {formatDate(transaction.transaction_date)}
                                        </p>
                                    </div>
                                    <div className="transaction-amount expense">
                                        -${Math.abs(parseFloat(transaction.amount)).toFixed(2)}
                                    </div>
                                </div>
                                
                                <div className="transaction-details">
                                    {transaction.description && (
                                        <div className="detail-row">
                                            <span className="detail-label">Description:</span>
                                            <span className="detail-value">{transaction.description}</span>
                                        </div>
                                    )}
                                    
                                    <div className="detail-row">
                                        <span className="detail-label">Amount:</span>
                                        <span className="detail-value expense">
                                            -${Math.abs(parseFloat(transaction.amount)).toFixed(2)}
                                        </span>
                                    </div>
                                    
                                    <div className="detail-row">
                                        <span className="detail-label">Category:</span>
                                        <span className="detail-value">{transaction.category}</span>
                                    </div>
                                    
                                    {transaction.merchant && (
                                        <div className="detail-row">
                                            <span className="detail-label">Merchant:</span>
                                            <span className="detail-value">{transaction.merchant}</span>
                                        </div>
                                    )}
                                    
                                    <div className="detail-row">
                                        <span className="detail-label">Date:</span>
                                        <span className="detail-value">{formatDate(transaction.transaction_date)}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TransactionList;