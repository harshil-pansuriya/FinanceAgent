import React from 'react';

const ErrorMessage = ({ message, onClose, title = "Error" }) => {
    if (!message) return null;

    return (
        <div className="error-message">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
                <div className="error-title">{title}</div>
                <div className="error-description">{message}</div>
            </div>
            {onClose && (
                <button className="error-close" onClick={onClose}>
                    ×
                </button>
            )}
        </div>
    );
};

export default ErrorMessage;