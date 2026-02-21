import React from 'react';

export const Card = ({ 
  children, 
  title, 
  subtitle,
  className = '',
  style = {} 
}) => {
  return (
    <div 
      className={className}
      style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        padding: '20px',
        ...style
      }}
    >
      {title && (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#333' }}>
            {title}
          </h3>
          {subtitle && (
            <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#666' }}>
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
