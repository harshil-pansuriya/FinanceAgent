// Utility functions for formatting and validation

export const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount || 0);
};

export const parseAmount = (amount) => {
    if (typeof amount === 'number') return amount;
    if (typeof amount === 'string') {
        // Handle string numbers, including those with decimal points
        const parsed = parseFloat(amount);
        return isNaN(parsed) ? 0 : parsed;
    }
    // Handle objects (like Decimal from backend)
    if (amount && typeof amount === 'object' && amount.toString) {
        const parsed = parseFloat(amount.toString());
        return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
};

export const formatDate = (dateString) => {
    if (!dateString) return 'Invalid Date';
    
    // Handle date-only strings by adding time component
    const dateToFormat = dateString.includes('T') ? dateString : dateString + 'T00:00:00';
    const date = new Date(dateToFormat);
    
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};



export const getCategoryColor = (category) => {
    const colors = {
        'food': '#FF6B6B',
        'transport': '#4ECDC4',
        'entertainment': '#45B7D1',
        'shopping': '#96CEB4',
        'utilities': '#FFEAA7',
        'healthcare': '#DDA0DD',
        'education': '#98D8C8',
        'salary': '#F7DC6F',
        'freelance': '#BB8FCE',
        'investment': '#85C1E9',
        'other': '#D5DBDB'
    };
    return colors[category.toLowerCase()] || colors.other;
};

export const getCategoryIcon = (category) => {
    const icons = {
        'food': '🍕',
        'transport': '🚗',
        'entertainment': '🎬',
        'shopping': '🛍️',
        'utilities': '💡',
        'healthcare': '🏥',
        'education': '📚',
        'salary': '💰',
        'freelance': '💻',
        'investment': '📈',
        'other': '📝'
    };
    return icons[category.toLowerCase()] || icons.other;
};

