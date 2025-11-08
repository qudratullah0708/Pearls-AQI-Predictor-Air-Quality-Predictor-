// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import PredictionCard from './components/PredictionCard';
import WeatherMetricsCard from './components/WeatherMetricsCard';
import ModelPerformanceCard from './components/ModelPerformanceCard';
import ModelPerformanceHistory from './components/ModelPerformanceHistory';

export default function AQIDashboard() {
  const [currentAQI, setCurrentAQI] = useState(null);
  const [predictions, setPredictions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/predictions/all');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setCurrentAQI(data.current_aqi);
        setPredictions(data.predictions);
        setLastUpdated(new Date());
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, []);

  const getAQIStatus = (aqi) => {
    if (!aqi) return 'No Data';
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
  };

  const getAQIColor = (aqi) => {
    if (!aqi) return 'var(--text-muted)';
    if (aqi <= 50) return 'var(--aqi-good)';
    if (aqi <= 100) return 'var(--aqi-moderate)';
    if (aqi <= 150) return 'var(--aqi-unhealthy-sensitive)';
    if (aqi <= 200) return 'var(--aqi-unhealthy)';
    if (aqi <= 300) return 'var(--aqi-very-unhealthy)';
    return 'var(--aqi-hazardous)';
  };

  const getAQIDescription = (aqi) => {
    if (!aqi) return 'No data available';
    if (aqi <= 50) return 'Air quality is satisfactory, and air pollution poses little or no risk.';
    if (aqi <= 100) return 'Air quality is acceptable. However, there may be a risk for some people.';
    if (aqi <= 150) return 'Members of sensitive groups may experience health effects.';
    if (aqi <= 200) return 'Some members of the general public may experience health effects.';
    if (aqi <= 300) return 'Health alert: The risk of health effects is increased for everyone.';
    return 'Health warning of emergency conditions.';
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, var(--background-light) 0%, #e2e8f0 100%)'
      }}>
        <div style={{
          textAlign: 'center',
          background: 'var(--background-white)',
          padding: '3rem',
          borderRadius: 'var(--rounded-xl)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border-light)'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            border: '4px solid var(--border-light)',
            borderTop: '4px solid var(--primary-blue)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1.5rem'
          }} />
          <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
            Loading AQI Data
          </h2>
          <p style={{ margin: '0', color: 'var(--text-secondary)' }}>
            Fetching the latest air quality information...
          </p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, var(--background-light) 0%, #e2e8f0 100%)'
      }}>
        <div style={{
          textAlign: 'center',
          background: 'var(--background-white)',
          padding: '3rem',
          borderRadius: 'var(--rounded-xl)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border-light)',
          maxWidth: '500px'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
          <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--aqi-unhealthy)' }}>
            Error Loading Data
          </h2>
          <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)' }}>
            {error}
          </p>
          <p style={{ margin: '0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Please check that the backend server is running on http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, var(--background-light) 0%, #e2e8f0 100%)',
      padding: '1rem'
    }}>
      {/* Header */}
      <div style={{
        background: 'var(--background-white)',
        borderRadius: 'var(--rounded-xl)',
        padding: '2rem',
        marginBottom: '2rem',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-light)',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <h1 style={{
          margin: '0 0 0.5rem 0',
          background: 'linear-gradient(135deg, var(--primary-blue), var(--primary-blue-light))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          fontSize: '3rem',
          fontWeight: '800'
        }}>
          🌬️ Air Quality Index Dashboard
        </h1>
        <p style={{
          margin: '0',
          color: 'var(--text-secondary)',
          fontSize: '1.125rem'
        }}>
          Real-time air quality monitoring and forecasting for Islamabad
        </p>
        {lastUpdated && (
          <div style={{
            marginTop: '1rem',
            fontSize: '0.875rem',
            color: 'var(--text-muted)'
          }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
        
        {/* Decorative Elements */}
        <div style={{
          position: 'absolute',
          top: '-50px',
          left: '-50px',
          width: '100px',
          height: '100px',
          background: 'linear-gradient(135deg, var(--primary-blue)10, transparent)',
          borderRadius: '50%',
          pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-30px',
          right: '-30px',
          width: '60px',
          height: '60px',
          background: 'linear-gradient(135deg, var(--aqi-good)10, transparent)',
          borderRadius: '50%',
          pointerEvents: 'none'
        }} />
      </div>

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'grid',
        gap: '2rem'
      }}>
        {/* Current AQI Card with Scale Reference */}
        <div style={{
          background: 'var(--background-white)',
          borderRadius: 'var(--rounded-xl)',
          padding: '2.5rem',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border-light)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '3rem',
            alignItems: 'center'
          }}>
            {/* Left Side - Current AQI */}
            <div style={{ textAlign: 'center' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.5rem'
              }}>
                <span style={{ fontSize: '2rem', marginRight: '0.75rem' }}>🌡️</span>
                <h2 style={{
                  margin: '0',
                  color: 'var(--text-primary)',
                  fontSize: '1.75rem',
                  fontWeight: '600'
                }}>
                  Current Air Quality
                </h2>
              </div>

              <div style={{
                fontSize: '6rem',
                fontWeight: '800',
                color: getAQIColor(currentAQI?.aqi?.[0]),
                margin: '1.5rem 0',
                lineHeight: '1',
                textShadow: '0 4px 8px rgba(0,0,0,0.1)'
              }}>
                {currentAQI?.aqi?.[0] ? Math.round(currentAQI.aqi[0]) : '--'}
              </div>

              <div style={{
                display: 'inline-block',
                background: getAQIColor(currentAQI?.aqi?.[0]),
                color: 'white',
                padding: '0.5rem 1.5rem',
                borderRadius: '9999px',
                fontSize: '1rem',
                fontWeight: '600',
                marginBottom: '1rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                boxShadow: `0 4px 12px ${getAQIColor(currentAQI?.aqi?.[0])}40`
              }}>
                {getAQIStatus(currentAQI?.aqi?.[0])}
              </div>

              <p style={{
                margin: '0 auto',
                color: 'var(--text-secondary)',
                fontSize: '1rem',
                lineHeight: '1.6',
                maxWidth: '400px'
              }}>
                {getAQIDescription(currentAQI?.aqi?.[0])}
              </p>
            </div>

            {/* Right Side - AQI Scale Reference */}
            <div style={{
              borderLeft: '2px solid var(--border-light)',
              paddingLeft: '2rem'
            }}>
              <h4 style={{
                margin: '0 0 1rem 0',
                fontSize: '1rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                textAlign: 'left'
              }}>
                AQI Scale Reference
              </h4>
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                {[
                  { range: '0-50', label: 'Good', color: 'var(--aqi-good)' },
                  { range: '51-100', label: 'Moderate', color: 'var(--aqi-moderate)' },
                  { range: '101-150', label: 'Unhealthy for Sensitive Groups', color: 'var(--aqi-unhealthy-sensitive)' },
                  { range: '151-200', label: 'Unhealthy', color: 'var(--aqi-unhealthy)' },
                  { range: '201-300', label: 'Very Unhealthy', color: 'var(--aqi-very-unhealthy)' },
                  { range: '300+', label: 'Hazardous', color: 'var(--aqi-hazardous)' }
                ].map((item, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.5rem',
                    borderRadius: 'var(--rounded-md)',
                    background: currentAQI?.aqi?.[0] && currentAQI.aqi[0] >= parseInt(item.range.split('-')[0]) && 
                               (item.range === '300+' || currentAQI.aqi[0] <= (parseInt(item.range.split('-')[1]) || 400)) ? 
                               `${item.color}15` : 'transparent',
                    transition: 'background 0.3s ease'
                  }}>
                    <div style={{
                      width: '20px',
                      height: '20px',
                      background: item.color,
                      borderRadius: '4px',
                      border: '2px solid white',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }} />
                    <div style={{ flex: 1 }}>
                      <div style={{
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: 'var(--text-primary)'
                      }}>
                        {item.range} - {item.label}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Decorative Background */}
          <div style={{
            position: 'absolute',
            top: '0',
            right: '0',
            width: '200px',
            height: '200px',
            background: `linear-gradient(135deg, ${getAQIColor(currentAQI?.aqi?.[0])}15, transparent)`,
            borderRadius: '0 0 0 100%',
            pointerEvents: 'none'
          }} />
        </div>

        {/* Weather Metrics */}
        <WeatherMetricsCard currentData={currentAQI} />

        {/* Predictions Section */}
        <div style={{
          background: 'var(--background-white)',
          borderRadius: 'var(--rounded-xl)',
          padding: '2rem',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-light)'
        }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '2rem'
          }}>
            <h2 style={{
              margin: '0 0 0.5rem 0',
              color: 'var(--text-primary)',
              fontSize: '1.75rem',
              fontWeight: '600'
            }}>
              🔮 Air Quality Forecast
            </h2>
            <p style={{
              margin: '0',
              color: 'var(--text-secondary)'
            }}>
              Predicted air quality for the next 3 days
            </p>
          </div>

          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <PredictionCard 
              title="Tomorrow (24h)" 
              value={predictions["24h"]} 
              horizon="24h"
            />
            <PredictionCard 
              title="2 Days (48h)" 
              value={predictions["48h"]} 
              horizon="48h"
            />
            <PredictionCard 
              title="3 Days (72h)" 
              value={predictions["72h"]} 
              horizon="72h"
            />
          </div>
        </div>

        {/* Model Performance Section */}
        <ModelPerformanceCard />

        {/* Model Performance History Section */}
        <ModelPerformanceHistory />

        {/* Add spin animation to the page */}
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
}