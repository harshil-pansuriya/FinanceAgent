import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { transactionAPI } from '../../services/api';
import { formatDate, getCategoryIcon } from '../../utils/helpers';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const TransactionList = ({ refreshTrigger }) => {
    const { user } = useAuthContext();
    const [transactions, setTransactions] = useState([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortBy, setSortBy] = useState('date');

    const fetchTransactions = useCallback(async () => {
        if (!user?.user_id) return;

        setLoading(true);
        setError(null);

        try {
            // Fetch transactions
            const transactionsResponse = await transactionAPI.getTransactions(user.user_id);
            setTransactions(transactionsResponse.data || []);
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    }, [user?.user_id]);

    useEffect(() => {
        fetchTransactions();
    }, [fetchTransactions, refreshTrigger]);

    const getFilteredTransactions = () => {
        const copy = [...transactions];

        // Sort transactions (no type filter since backend doesn't have transaction_type)
        copy.sort((a, b) => {
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

        return copy;
    };

    const filteredTransactions = useMemo(getFilteredTransactions, [transactions, sortBy]);
    
    // Calculate total expenses from all transactions
    const absoluteExpenses = useMemo(() => {
        const total = filteredTransactions.reduce((sum, transaction) => {
            const amount = parseFloat(transaction.amount);
            return isNaN(amount) ? sum : sum + amount;
        }, 0);
        return Math.abs(total);
    }, [filteredTransactions]);

    if (loading) return <Loader message="Loading transactions..." />;
    if (error) return <ErrorMessage message={error} />;

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
                                        <p className="transaction-meta">
                                            {transaction.description ? (
                                                <span className="transaction-description">{transaction.description}</span>
                                            ) : null}
                                        </p>
                                        <p className="transaction-date">
                                            {formatDate(transaction.transaction_date)}
                                        </p>
                                    </div>
                                    <div className="transaction-merchant-right">
                                      {transaction.merchant ? transaction.merchant : ''}
                                    </div>
                                    <div className={`transaction-amount ${parseFloat(transaction.amount) < 0 ? 'expense' : 'income'}`}>
                                        {parseFloat(transaction.amount) < 0 ? '-' : '+'}${Math.abs(parseFloat(transaction.amount)).toFixed(2)}
                                    </div>
                                </div>
                                
                                <div className="transaction-details">
                                    {/* Keep details for accessibility but minimized in classic theme */}
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