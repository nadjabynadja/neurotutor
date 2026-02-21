import React from 'react';

export const Button = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  className = ''
}) => {
  const baseStyles = {
    border: 'none',
    borderRadius: '8px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontWeight: '500',
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  };

  const sizes = {
    small: { padding: '8px 16px', fontSize: '14px' },
    medium: { padding: '12px 24px', fontSize: '16px' },
    large: { padding: '16px 32px', fontSize: '18px' }
  };

  const variants = {
    primary: { 
      backgroundColor: '#2196f3', 
      color: 'white',
      opacity: disabled ? 0.6 : 1
    },
    secondary: { 
      backgroundColor: '#e0e0e0', 
      color: '#333',
      opacity: disabled ? 0.6 : 1
    },
    success: { 
      backgroundColor: '#4caf50', 
      color: 'white',
      opacity: disabled ? 0.6 : 1
    },
    danger: { 
      backgroundColor: '#f44336', 
      color: 'white',
      opacity: disabled ? 0.6 : 1
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{
        ...baseStyles,
        ...sizes[size],
        ...variants[variant]
      }}
    >
      {children}
    </button>
  );
};

export default Button;
