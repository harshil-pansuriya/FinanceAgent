import React, { useState } from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { transactionAPI } from '../../services/api';
import { formatDate, getCategoryIcon } from '../../utils/helpers';
import Loader from '../Common/Loader';
import ErrorMessage from '../Common/ErrorMessage';

const SearchTransactions = () => {
    const { user } = useAuthContext();
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await transactionAPI.searchTransactions({
                user_id: user.user_id,
                query: searchQuery.trim()
            });
            // Backend returns array directly, not wrapped in object
            const transactions = Array.isArray(response.data) ? response.data : [];
            setSearchResults({
                transactions: transactions,
                summary: transactions.length > 0 
                    ? `Found ${transactions.length} transactions matching your search.`
                    : 'No transactions found matching your search criteria.'
            });
        } catch (err) {
            setError(err.response?.data?.message || 'Search failed');
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setSearchQuery('');
        setSearchResults(null);
        setError(null);
    };

    return (
        <div className="search-transactions">
            <div className="search-container">
                <div className="search-header">
                    <h3>Search Transactions</h3>
                    <p className="search-description">
                        Use natural language to find your transactions. Ask questions like "What did I spend on food last month?"
                    </p>
                </div>

                {error && <ErrorMessage message={error} onClose={() => setError(null)} />}

                <form onSubmit={handleSearch} className="search-form">
                    <div className="search-input-group">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="e.g., Show all my food expenses this month"
                            className="search-input"
                            disabled={loading}
                        />
                        <button 
                            type="submit" 
                            className="search-button"
                            disabled={loading || !searchQuery.trim()}
                        >
                            {loading ? '🔍' : '🔍 Search'}
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

                {loading && <Loader message="Searching transactions..." />}

                {searchResults && (
                    <div className="search-results">
                        <div className="results-header">
                            <h4>Search Results</h4>
                            <span className="results-count">
                                {searchResults.transactions?.length || 0} transactions found
                            </span>
                        </div>

                        {searchResults.summary && (
                            <div className="search-summary">
                                <p className="summary-text">{searchResults.summary}</p>
                            </div>
                        )}

                        {searchResults.transactions && searchResults.transactions.length > 0 ? (
                            <div className="results-container">
                                <div className="results-list">
                                {searchResults.transactions.map((transaction, index) => (
                                    <div key={index} className="result-item">
                                        <div className="result-icon">
                                            {getCategoryIcon(transaction.category)}
                                        </div>
                                        <div className="result-details">
                                            <div className="result-main">
                                                <h5 className="result-category">{transaction.category}</h5>
                                                <span className="result-amount expense">
                                                    -${Math.abs(parseFloat(transaction.amount)).toFixed(2)}
                                                </span>
                                            </div>
                                            <div className="result-meta">
                                                <span className="result-date">
                                                    {formatDate(transaction.transaction_date)}
                                                </span>
                                                {transaction.merchant && (
                                                    <span className="result-merchant">• {transaction.merchant}</span>
                                                )}
                                            </div>
                                            {transaction.description && (
                                                <p className="result-description">{transaction.description}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                                </div>
                            </div>
                        ) : (
                            <div className="no-results">
                                <span className="no-results-icon">🔍</span>
                                <h4>No transactions found</h4>
                                <p>Try adjusting your search query or check your transaction history.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SearchTransactions;