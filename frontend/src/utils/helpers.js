// Utility functions for formatting and validation

export const formatCurrency = (amount) => {
    // Format currency in USD with $ symbol for a consistent experience
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
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



// removed unused getCategoryColor

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

