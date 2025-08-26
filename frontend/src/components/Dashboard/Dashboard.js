import React, { useState } from 'react';
import Header from '../Common/Header';
import Overview from './Overview';
import AddTransaction from '../Transactions/AddTransaction';
import TransactionList from '../Transactions/TransactionList';
import SearchTransactions from '../Transactions/SearchTransactions';
import Insights from '../Analysis/Insights';
import ErrorMessage from '../Common/ErrorMessage';

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('overview');
    const [error, setError] = useState(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Trigger refresh for components
    const handleRefresh = () => {
        setRefreshTrigger(prev => prev + 1);
    };

    const tabs = [
        { id: 'overview', label: 'Overview', icon: '📊' },
        { id: 'transactions', label: 'Add Transaction', icon: '💰' },
        { id: 'history', label: 'Transaction History', icon: '📝' },
        { id: 'search', label: 'Search', icon: '🔍' },
        { id: 'insights', label: 'Insights', icon: '📈' },
    ];

    const handleNavigateToInsights = () => {
        setActiveTab('insights');
    };

    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return <Overview refreshTrigger={refreshTrigger} onNavigateToInsights={handleNavigateToInsights} />;
            case 'transactions':
                return <AddTransaction onTransactionAdded={handleRefresh} />;
            case 'history':
                return <TransactionList refreshTrigger={refreshTrigger} />;
            case 'search':
                return <SearchTransactions />;
            case 'insights':
                return <Insights refreshTrigger={refreshTrigger} />;
            default:
                return <Overview refreshTrigger={refreshTrigger} onNavigateToInsights={handleNavigateToInsights} />;
        }
    };


    return (
        <div className="dashboard">
            <Header />
        
            <div className="dashboard-container">
                {error && (
                    <ErrorMessage 
                        message={error} 
                        onClose={() => setError(null)} 
                    />
                )}

                <div className="dashboard-content">
                    <div className="dashboard-sidebar">
                        <nav className="dashboard-nav">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                                >
                                    <span className="nav-icon">{tab.icon}</span>
                                    <span className="nav-label">{tab.label}</span>
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="dashboard-main">
                        <div className="dashboard-header">
                            <h2 className="dashboard-title">
                                {tabs.find(tab => tab.id === activeTab)?.label}
                            </h2>
                            <p className="dashboard-subtitle">
                                Manage your finances with ease
                            </p>
                        </div>
                        
                        <div className="dashboard-content-area">
                            {renderTabContent()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;