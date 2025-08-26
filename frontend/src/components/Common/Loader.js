import React from 'react';

const Loader = ({ size = 'medium', message = 'Loading...' }) => {
    return (
         <div className="loader-container">
      <div className={`loader ${size}`}>
        <div className="spinner"></div>
      </div>
      <p className="loader-message">{message}</p>
    </div>
    );
};

export default Loader;