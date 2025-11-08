import React from 'react';

export default function WeatherMetricsCard({ currentData }) {
  if (!currentData || !currentData.aqi) {
    return null;
  }

  const metrics = [
    {
      label: 'Temperature',
      value: `${Math.round(currentData.temp?.[0] || 0)}°C`,
      icon: '🌡️',
      color: 'var(--aqi-unhealthy-sensitive)'
    },
    {
      label: 'Humidity',
      value: `${Math.round(currentData.humidity?.[0] || 0)}%`,
      icon: '💧',
      color: 'var(--primary-blue)'
    },
    {
      label: 'Pressure',
      value: `${Math.round(currentData.pressure?.[0] || 0)} hPa`,
      icon: '🔽',
      color: 'var(--secondary-gray)'
    },
    {
      label: 'Wind Speed',
      value: `${Math.round(currentData.wind_speed?.[0] || 0)} m/s`,
      icon: '💨',
      color: 'var(--aqi-moderate)'
    },
    {
      label: 'PM2.5',
      value: `${Math.round(currentData.pm25?.[0] || 0)} μg/m³`,
      icon: '🌫️',
      color: 'var(--aqi-unhealthy)'
    },
    {
      label: 'Dew Point',
      value: `${Math.round(currentData.dew?.[0] || 0)}°C`,
      icon: '💎',
      color: 'var(--aqi-good)'
    }
  ];

  return (
    <div style={{
      background: 'var(--background-white)',
      border: '1px solid var(--border-light)',
      borderRadius: 'var(--rounded-xl)',
      padding: '1.5rem',
      margin: '1rem 0',
      boxShadow: 'var(--shadow-md)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        marginBottom: '1.5rem'
      }}>
        <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>🌤️</span>
        <h3 style={{
          margin: '0',
          color: 'var(--text-primary)',
          fontSize: '1.25rem',
          fontWeight: '600'
        }}>
          Current Weather Conditions
        </h3>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '1rem'
      }}>
        {metrics.map((metric, index) => (
          <div key={index} style={{
            background: 'var(--background-light)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--rounded-lg)',
            padding: '1rem',
            textAlign: 'center',
            transition: 'all 0.3s ease',
            position: 'relative'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }}>
            <div style={{
              fontSize: '1.5rem',
              marginBottom: '0.5rem'
            }}>
              {metric.icon}
            </div>
            <div style={{
              fontSize: '1.25rem',
              fontWeight: '700',
              color: metric.color,
              marginBottom: '0.25rem'
            }}>
              {metric.value}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              fontWeight: '500'
            }}>
              {metric.label}
            </div>
          </div>
        ))}
      </div>

      {/* Dominant Pollutant */}
      {currentData.dominant_pollutant && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: 'linear-gradient(135deg, var(--primary-blue)10, var(--primary-blue-light)10)',
          borderRadius: 'var(--rounded-lg)',
          border: '1px solid var(--primary-blue-light)20',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.25rem'
          }}>
            Dominant Pollutant
          </div>
          <div style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: 'var(--primary-blue)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            {currentData.dominant_pollutant[0]}
          </div>
        </div>
      )}

      {/* Decorative Element */}
      <div style={{
        position: 'absolute',
        top: '-30px',
        right: '-30px',
        width: '60px',
        height: '60px',
        background: 'linear-gradient(135deg, var(--primary-blue)10, transparent)',
        borderRadius: '50%',
        pointerEvents: 'none'
      }} />
    </div>
  );
}
