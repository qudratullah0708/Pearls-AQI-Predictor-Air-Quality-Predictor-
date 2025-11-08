import React from 'react';

export default function PredictionCard({ title, value, horizon }) {
  const getAQIColor = (aqi) => {
    if (!aqi) return 'var(--text-muted)';
    if (aqi <= 50) return 'var(--aqi-good)';
    if (aqi <= 100) return 'var(--aqi-moderate)';
    if (aqi <= 150) return 'var(--aqi-unhealthy-sensitive)';
    if (aqi <= 200) return 'var(--aqi-unhealthy)';
    if (aqi <= 300) return 'var(--aqi-very-unhealthy)';
    return 'var(--aqi-hazardous)';
  };

  const getAQIStatus = (aqi) => {
    if (!aqi) return 'No Data';
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
  };

  const getAQIDescription = (aqi) => {
    if (!aqi) return 'No data available';
    if (aqi <= 50) return 'Air quality is satisfactory';
    if (aqi <= 100) return 'Air quality is acceptable';
    if (aqi <= 150) return 'Sensitive groups may experience health effects';
    if (aqi <= 200) return 'Everyone may experience health effects';
    if (aqi <= 300) return 'Health alert: everyone may experience serious health effects';
    return 'Health warnings of emergency conditions';
  };

  const getHorizonIcon = (horizon) => {
    switch (horizon) {
      case '24h': return '🌅';
      case '48h': return '🌄';
      case '72h': return '🌆';
      default: return '📊';
    }
  };

  return (
    <div className="prediction-card" style={{
      background: 'var(--background-white)',
      border: '1px solid var(--border-light)',
      borderRadius: 'var(--rounded-xl)',
      padding: '1.5rem',
      margin: '0.5rem',
      minWidth: '280px',
      maxWidth: '320px',
      textAlign: 'center',
      boxShadow: 'var(--shadow-md)',
      transition: 'all 0.3s ease',
      position: 'relative',
      overflow: 'hidden'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'var(--shadow-md)';
    }}>
      {/* Card Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>
          {getHorizonIcon(horizon)}
        </span>
        <h3 style={{ 
          margin: 0, 
          color: 'var(--text-primary)',
          fontSize: '1.125rem',
          fontWeight: '600'
        }}>
          {title}
        </h3>
      </div>

      {/* AQI Value */}
      <div style={{
        fontSize: '3rem',
        fontWeight: '700',
        color: getAQIColor(value),
        margin: '1rem 0',
        lineHeight: '1',
        textShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        {value ? Math.round(value) : '--'}
      </div>

      {/* Status Badge */}
      <div style={{
        display: 'inline-block',
        background: getAQIColor(value),
        color: 'white',
        padding: '0.25rem 0.75rem',
        borderRadius: '9999px',
        fontSize: '0.875rem',
        fontWeight: '600',
        marginBottom: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
      }}>
        {getAQIStatus(value)}
      </div>

      {/* Description */}
      <p style={{
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        lineHeight: '1.5',
        margin: '0',
        fontStyle: 'italic'
      }}>
        {getAQIDescription(value)}
      </p>

      {/* Decorative Element */}
      <div style={{
        position: 'absolute',
        top: '0',
        right: '0',
        width: '60px',
        height: '60px',
        background: `linear-gradient(135deg, ${getAQIColor(value)}20, ${getAQIColor(value)}10)`,
        borderRadius: '0 0 0 100%',
        pointerEvents: 'none'
      }} />
    </div>
  );
}
