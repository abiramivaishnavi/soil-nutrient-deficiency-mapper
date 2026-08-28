import { useState, useEffect } from 'react';
import { MapContainer, ImageOverlay, LayersControl, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

const CLASS_COLORS = {
  Low: '#B23A2E',
  Moderate: '#D98E2B',
  High: '#6E9F5E',
  'Very High': '#1F4A2C',
};

function App() {
  const [stats, setStats] = useState(null);
  const [activeLayer, setActiveLayer] = useState('fertility');

  useEffect(() => {
    fetch('/stats.json')
      .then((res) => res.json())
      .then(setStats);
  }, []);

  if (!stats) return <div className="loading">Loading farm data...</div>;

  const bounds = stats.bounds;

  const overlayMap = {
    fertility: '/fertility_overlay.png',
    confidence: '/confidence_overlay.png',
    fertilizer: '/fertilizer_overlay.png',
    ndvi: '/ndvi_overlay.png',
    ndre: '/ndre_overlay.png',
    evi: '/evi_overlay.png',
    savi: '/savi_overlay.png',
    gndvi: '/gndvi_overlay.png',
  };

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">🌱</div>
          <span>Soil<b>Sight</b></span>
        </div>
        <nav>
          <a className="nav-item active" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>📊 Dashboard</a>
          <a className="nav-item" onClick={() => { setActiveLayer('fertility'); document.querySelector('.map-panel').scrollIntoView({ behavior: 'smooth' }); }}>🗺️ Fertility Map</a>
          <a className="nav-item" onClick={() => document.querySelector('.side-panel').scrollIntoView({ behavior: 'smooth' })}>🧪 Fertilizer Plan</a>
          <a className="nav-item" onClick={() => alert('Machine Learning-Based Remote Sensing Soil Fertility Mapping and Variable-Rate Fertilizer Recommendation — built using Random Forest on the Soil Sight V2 dataset (Sakri, Maharashtra).')}>ℹ️ About Project</a>
        </nav>
      </aside>

      {/* Main content */}
      <main className="main">
        <header className="topbar">
          <div>
            <h1>Welcome 👋</h1>
            <p>Soil fertility overview for the Sakri agricultural region</p>
          </div>
        </header>

        {/* Stat cards */}
        <section className="stat-grid">
          <div className="stat-card">
            <span className="stat-label">Total Area Mapped</span>
            <span className="stat-value">{stats.total_area_ha.toLocaleString()} ha</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Dominant Class</span>
            <span className="stat-value" style={{ color: CLASS_COLORS[Object.keys(stats.class_percent).reduce((a, b) => stats.class_percent[a] > stats.class_percent[b] ? a : b)] }}>
              {Object.keys(stats.class_percent).reduce((a, b) => stats.class_percent[a] > stats.class_percent[b] ? a : b)}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Model Confidence</span>
            <span className="stat-value">{(stats.mean_confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Recommended Crop</span>
            <span className="stat-value">Cotton</span>
          </div>
        </section>

        <section className="content-grid">
          {/* Map panel */}
          <div className="panel map-panel">
            <div className="panel-header">
              <h3>Fertility Zone Map</h3>
              <div className="layer-toggle">
                <button className={activeLayer === 'fertility' ? 'active' : ''} onClick={() => setActiveLayer('fertility')}>Fertility</button>
                <button className={activeLayer === 'confidence' ? 'active' : ''} onClick={() => setActiveLayer('confidence')}>Confidence</button>
                <button className={activeLayer === 'fertilizer' ? 'active' : ''} onClick={() => setActiveLayer('fertilizer')}>Fertilizer Zones</button>
                <button className={activeLayer === 'ndvi' ? 'active' : ''} onClick={() => setActiveLayer('ndvi')}>NDVI</button>
                <button className={activeLayer === 'ndre' ? 'active' : ''} onClick={() => setActiveLayer('ndre')}>NDRE</button>
                <button className={activeLayer === 'evi' ? 'active' : ''} onClick={() => setActiveLayer('evi')}>EVI</button>
                <button className={activeLayer === 'savi' ? 'active' : ''} onClick={() => setActiveLayer('savi')}>SAVI</button>
                <button className={activeLayer === 'gndvi' ? 'active' : ''} onClick={() => setActiveLayer('gndvi')}>GNDVI</button>
              </div>
            </div>
            <MapContainer
              center={stats.center}
              bounds={bounds}
              zoomControl={false}
              style={{ height: '480px', width: '100%', borderRadius: '12px' }}
            >
              <ZoomControl position="bottomright" />
              <ImageOverlay url={overlayMap[activeLayer]} bounds={bounds} />
            </MapContainer>

            {activeLayer === 'fertility' && (
              <div className="legend">
                {Object.entries(CLASS_COLORS).map(([cls, color]) => (
                  <div className="legend-item" key={cls}>
                    <span className="dot" style={{ background: color }} /> {cls}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Side panel */}
          <div className="panel side-panel">
            <h3>Fertility Breakdown</h3>
            {Object.entries(stats.class_percent).map(([cls, pct]) => (
              <div className="breakdown-row" key={cls}>
                <div className="breakdown-label">
                  <span className="dot" style={{ background: CLASS_COLORS[cls] }} />
                  {cls}
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${pct}%`, background: CLASS_COLORS[cls] }} />
                </div>
                <span className="breakdown-pct">{pct}%</span>
              </div>
            ))}

            <h3 style={{ marginTop: '28px' }}>Rule-Based Fertilizer Recommendation (Cotton)</h3>
            <table className="fert-table">
              <thead>
                <tr><th>Zone</th><th>N</th><th>P</th><th>K</th></tr>
              </thead>
              <tbody>
                {Object.entries(stats.fertilizer_rates).map(([cls, rates]) => (
                  <tr key={cls}>
                    <td><span className="dot" style={{ background: CLASS_COLORS[cls] }} /> {cls}</td>
                    <td>{rates.N} kg/ha</td>
                    <td>{rates.P} kg/ha</td>
                    <td>{rates.K} kg/ha</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="disclaimer">* Rule-based recommendation derived from Maharashtra cotton RDF guidelines, scaled by predicted fertility zone.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;