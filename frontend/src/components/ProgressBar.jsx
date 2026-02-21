import React from 'react';

export const ProgressBar = ({ 
  value = 0, 
  max = 1,
  label,
  showValue = true,
  color,
  size = 'medium',
  animated = true
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  const getColor = () => {
    if (color) return color;
    if (percentage >= 70) return '#4caf50';
    if (percentage >= 40) return '#ff9800';
    return '#f44336';
  };

  const heights = {
    small: '4px',
    medium: '8px',
    large: '12px'
  };

  return (
    <div style={{ width: '100%' }}>
      {(label || showValue) && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '4px',
          fontSize: '14px'
        }}>
          {label && <span style={{ fontWeight: '500' }}>{label}</span>}
          {showValue && (
            <span style={{ color: '#666' }}>
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div style={{
        width: '100%',
        height: heights[size],
        backgroundColor: '#e0e0e0',
        borderRadius: heights[size],
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          backgroundColor: getColor(),
          borderRadius: heights[size],
          transition: animated ? 'width 0.3s ease' : 'none'
        }} />
      </div>
    </div>
  );
};

export const MetricCard = ({ 
  label, 
  value, 
  icon,
  trend,
  description 
}) => {
  const getTrendColor = () => {
    if (!trend) return '#666';
    return trend > 0 ? '#4caf50' : trend < 0 ? '#f44336' : '#666';
  };

  return (
    <div style={{
      padding: '16px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '8px'
      }}>
        <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>
          {label}
        </span>
        {icon && <span style={{ fontSize: '20px' }}>{icon}</span>}
      </div>
      <div style={{ 
        fontSize: '24px', 
        fontWeight: '600',
        color: '#333'
      }}>
        {typeof value === 'number' ? `${(value * 100).toFixed(0)}%` : value}
      </div>
      {trend !== undefined && (
        <div style={{ 
          fontSize: '12px', 
          color: getTrendColor(),
          marginTop: '4px'
        }}>
          {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend)}%
        </div>
      )}
      {description && (
        <p style={{ 
          fontSize: '12px', 
          color: '#999', 
          margin: '8px 0 0' 
        }}>
          {description}
        </p>
      )}
    </div>
  );
};

export default ProgressBar;
