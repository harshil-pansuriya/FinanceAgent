import React, { useState } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { transactionAPI } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const AddTransaction = ({ onTransactionAdded }) => {
    const { user } = useAuthContext();
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [parsedTransaction, setParsedTransaction] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        setLoading(true);
        setError(null);
        setSuccess(null);
        setParsedTransaction(null);

        try {
            const response = await transactionAPI.addTransaction({
                user_id: user.user_id,
                text: input.trim()
            });
            setParsedTransaction(response.data);
            setSuccess('Transaction added successfully!');
            setInput('');
            
            // Notify parent component to refresh data with a small delay
            if (onTransactionAdded) {
                setTimeout(() => {
                    onTransactionAdded();
                }, 500);
            }
            } catch (err) {
            const apiMsg = err.response?.data?.detail || err.response?.data?.message;
            setError(apiMsg || 'Failed to add transaction');
            } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setInput('');
        setError(null);
        setSuccess(null);
        setParsedTransaction(null);
    };

    return (
        <div className="add-transaction">
            <div className="transaction-form-container">
                <div className="form-header">
                    <h3>💰 Add New Transaction</h3>
                </div>

                {error && <ErrorMessage message={error} onClose={() => setError(null)} />}
                {success && (
                <div className="success-message">
                    <span className="success-icon">✅</span>
                    <span className="success-text">{success}</span>
                </div>
                )}

                <form onSubmit={handleSubmit} className="transaction-form">
                    <div className="form-group">
                        <label htmlFor="transaction-input"></label>
                        <textarea
                        id="transaction-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="e.g., I spent $25 on lunch at McDonald's today or paid bills on 1st of aug"
                        rows="3"
                        required
                        disabled={loading}
                        className="transaction-input"
                        />
                    </div>

                    <div className="form-actions">
                        <button 
                            type="submit" 
                            className="submit-button" 
                            disabled={loading || !input.trim()}
                        >
                            {loading ? 'Processing...' : 'Add Transaction'}
                        </button>
                        <button 
                            type="button" 
                            onClick={handleClear}
                            className="clear-button"
                            disabled={loading}
                        >
                            Clear
                        </button>
                    </div>
                </form>

                {loading && <Loader message="Processing your transaction..." />}

                {parsedTransaction && (
                    <div className="transaction-preview">
                        <h4>Transaction Details</h4>
                        <div className="preview-card">
                          <div className="preview-row">
                            <div className="preview-left">
                              <div className="preview-title">{parsedTransaction.category}</div>
                              <div className="preview-sub">
                                {formatDate(parsedTransaction.transaction_date)}
                                {parsedTransaction.merchant ? ` · ${parsedTransaction.merchant}` : ''}
                              </div>
                            </div>
                            <div className={`preview-amount expense`}>
                              -${Math.abs(parseFloat(parsedTransaction.amount)).toFixed(2)}
                            </div>
                          </div>
                          {parsedTransaction.description && (
                            <div className="preview-row">
                              <div className="preview-description">{parsedTransaction.description}</div>
                            </div>
                          )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AddTransaction;