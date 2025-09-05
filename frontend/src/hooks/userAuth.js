import { useState } from 'react';
import { useAuthContext } from '../context/AuthContext';
import { authAPI } from '../services/api';

export const useAuth = () => {
    const { login: contextLogin, logout: contextLogout } = useAuthContext();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const register = async (userData) => {
        setLoading(true);
        setError(null);

        try{
            const response= await authAPI.register(userData);
            contextLogin(response.data);
            return response.data;
        }
        catch (err) {
            setError(err.response?.data?.message || 'Registration failed');
            throw err;
        }
        finally {
            setLoading(false);
        }
    };

    const login= async (loginData) => {
        setLoading(true);
        setError(null);
        try {
            const response= await authAPI.login(loginData);
            contextLogin(response.data);
            return response.data;
        } 
        catch (err) {
            // Show a clean, user-friendly message for login failures
            setError('Login failed try again');
            throw err;
        }
        finally{
            setLoading(false);
        }
    };

    const logout = () => {
        contextLogout();
    };

    return {
        register,
        login,
        logout,
        loading,
        error,
    };
};
