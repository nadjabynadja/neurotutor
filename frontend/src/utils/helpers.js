export const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

export const formatDate = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
};

export const formatTime = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDateTime = (date) => {
  return `${formatDate(date)} ${formatTime(date)}`;
};

export const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

export const throttle = (fn, limit) => {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

export const clamp = (value, min, max) => {
  return Math.min(Math.max(value, min), max);
};

export const normalizeValue = (value, min, max) => {
  if (max === min) return 0;
  return (value - min) / (max - min);
};

export const lerp = (start, end, t) => {
  return start + (end - start) * t;
};

export const getStatusColor = (value, inverted = false) => {
  const effectiveValue = inverted ? 1 - value : value;
  if (effectiveValue >= 0.7) return '#4caf50';
  if (effectiveValue >= 0.4) return '#ff9800';
  return '#f44336';
};

export const getStatusLabel = (value, inverted = false) => {
  const effectiveValue = inverted ? 1 - value : value;
  if (effectiveValue >= 0.7) return 'Good';
  if (effectiveValue >= 0.4) return 'Fair';
  return 'Poor';
};

export const pluralize = (count, singular, plural) => {
  return count === 1 ? singular : plural;
};

export const truncate = (str, length = 100) => {
  if (!str || str.length <= length) return str;
  return str.slice(0, length) + '...';
};
