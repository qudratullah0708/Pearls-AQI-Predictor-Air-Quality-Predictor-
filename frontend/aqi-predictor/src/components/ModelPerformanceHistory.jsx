import React, { useState, useEffect } from 'react';

export default function ModelPerformanceHistory() {
  const [history, setHistory] = useState(null);
  const [selectedHorizon, setSelectedHorizon] = useState('24h');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:8000/model/performance/${selectedHorizon}?limit=50`);
        if (!response.ok) throw new Error('Failed to fetch performance history');
        const data = await response.json();
        setHistory(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching performance history:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchHistory();
  }, [selectedHorizon]);

  const getModelColor = (model) => {
    const colors = {
      'xgboost': '#1f77b4',
      'random_forest': '#ff7f0e',
      'linear_regression': '#2ca02c'
    };
    return colors[model] || '#9467bd';
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
        Loading performance history...
      </div>
    );
  }

  if (error || !history || history.error) {
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
        ⚠️ Unable to load performance history: {error || history?.error}
      </div>
    );
  }

  const historyData = history.history || [];
  const maxRmse = Math.max(...historyData.map(h => h.rmse), 0);

  // Group by timestamp to show all models trained at the same time
  const groupedByTimestamp = {};
  historyData.forEach(item => {
    if (!groupedByTimestamp[item.timestamp]) {
      groupedByTimestamp[item.timestamp] = [];
    }
    groupedByTimestamp[item.timestamp].push(item);
  });

  // Sort timestamps (newest first)
  const sortedTimestamps = Object.keys(groupedByTimestamp).sort((a, b) => 
    new Date(b) - new Date(a)
  );

  return (
    <div style={{
      background: 'var(--background-white)',
      borderRadius: 'var(--rounded-xl)',
      padding: '2rem',
      boxShadow: 'var(--shadow-md)',
      border: '1px solid var(--border-light)'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        borderBottom: '2px solid var(--border-light)',
        paddingBottom: '1.5rem'
      }}>
        <div>
          <h2 style={{
            margin: '0 0 0.5rem 0',
            color: 'var(--text-primary)',
            fontSize: '1.75rem',
            fontWeight: '600'
          }}>
            📊 Performance History
          </h2>
          <p style={{
            margin: '0',
            color: 'var(--text-secondary)',
            fontSize: '0.875rem'
          }}>
            Historical model performance metrics over time
          </p>
        </div>

        {/* Horizon Selector */}
        <div style={{
          display: 'flex',
          gap: '0.5rem'
        }}>
          {['24h', '48h', '72h'].map(horizon => (
            <button
              key={horizon}
              onClick={() => setSelectedHorizon(horizon)}
              style={{
                padding: '0.5rem 1rem',
                border: `2px solid ${selectedHorizon === horizon ? 'var(--primary-blue)' : 'var(--border-light)'}`,
                borderRadius: 'var(--rounded-md)',
                background: selectedHorizon === horizon ? 'var(--primary-blue)' : 'var(--background-white)',
                color: selectedHorizon === horizon ? 'white' : 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '0.875rem',
                transition: 'all 0.2s ease'
              }}
            >
              {horizon}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Section */}
      {historyData.length > 0 && (
        <div style={{
          marginBottom: '2rem',
          padding: '1.5rem',
          background: 'var(--background-light)',
          borderRadius: 'var(--rounded-lg)',
          border: '1px solid var(--border-light)'
        }}>
          <h3 style={{
            margin: '0 0 1rem 0',
            fontSize: '1.125rem',
            fontWeight: '600',
            color: 'var(--text-primary)'
          }}>
            RMSE Trend Over Time
          </h3>
          
          {/* Simple Bar Chart */}
          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '0.25rem',
            height: '200px',
            padding: '1rem 0',
            overflowX: 'auto'
          }}>
            {sortedTimestamps.slice(0, 20).reverse().map((timestamp, idx) => {
              const items = groupedByTimestamp[timestamp];
              const bestRmse = Math.min(...items.map(i => i.rmse));
              const height = maxRmse > 0 ? (bestRmse / maxRmse) * 180 : 20;
              
              return (
                <div key={idx} style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: '40px',
                  flex: 1
                }}>
                  <div style={{
                    width: '100%',
                    height: `${height}px`,
                    background: 'linear-gradient(180deg, var(--primary-blue), var(--primary-blue-light))',
                    borderRadius: '4px 4px 0 0',
                    minHeight: '4px',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  title={`${formatDate(timestamp)}\nRMSE: ${bestRmse.toFixed(2)}`}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '0.8';
                    e.currentTarget.style.transform = 'scaleY(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '1';
                    e.currentTarget.style.transform = 'scaleY(1)';
                  }}
                  />
                </div>
              );
            })}
          </div>
          
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '0.5rem',
            fontSize: '0.75rem',
            color: 'var(--text-muted)'
          }}>
            <span>Older</span>
            <span>Recent ({historyData.length} records)</span>
          </div>
        </div>
      )}

      {/* History Table */}
      <div style={{
        overflowX: 'auto'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.875rem'
        }}>
          <thead>
            <tr style={{
              background: 'var(--background-light)',
              borderBottom: '2px solid var(--border-light)'
            }}>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>Date</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>Model</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>RMSE</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>MAE</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>R²</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'right',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>MAPE</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'center',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedTimestamps.map((timestamp, idx) => {
              const items = groupedByTimestamp[timestamp];
              return items.map((item, itemIdx) => (
                <tr 
                  key={`${timestamp}-${itemIdx}`}
                  style={{
                    borderBottom: '1px solid var(--border-light)',
                    background: item.deployed ? 'var(--background-light)' : 'transparent',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!item.deployed) {
                      e.currentTarget.style.background = 'var(--background-light)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!item.deployed) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <td style={{
                    padding: '0.75rem',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'nowrap'
                  }}>
                    {formatDate(item.timestamp)}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    color: 'var(--text-primary)',
                    fontWeight: '600'
                  }}>
                    <span style={{
                      display: 'inline-block',
                      width: '12px',
                      height: '12px',
                      borderRadius: '2px',
                      background: getModelColor(item.model),
                      marginRight: '0.5rem'
                    }} />
                    {item.model.replace('_', ' ')}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: 'var(--text-primary)',
                    fontWeight: '600'
                  }}>
                    {item.rmse.toFixed(2)}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: 'var(--text-secondary)'
                  }}>
                    {item.mae.toFixed(2)}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: item.r2 > 0 ? 'var(--aqi-good)' : 'var(--text-secondary)'
                  }}>
                    {item.r2.toFixed(3)}
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'right',
                    color: 'var(--text-secondary)'
                  }}>
                    {item.mape.toFixed(2)}%
                  </td>
                  <td style={{
                    padding: '0.75rem',
                    textAlign: 'center'
                  }}>
                    {item.deployed && (
                      <span style={{
                        padding: '0.25rem 0.5rem',
                        background: 'var(--aqi-good)',
                        color: 'white',
                        borderRadius: '999px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        ✓ Active
                      </span>
                    )}
                  </td>
                </tr>
              ));
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      {historyData.length > 0 && (
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: 'var(--background-light)',
          borderRadius: 'var(--rounded-lg)',
          display: 'flex',
          justifyContent: 'space-around',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--text-primary)'
            }}>
              {historyData.length}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}>
              Total Records
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--aqi-good)'
            }}>
              {Math.min(...historyData.map(h => h.rmse)).toFixed(2)}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}>
              Best RMSE
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: '700',
              color: 'var(--text-primary)'
            }}>
              {(historyData.reduce((sum, h) => sum + h.rmse, 0) / historyData.length).toFixed(2)}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}>
              Average RMSE
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

