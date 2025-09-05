import React from 'react';
import { useAuthContext } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Header = () => {
    const { user, logout } = useAuthContext();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="header">
            <div className="header-container">
                <div className="header-left">
                    <h1 className="header-title">GoalNest</h1>
                </div>
        
                <div className="header-right"> 
                    <div className="user-info">
                        <span className="user-greeting">Hello, {user?.user_id}</span>
                        <div className="user-menu">
                            <button className="user-menu-button" title={`Logged in as ${user?.user_id}`}>
                                <span className="user-avatar">{user?.user_id?.charAt(0)?.toUpperCase() || 'U'}</span>
                            </button>
                            <div className="user-dropdown">
                                <button 
                                    className="dropdown-item logout-btn" 
                                    onClick={handleLogout}
                                >
                                    
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;