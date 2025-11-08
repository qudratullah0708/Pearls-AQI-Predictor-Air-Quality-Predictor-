import React from 'react';

export default function AQITrendChart({ predictions }) {
  const getAQIColor = (aqi) => {
    if (!aqi) return 'var(--text-muted)';
    if (aqi <= 50) return 'var(--aqi-good)';
    if (aqi <= 100) return 'var(--aqi-moderate)';
    if (aqi <= 150) return 'var(--aqi-unhealthy-sensitive)';
    if (aqi <= 200) return 'var(--aqi-unhealthy)';
    if (aqi <= 300) return 'var(--aqi-very-unhealthy)';
    return 'var(--aqi-hazardous)';
  };

  const data = [
    { label: '24h', value: predictions["24h"], icon: '🌅', description: 'Tomorrow' },
    { label: '48h', value: predictions["48h"], icon: '🌄', description: 'Day After' },
    { label: '72h', value: predictions["72h"], icon: '🌆', description: '3 Days' }
  ].filter(item => item.value !== undefined);

  const maxValue = Math.max(...data.map(d => d.value || 0));
  const chartHeight = Math.max(200, Math.min(280, window.innerWidth * 0.15));

  return (
    <div className="aqi-trend-chart" style={{
      background: 'var(--background-white)',
      border: '1px solid var(--border-light)',
      borderRadius: 'var(--rounded-xl)',
      padding: '2rem',
      margin: '1.5rem 0',
      boxShadow: 'var(--shadow-md)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      Header
      <div style={{
        textAlign: 'center',
        marginBottom: '2rem',
        position: 'relative'
      }}>
        <h3 style={{ 
          margin: '0 0 0.5rem 0', 
          color: 'var(--text-primary)',
          fontSize: '1.5rem',
          fontWeight: '600'
        }}>
          📈 AQI Prediction Trend
        </h3>
        <p style={{
          margin: '0',
          color: 'var(--text-secondary)',
          fontSize: '0.875rem'
        }}>
          Forecasted air quality over the next 3 days
        </p>
      </div>
      
      {data.length > 0 ? (
        <div style={{
          display: 'flex',
          alignItems: 'end',
          justifyContent: 'center',
          height: chartHeight,
          gap: 'clamp(1rem, 4vw, 2rem)',
          padding: '1rem 0',
          flexWrap: 'wrap'
        }}>
          {data.map((item, index) => {
            const height = maxValue > 0 ? (item.value / maxValue) * (chartHeight - 80) : 20;
            const color = getAQIColor(item.value);
            
            return (
              <div key={index} style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center',
                position: 'relative'
              }}>
                {/* Bar Container */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  height: chartHeight - 60,
                  justifyContent: 'flex-end'
                }}>
                  {/* Value Label */}
                  <div style={{
                    fontSize: 'clamp(1rem, 3vw, 1.25rem)',
                    fontWeight: '700',
                    color: color,
                    marginBottom: '0.5rem',
                    textAlign: 'center'
                  }}>
                    {Math.round(item.value)}
                  </div>
                  
                  {/* Bar */}
                  <div style={{
                    width: 'clamp(50px, 8vw, 80px)',
                    height: `${height}px`,
                    background: `linear-gradient(180deg, ${color} 0%, ${color}dd 100%)`,
                    borderRadius: '8px 8px 0 0',
                    position: 'relative',
                    boxShadow: `0 4px 12px ${color}40`,
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                    minHeight: '20px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.boxShadow = `0 8px 20px ${color}60`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow = `0 4px 12px ${color}40`;
                  }}>
                    {/* Bar Gradient Overlay */}
                    <div style={{
                      position: 'absolute',
                      top: '0',
                      left: '0',
                      right: '0',
                      height: '20px',
                      background: `linear-gradient(180deg, ${color}80, transparent)`,
                      borderRadius: '8px 8px 0 0'
                    }} />
                  </div>
                </div>

                {/* Bottom Labels */}
                <div style={{
                  marginTop: '1rem',
                  textAlign: 'center',
                  minWidth: 'clamp(80px, 12vw, 120px)'
                }}>
                  <div style={{
                    fontSize: 'clamp(1.25rem, 4vw, 1.5rem)',
                    marginBottom: '0.25rem'
                  }}>
                    {item.icon}
                  </div>
                  <div style={{
                    fontSize: 'clamp(0.75rem, 2.5vw, 0.875rem)',
                    fontWeight: '600',
                    color: 'var(--text-primary)',
                    marginBottom: '0.125rem'
                  }}>
                    {item.label}
                  </div>
                  <div style={{
                    fontSize: 'clamp(0.65rem, 2vw, 0.75rem)',
                    color: 'var(--text-secondary)'
                  }}>
                    {item.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          color: 'var(--text-secondary)', 
          padding: '3rem',
          fontSize: '1rem'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
            No Prediction Data Available
          </h4>
          <p style={{ margin: '0' }}>
            Unable to load forecast data. Please check your connection.
          </p>
        </div>
      )}

      {/* Chart Legend */}
      {data.length > 0 && (
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: 'var(--background-light)',
          borderRadius: 'var(--rounded-lg)',
          border: '1px solid var(--border-light)'
        }}>
          <h4 style={{
            margin: '0 0 0.75rem 0',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
            textAlign: 'center'
          }}>
            AQI Scale Reference
          </h4>
          <div style={{
            display: 'flex',
            justifyContent: 'space-around',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            {[
              { range: '0-50', label: 'Good', color: 'var(--aqi-good)' },
              { range: '51-100', label: 'Moderate', color: 'var(--aqi-moderate)' },
              { range: '101-150', label: 'Unhealthy for Sensitive', color: 'var(--aqi-unhealthy-sensitive)' },
              { range: '151-200', label: 'Unhealthy', color: 'var(--aqi-unhealthy)' },
              { range: '201-300', label: 'Very Unhealthy', color: 'var(--aqi-very-unhealthy)' },
              { range: '300+', label: 'Hazardous', color: 'var(--aqi-hazardous)' }
            ].map((item, index) => (
              <div key={index} style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '0.75rem'
              }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  background: item.color,
                  borderRadius: '2px',
                  marginRight: '0.25rem'
                }} />
                <span style={{ color: 'var(--text-secondary)' }}>
                  {item.range}: {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decorative Background */}
      <div style={{
        position: 'absolute',
        top: '-50px',
        right: '-50px',
        width: '100px',
        height: '100px',
        background: 'linear-gradient(135deg, var(--primary-blue)10, transparent)',
        borderRadius: '50%',
        pointerEvents: 'none'
      }} />
    </div>
  );
}