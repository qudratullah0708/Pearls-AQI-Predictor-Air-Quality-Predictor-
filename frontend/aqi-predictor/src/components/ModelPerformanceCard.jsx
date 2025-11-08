import React, { useState, useEffect } from 'react';

export default function ModelPerformanceCard() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const response = await fetch('http://localhost:8000/model/performance/overview');
        if (!response.ok) throw new Error('Failed to fetch performance data');
        const data = await response.json();
        console.log('Model Performance Data:', data);
        setOverview(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching performance data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchPerformance();
  }, []);

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'degrading': return '📉';
      case 'stable': return '➡️';
      default: return '📊';
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'improving': return 'var(--aqi-good)';
      case 'degrading': return 'var(--aqi-unhealthy)';
      case 'stable': return 'var(--text-secondary)';
      default: return 'var(--text-muted)';
    }
  };

  if (loading) {
    return (
      <div style={{
        background: 'var(--background-white)',
        borderRadius: 'var(--rounded-xl)',
        padding: '3rem',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-light)',
        textAlign: 'center',
        color: 'var(--text-secondary)'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid var(--border-light)',
          borderTop: '3px solid var(--primary-blue)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 1rem'
        }} />
        Loading model performance...
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div style={{
        background: 'var(--background-white)',
        borderRadius: 'var(--rounded-xl)',
        padding: '2rem',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-light)',
        textAlign: 'center',
        color: 'var(--aqi-unhealthy)'
      }}>
        ⚠️ Unable to load model performance data
      </div>
    );
  }

  return (
    <div style={{
      background: 'var(--background-white)',
      borderRadius: 'var(--rounded-xl)',
      padding: '2rem',
      boxShadow: 'var(--shadow-md)',
      border: '1px solid var(--border-light)'
    }}>
      <div style={{
        textAlign: 'center',
        marginBottom: '2rem',
        borderBottom: '2px solid var(--border-light)',
        paddingBottom: '1.5rem'
      }}>
        <h2 style={{
          margin: '0 0 0.5rem 0',
          color: 'var(--text-primary)',
          fontSize: '1.75rem',
          fontWeight: '600'
        }}>
          🤖 Model Performance
        </h2>
        <p style={{
          margin: '0',
          color: 'var(--text-secondary)',
          fontSize: '0.875rem'
        }}>
          AI model training metrics and trends
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem'
      }}>
        {['24h', '48h', '72h'].map(horizon => {
          const modelData = overview[horizon];
          
          if (!modelData || modelData.error) {
            return (
              <div key={horizon} style={{
                padding: '1.5rem',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--rounded-lg)',
                background: 'var(--background-light)',
                textAlign: 'center',
                color: 'var(--text-muted)'
              }}>
                No data for {horizon} model
              </div>
            );
          }

          return (
            <div key={horizon} style={{
              padding: '1.5rem',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--rounded-lg)',
              transition: 'all 0.3s ease',
              background: modelData.deployed ? 'var(--background-light)' : 'var(--background-white)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = 'var(--shadow-md)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}>
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h3 style={{
                  margin: 0,
                  color: 'var(--text-primary)',
                  fontSize: '1.125rem',
                  fontWeight: '600'
                }}>
                  {horizon} Model
                </h3>
                {modelData.deployed && (
                  <span style={{
                    fontSize: '0.75rem',
                    padding: '0.25rem 0.5rem',
                    background: 'var(--aqi-good)',
                    color: 'white',
                    borderRadius: '999px',
                    fontWeight: '600'
                  }}>
                    ✓ Active
                  </span>
                )}
              </div>

              {/* RMSE Metric */}
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '0.25rem',
                  fontSize: '0.875rem',
                  color: 'var(--text-secondary)'
                }}>
                  <span>RMSE (Lower is better)</span>
                  <span style={{ fontWeight: '600' }}>
                    {modelData.current_rmse?.toFixed(2)}
                  </span>
                </div>
                <div style={{
                  height: '8px',
                  background: 'var(--background-light)',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(100, (modelData.current_rmse || 0) / 50 * 100)}%`,
                    background: modelData.trend === 'improving' ? 'var(--aqi-good)' : 
                               modelData.trend === 'degrading' ? 'var(--aqi-unhealthy)' : 
                               'var(--text-secondary)',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              {/* Trend Indicator */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem',
                background: 'var(--background-light)',
                borderRadius: 'var(--rounded-md)',
                marginBottom: '0.5rem'
              }}>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Trend:
                </span>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{ fontSize: '1.25rem' }}>
                    {getTrendIcon(modelData.trend)}
                  </span>
                  <span style={{
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: getTrendColor(modelData.trend),
                    textTransform: 'capitalize'
                  }}>
                    {modelData.trend}
                  </span>
                </div>
              </div>

              {/* Additional Metrics */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '0.5rem',
                fontSize: '0.75rem',
                color: 'var(--text-muted)'
              }}>
                <div>Model: {modelData.model_type || 'N/A'}</div>
                <div>Version: {modelData.active_version?.substring(0, 8) || 'N/A'}</div>
                <div>MAE: {modelData.current_mae?.toFixed(2) || 'N/A'}</div>
                <div>R²: {modelData.current_r2?.toFixed(3) || 'N/A'}</div>
              </div>

              {/* Last Training */}
              {modelData.last_trained && (
                <div style={{
                  marginTop: '0.75rem',
                  paddingTop: '0.75rem',
                  borderTop: '1px solid var(--border-light)',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  textAlign: 'center'
                }}>
                  Last trained: {new Date(modelData.last_trained).toLocaleDateString()}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

