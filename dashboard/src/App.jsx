import { useState, useEffect } from 'react';
import { MapContainer, ImageOverlay, CircleMarker, Popup, ZoomControl, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import './Dashboard.css';

/* ------------------------------------------------------------------ *
 * All numbers shown here come from the JSON files in /public:
 *   stats.json, temporal_summary.json, model_evaluation.json,
 *   validation_extra.json, npk_points.json, shc_status.json
 * Nothing numeric is typed into this file. Charts are plain SVG
 * (no extra dependency).
 * ------------------------------------------------------------------ */

const CLASS_COLORS = { Low: '#B23A2E', Moderate: '#D98E2B', High: '#6E9F5E', 'Very High': '#1F4A2C' };
const STATUS_COLORS = { Low: '#B23A2E', Medium: '#D98E2B', High: '#2E7D4F' };
const NUTRIENT_SHORT = { N: 'Nitrogen', P: 'Phosphorus', K: 'Potassium' };
const SERIES_A = '#6E9F5E';
const SERIES_B = '#D98E2B';
const SERIES_C = '#5B8DB8';

const SOIL_TEST_DISCLAIMER =
  'Screening / decision-support result. It does not replace a laboratory soil test. Get your soil tested (Soil Health Card) before applying fertilizer.';

/* ---------------------------- helpers ----------------------------- */
const pctOf = (obj, cls) => (obj && typeof obj === 'object' && typeof obj[cls] === 'number' ? obj[cls] : 0);

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function pointsBounds(points) {
  if (!points || !points.length) return null;
  const lats = points.map((p) => p.lat);
  const lons = points.map((p) => p.lon);
  return [[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]];
}

/* --------------------------- small UI bits ------------------------- */
function Info({ text }) {
  return (
    <span className="info" tabIndex={0}>
      i<span className="info-pop">{text}</span>
    </span>
  );
}

function ChartTitle({ title, info }) {
  return (
    <div className="chart-title">
      {title}
      {info && <Info text={info} />}
    </div>
  );
}

function Legend({ items }) {
  return (
    <div className="legend-inline">
      {items.map((it) => (
        <span key={it.name}><span className="sw" style={{ background: it.color }} />{it.name}</span>
      ))}
    </div>
  );
}

function Kpi({ label, value, sub, info, color }) {
  return (
    <div className="kpi">
      <span className="k-label">{label}{info && <Info text={info} />}</span>
      <span className="k-value" style={color ? { color } : undefined}>{value}</span>
      {sub && <span className="k-sub">{sub}</span>}
    </div>
  );
}

function NoData({ name }) {
  return <div className="panel"><p className="disclaimer">{name} not loaded.</p></div>;
}

/* ------------------------------ charts ----------------------------- */
function Donut({ data, centerTop, centerBottom }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const r = 70, C = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg viewBox="0 0 200 200" className="chart-svg" style={{ maxWidth: 240, margin: '0 auto' }}>
      <g transform="rotate(-90 100 100)">
        {data.map((d) => {
          const len = (d.value / total) * C;
          const el = (
            <circle key={d.label} cx="100" cy="100" r={r} fill="none" stroke={d.color} strokeWidth="26"
              strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-acc}>
              <title>{`${d.label}: ${d.value}%`}</title>
            </circle>
          );
          acc += len;
          return el;
        })}
      </g>
      <text x="100" y="98" textAnchor="middle" className="val" style={{ fontSize: 15 }}>{centerTop}</text>
      <text x="100" y="116" textAnchor="middle">{centerBottom}</text>
    </svg>
  );
}

// groups: [{label, values:[v|null,...]}], series: [{name,color}]
function GroupedBars({ groups, series, yMax, fmt = (v) => v.toFixed(2), ticks = 4, height = 240 }) {
  const W = 560, H = height, padL = 38, padB = 34, padT = 16, padR = 8;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const gw = innerW / groups.length;
  const bw = Math.min(36, (gw * 0.72) / series.length);
  const y = (v) => padT + innerH * (1 - v / yMax);
  const tickVals = Array.from({ length: ticks + 1 }, (_, i) => (yMax * i) / ticks);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
      {tickVals.map((t) => (
        <g key={t}>
          <line x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} stroke="rgba(169,194,163,.15)" />
          <text x={padL - 6} y={y(t) + 4} textAnchor="end">{fmt(t)}</text>
        </g>
      ))}
      {groups.map((g, gi) => {
        const x0 = padL + gi * gw + (gw - bw * series.length) / 2;
        return (
          <g key={g.label}>
            {g.values.map((v, si) => (
              v == null ? (
                <text key={si} x={x0 + si * bw + bw / 2} y={y(0) - 6} textAnchor="middle">n/a</text>
              ) : (
                <g key={si}>
                  <rect x={x0 + si * bw} y={y(v)} width={bw - 3} height={Math.max(0, y(0) - y(v))} rx="3" fill={series[si].color}>
                    <title>{`${g.label} — ${series[si].name}: ${fmt(v)}`}</title>
                  </rect>
                  <text x={x0 + si * bw + (bw - 3) / 2} y={y(v) - 4} textAnchor="middle" className="val">{fmt(v)}</text>
                </g>
              )
            ))}
            <text x={padL + gi * gw + gw / 2} y={H - 12} textAnchor="middle">{g.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

function HBars({ rows, color = '#4a8f52', suffix = '%' }) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  return (
    <div>
      {rows.map((r) => (
        <div className="hbar" key={r.label}>
          <span>{r.label}</span>
          <div className="track"><div className="fill" style={{ width: `${(r.value / max) * 100}%`, background: color }} /></div>
          <span style={{ textAlign: 'right' }}>{r.value}{suffix}</span>
        </div>
      ))}
    </div>
  );
}

function Heatmap({ labels, matrix }) {
  return (
    <div className="heat" style={{ gridTemplateColumns: `90px repeat(${labels.length}, 1fr)` }}>
      <div />
      {labels.map((l) => <div className="h" key={l}>{l}</div>)}
      {labels.map((rl, i) => (
        <HeatRow key={rl} label={rl} row={matrix[i]} diag={i} />
      ))}
    </div>
  );
}
function HeatRow({ label, row, diag }) {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
        <span className="dot" style={{ background: CLASS_COLORS[label] }} />{label}
      </div>
      {row.map((v, j) => (
        <div key={j} className="c" title={`${v}%`}
          style={{ background: `rgba(110,159,94,${0.06 + (v / 100) * 0.85})`, fontWeight: j === diag ? 700 : 400 }}>
          {v}%
        </div>
      ))}
    </>
  );
}

// rows: [{label, mean, std}] ; ref: {value,label}
function ErrorDots({ rows, ref }) {
  const W = 560, H = 230, padL = 44, padB = 34, padT = 16, padR = 12;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const lows = rows.map((r) => r.mean - r.std), highs = rows.map((r) => r.mean + r.std);
  let lo = Math.min(...lows, ref ? ref.value : Infinity), hi = Math.max(...highs, ref ? ref.value : -Infinity);
  lo = Math.floor((lo - 0.01) * 50) / 50; hi = Math.ceil((hi + 0.01) * 50) / 50;
  const y = (v) => padT + innerH * (1 - (v - lo) / (hi - lo));
  const x = (i) => padL + (innerW * (i + 0.5)) / rows.length;
  const ticks = [0, 1, 2, 3, 4].map((i) => lo + ((hi - lo) * i) / 4);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} stroke="rgba(169,194,163,.15)" />
          <text x={padL - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(2)}</text>
        </g>
      ))}
      {ref && (
        <g>
          <line x1={padL} x2={W - padR} y1={y(ref.value)} y2={y(ref.value)} stroke={SERIES_B} strokeDasharray="5 4" />
          <text x={padL + innerW / 2} y={y(ref.value) - 5} textAnchor="middle" style={{ fill: SERIES_B }}>{ref.label}</text>
        </g>
      )}
      {rows.map((r, i) => (
        <g key={r.label}>
          <line x1={x(i)} x2={x(i)} y1={y(r.mean - r.std)} y2={y(r.mean + r.std)} stroke={SERIES_A} strokeWidth="3" strokeLinecap="round" />
          <circle cx={x(i)} cy={y(r.mean)} r="6" fill={SERIES_A}>
            <title>{`${r.label}: ${r.mean.toFixed(3)} ± ${r.std.toFixed(3)}`}</title>
          </circle>
          <text x={x(i)} y={y(r.mean + r.std) - 8} textAnchor="middle" className="val">{r.mean.toFixed(3)}</text>
          <text x={x(i)} y={H - 12} textAnchor="middle">{r.label}</text>
        </g>
      ))}
    </svg>
  );
}

// bins: [{n, mean_confidence, accuracy}]
function Reliability({ bins }) {
  const S = 300, pad = 38;
  const vals = bins.flatMap((b) => [Number(b.mean_confidence), Number(b.accuracy)]);
  const lo = Math.floor(Math.min(...vals) * 10) / 10;
  const maxN = Math.max(...bins.map((b) => b.n));
  const sc = (v) => pad + ((v - lo) / (1 - lo)) * (S - pad - 12);
  const sy = (v) => S - pad - ((v - lo) / (1 - lo)) * (S - pad - 12);
  const ticks = [0, 1, 2, 3, 4].map((i) => lo + ((1 - lo) * i) / 4);
  return (
    <svg viewBox={`0 0 ${S} ${S}`} className="chart-svg" style={{ maxWidth: 360, margin: '0 auto' }}>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={sc(lo)} x2={sc(1)} y1={sy(t)} y2={sy(t)} stroke="rgba(169,194,163,.12)" />
          <line y1={sy(lo)} y2={sy(1)} x1={sc(t)} x2={sc(t)} stroke="rgba(169,194,163,.12)" />
          <text x={pad - 6} y={sy(t) + 4} textAnchor="end">{t.toFixed(1)}</text>
          <text x={sc(t)} y={S - pad + 16} textAnchor="middle">{t.toFixed(1)}</text>
        </g>
      ))}
      <line x1={sc(lo)} y1={sy(lo)} x2={sc(1)} y2={sy(1)} stroke="#e8f1e4" strokeDasharray="5 4" opacity=".6" />
      <polyline fill="none" stroke={SERIES_A} strokeWidth="2"
        points={bins.map((b) => `${sc(Number(b.mean_confidence))},${sy(Number(b.accuracy))}`).join(' ')} />
      {bins.map((b, i) => (
        <circle key={i} cx={sc(Number(b.mean_confidence))} cy={sy(Number(b.accuracy))}
          r={4 + 9 * Math.sqrt(b.n / maxN)} fill={SERIES_A} fillOpacity=".75" stroke="#fff" strokeWidth="1">
          <title>{`${b.bin}: n=${b.n}, confidence ${Number(b.mean_confidence).toFixed(3)}, accuracy ${Number(b.accuracy).toFixed(3)}`}</title>
        </circle>
      ))}
      <text x={S / 2} y={S - 4} textAnchor="middle">mean confidence</text>
      <text x="10" y={S / 2} transform={`rotate(-90 10 ${S / 2})`} textAnchor="middle">accuracy</text>
    </svg>
  );
}

// Where does the measured mean sit relative to the official limits?
function BandMeter({ low, high, mean, min, max }) {
  const top = Math.max(high * 1.5, max ?? 0, mean * 1.08);
  const p = (v) => `${Math.min(100, (v / top) * 100)}%`;
  return (
    <div className="band">
      <div style={{ width: p(low), background: STATUS_COLORS.Low }} title={`Low: below ${low}`} />
      <div style={{ width: `${((high - low) / top) * 100}%`, background: STATUS_COLORS.Medium }} title={`Medium: ${low}–${high}`} />
      <div style={{ flex: 1, background: STATUS_COLORS.High }} title={`High: above ${high}`} />
      {typeof min === 'number' && typeof max === 'number' && (
        <div style={{ position: 'absolute', left: p(min), width: `calc(${p(max)} - ${p(min)})`, top: 5, height: 6, background: 'rgba(255,255,255,.45)', borderRadius: 3 }} title={`Observed range ${min}–${max}`} />
      )}
      <div className="mark" style={{ left: p(mean) }}><b>{mean.toFixed(1)}</b></div>
      <span className="tick" style={{ left: p(low) }}>{low}</span>
      <span className="tick" style={{ left: p(high) }}>{high}</span>
    </div>
  );
}

function StackedStatus({ pct }) {
  return (
    <div className="stack">
      {['Low', 'Medium', 'High'].map((k) => {
        const v = pctOf(pct, k);
        return v > 0 ? (
          <div key={k} style={{ width: `${v}%`, background: STATUS_COLORS[k] }} title={`${k}: ${v}%`}>{v >= 8 ? `${k} ${v}%` : ''}</div>
        ) : null;
      })}
    </div>
  );
}

/* --------------------------- map helpers --------------------------- */
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => { if (bounds) map.fitBounds(bounds); }, [bounds, map]);
  return null;
}
function ClickCatcher({ onPick }) {
  useMapEvents({ click: (e) => onPick([e.latlng.lat, e.latlng.lng]) });
  return null;
}

/* =============================== APP =============================== */
const TABS = [
  ['overview', '📊', 'Overview'],
  ['models', '📈', 'Models'],
  ['validation', '🔍', 'Validation'],
  ['temporal', '📅', 'Temporal'],
  ['lab', '🧪', 'Lab Data (SHC)'],
  ['fertilizer', '🌾', 'Fertilizer'],
];

function App() {
  const [stats, setStats] = useState(null);
  const [temporalStats, setTemporalStats] = useState(null);
  const [npkData, setNpkData] = useState(null);
  const [modelEval, setModelEval] = useState(null);
  const [validationExtra, setValidationExtra] = useState(null);
  const [shc, setShc] = useState(null);

  const [tab, setTab] = useState('overview');
  const [farmerView, setFarmerView] = useState(false);
  const [activeLayer, setActiveLayer] = useState('fertility');
  const [showShcPoints, setShowShcPoints] = useState(false);
  const [shcNutrient, setShcNutrient] = useState('N');
  const [pickedPoint, setPickedPoint] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [selMode, setSelMode] = useState('dropdown');

  useEffect(() => { fetch('/stats.json').then((r) => r.json()).then(setStats); }, []);
  useEffect(() => { fetch('/temporal_summary.json').then((r) => r.json()).then(setTemporalStats).catch(() => setTemporalStats(null)); }, []);
  useEffect(() => { fetch('/npk_points.json').then((r) => r.json()).then(setNpkData).catch(() => setNpkData(null)); }, []);
  useEffect(() => { fetch('/model_evaluation.json').then((r) => r.json()).then(setModelEval).catch(() => setModelEval(null)); }, []);
  useEffect(() => { fetch('/validation_extra.json').then((r) => r.json()).then(setValidationExtra).catch(() => setValidationExtra(null)); }, []);
  useEffect(() => { fetch('/shc_status.json').then((r) => r.json()).then(setShc).catch(() => setShc(null)); }, []);

  if (!stats) return <div className="loading">Loading farm data...</div>;

  const bounds = stats.bounds;
  const overlayMap = {
    fertility: '/fertility_overlay.png', confidence: '/confidence_overlay.png', fertilizer: '/fertilizer_overlay.png',
    ndvi: '/ndvi_overlay.png', ndre: '/ndre_overlay.png', evi: '/evi_overlay.png', savi: '/savi_overlay.png', gndvi: '/gndvi_overlay.png',
    fertility_date1: '/fertility_date1_overlay.png', fertility_date2: '/fertility_date2_overlay.png', fertility_change: '/fertility_change_overlay.png',
    nitrogen: '/nitrogen_overlay.png', cec: '/cec_overlay.png',
  };
  const layerGroups = [
    ['Fertility', [['fertility', 'Fertility class'], ['confidence', 'Model confidence'], ['fertilizer', 'Fertilizer zones (illustrative)']]],
    ['Spectral indices', [['ndvi', 'NDVI'], ['ndre', 'NDRE'], ['evi', 'EVI'], ['savi', 'SAVI'], ['gndvi', 'GNDVI']]],
    ['Seasons', [['fertility_date1', 'Fertility — Date 1'], ['fertility_date2', 'Fertility — Date 2'], ['fertility_change', 'Class change']]],
    ['Reference soil layers (modelled — not lab data)', [['nitrogen', 'Nitrogen — SoilGrids (reference)'], ['cec', 'CEC — SoilGrids (not potassium)']]],
  ];
  const isFertilityStyleLayer = ['fertility', 'fertility_date1', 'fertility_date2'].includes(activeLayer);

  const dominantClass = Object.keys(stats.class_percent).reduce((a, b) => (stats.class_percent[a] > stats.class_percent[b] ? a : b));
  const shcPoints = shc?.points || [];
  const ptsBounds = (npkData && npkData.bounds) || pointsBounds(shcPoints);
  const readingsByKey = {};
  (npkData?.points || []).forEach((p) => { readingsByKey[`${p.lat},${p.lon}`] = p.num_readings; });

  const ShcMarkers = ({ nutrient }) => shcPoints.map((pt, i) => (
    <CircleMarker key={i} center={[pt.lat, pt.lon]} radius={7}
      pathOptions={{ color: '#fff', weight: 1, fillColor: STATUS_COLORS[pt[`${nutrient}_status`]] || '#888', fillOpacity: 0.92 }}>
      <Popup>
        <strong>{pt.village}</strong><br />
        N: {pt.N} kg/ha ({pt.N_status})<br />
        P: {pt.P} kg/ha ({pt.P_status})<br />
        K: {pt.K} kg/ha ({pt.K_status})
        {readingsByKey[`${pt.lat},${pt.lon}`] != null && <><br /><span style={{ fontSize: 11, color: '#888' }}>{readingsByKey[`${pt.lat},${pt.lon}`]} reading(s)</span></>}
      </Popup>
    </CircleMarker>
  ));

  const NutSeg = () => (
    <div className="seg">
      {['N', 'P', 'K'].map((n) => (
        <button key={n} className={shcNutrient === n ? 'on' : ''} onClick={() => setShcNutrient(n)}>{NUTRIENT_SHORT[n]}</button>
      ))}
    </div>
  );

  /* ---------------------------- OVERVIEW ---------------------------- */
  const Overview = () => (
    <>
      <div className="kpi-row">
        <Kpi label="Area mapped" value={`${stats.total_area_ha.toLocaleString()} ha`} />
        <Kpi label="Dominant class" value={dominantClass} color={CLASS_COLORS[dominantClass]}
          sub={`${stats.class_percent[dominantClass]}% of area`} />
        <Kpi label="Map confidence" value={`${(stats.mean_confidence * 100).toFixed(1)}%`}
          info="Average model confidence over mapped pixels. Confidence is not accuracy — accuracy is on the Validation tab." />
        <Kpi label="Lab-tested locations" value={shc ? shc.locations : npkData?.total_locations ?? '—'}
          sub={shc ? `${shc.readings} readings` : undefined}
          info="Real Soil Health Card laboratory measurements for Sakri (independent of the satellite model)." />
      </div>

      <div className="grid-map">
        <div className="panel">
          <div className="toolbar">
            <select value={activeLayer} onChange={(e) => setActiveLayer(e.target.value)}>
              {layerGroups.map(([g, items]) => (
                <optgroup key={g} label={g}>
                  {items.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </optgroup>
              ))}
            </select>
            {shc?.points && (
              <>
                <button className={`seg-btn ${showShcPoints ? 'active' : ''}`} onClick={() => setShowShcPoints(!showShcPoints)}
                  style={{ padding: '8px 12px', borderRadius: 10, border: '1px solid rgba(169,194,163,.25)', background: showShcPoints ? '#4a8f52' : '#0d1a12', color: '#e8f1e4', cursor: 'pointer', fontSize: 13 }}>
                  🧪 {showShcPoints ? 'Hide lab points' : 'Show lab points'}
                </button>
                <Info text="Lab points show locations with available soil-test readings. Colour = Low / Medium / High for the nutrient you pick." />
              </>
            )}
            {showShcPoints && NutSeg()}
            {['fertility_change', 'nitrogen', 'cec', 'fertilizer'].includes(activeLayer) && (
              <Info text={
                activeLayer === 'fertility_change' ? 'Red = the predicted class changed between dates. This mostly reflects crop growth stage, not a real change in soil.'
                : activeLayer === 'fertilizer' ? 'Illustrative heuristic zones — not validated against lab data.'
                : activeLayer === 'nitrogen' ? 'SoilGrids is an auxiliary gridded soil-property reference layer. It is not the same as the project\'s laboratory soil-test observations. It is a modelled total-nitrogen estimate (g/kg), while the lab values are available nitrogen (kg/ha) — the two are different quantities and cannot be compared directly.'
                : 'CEC (Cation Exchange Capacity) describes the soil\'s capacity to retain exchangeable cations and is not a direct measurement of potassium concentration. Shown as a SoilGrids reference layer.'} />
            )}
          </div>
          <div className="map-wrap">
            <MapContainer center={stats.center} bounds={bounds} zoomControl={false} style={{ height: '520px', width: '100%', borderRadius: '12px' }}>
              <ZoomControl position="bottomright" />
              <ImageOverlay url={overlayMap[activeLayer]} bounds={bounds} />
              <FitBounds bounds={showShcPoints && ptsBounds ? ptsBounds : bounds} />
              {showShcPoints && ShcMarkers({ nutrient: shcNutrient })}
            </MapContainer>
            {(isFertilityStyleLayer || showShcPoints) && (
              <div className="map-chip">
                {isFertilityStyleLayer && Object.entries(CLASS_COLORS).map(([c, col]) => (
                  <div className="row" key={c}><span className="dot" style={{ background: col }} />{c}</div>
                ))}
                {showShcPoints && (
                  <>
                    <div style={{ fontWeight: 600, marginTop: isFertilityStyleLayer ? 4 : 0 }}>{NUTRIENT_SHORT[shcNutrient]} (lab)</div>
                    {Object.entries(STATUS_COLORS).map(([c, col]) => (
                      <div className="row" key={c}><span className="dot" style={{ background: col }} />{c}</div>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <ChartTitle title="Fertility mix" info="Predicted fertility classes from the satellite model. These are proxy labels, not laboratory fertility." />
          <Donut
            data={Object.entries(stats.class_percent).map(([label, value]) => ({ label, value, color: CLASS_COLORS[label] }))}
            centerTop={dominantClass} centerBottom={`${stats.class_percent[dominantClass]}%`} />
          <Legend items={Object.entries(stats.class_percent).map(([c, v]) => ({ name: `${c} ${v}%`, color: CLASS_COLORS[c] }))} />
        </div>
      </div>
    </>
  );

  /* ----------------------------- MODELS ----------------------------- */
  const Models = () => {
    if (!modelEval) return <NoData name="model_evaluation.json" />;
    const mc = modelEval.model_comparison;
    const ht = modelEval.hyperparameter_tuning;
    return (
      <>
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="Model comparison (Macro-F1)"
              info="Random split can be optimistic because neighbouring pixels are similar. Spatial-block holds out whole regions. K-Means is unsupervised, so its F1 is not comparable to the supervised models." />
            <GroupedBars yMax={1}
              groups={mc.map((m) => ({ label: m.model.split(' (')[0], values: [m.random_split_f1, m.spatial_block_f1] }))}
              series={[{ name: 'Random split', color: SERIES_A }, { name: 'Spatial block', color: SERIES_B }]} />
            <Legend items={[{ name: 'Random split', color: SERIES_A }, { name: 'Spatial block', color: SERIES_B }]} />
          </div>
          <div className="panel">
            <ChartTitle title="Hyperparameter tuning" info={ht.conclusion} />
            <GroupedBars yMax={1}
              groups={[{ label: 'Random split', values: [ht.baseline_random_split_f1, ht.tuned_random_split_f1] },
                { label: 'Spatial block', values: [ht.baseline_spatial_block_f1, ht.tuned_spatial_block_f1] }]}
              series={[{ name: 'Baseline', color: SERIES_C }, { name: 'Tuned', color: SERIES_A }]} fmt={(v) => v.toFixed(4)} />
            <Legend items={[{ name: 'Baseline', color: SERIES_C }, { name: 'Tuned', color: SERIES_A }]} />
          </div>
        </div>
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="What the model uses (permutation importance)"
              info="How much the score drops when a feature is shuffled. It describes the model, not soil chemistry." />
            <HBars rows={modelEval.permutation_importance.map((f) => ({ label: f.feature, value: f.importance_pct }))} />
          </div>
          <div className="panel">
            <ChartTitle title="Confusion matrix (row %)" info="Each row sums to 100%. Diagonal = correct predictions." />
            <Heatmap labels={modelEval.confusion_matrix.labels} matrix={modelEval.confusion_matrix.row_normalized_pct} />
          </div>
        </div>
      </>
    );
  };

  /* --------------------------- VALIDATION --------------------------- */
  const Validation = () => {
    if (!validationExtra) return <NoData name="validation_extra.json" />;
    const cal = validationExtra.calibration;
    const rf = modelEval?.model_comparison?.find((m) => m.model.startsWith('Random Forest'));
    return (
      <>
        <div className="kpi-row">
          <Kpi label="ECE" value={Number(cal.ece).toFixed(4)} info="Expected calibration error: gap between stated confidence and observed accuracy. Lower is better. Measured on in-distribution test data against proxy labels." />
          <Kpi label="Test accuracy" value={`${(cal.overall_accuracy * 100).toFixed(1)}%`} info="Against proxy labels, on held-out test pixels. Not agreement with laboratory soil tests." />
          <Kpi label="Test mean confidence" value={`${(cal.mean_confidence * 100).toFixed(1)}%`} />
          <Kpi label="Map mean confidence" value={`${(stats.mean_confidence * 100).toFixed(1)}%`} info="Different quantity: average over the mapped area, not over the test set." />
        </div>
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="Spatial-block sensitivity"
              info="Macro-F1 depends on how the study area is cut into blocks. Bars show mean ± std over repeated hold-outs. The dashed line is the single hold-out reported on the Models tab." />
            {validationExtra.spatial_sensitivity ? (
              <ErrorDots
                rows={validationExtra.spatial_sensitivity.map((r) => ({ label: r.grid, mean: Number(r.mean_f1), std: Number(r.std_f1) }))}
                ref={rf && typeof rf.spatial_block_f1 === 'number' ? { value: rf.spatial_block_f1, label: 'single hold-out' } : null} />
            ) : null}
          </div>
          <div className="panel">
            <ChartTitle title="Reliability diagram"
              info="Points on the dashed diagonal = confidence equals accuracy. Dot size = number of pixels. Calibration here does not guarantee anything on new dates or areas." />
            <Reliability bins={cal.bins} />
          </div>
        </div>
      </>
    );
  };

  /* ---------------------------- TEMPORAL ---------------------------- */
  const Temporal = () => {
    if (!temporalStats) return <NoData name="temporal_summary.json" />;
    const dInfo = `Date 1: ${temporalStats.date1_range}. Date 2: ${temporalStats.date2_range}.`;
    const legend = [{ name: 'Date 1', color: SERIES_A }, { name: 'Date 2', color: SERIES_B }];
    return (
      <>
        <div className="kpi-row">
          <Kpi label="Pixels that changed class" value={`${temporalStats.pct_pixels_changed_class}%`} info={temporalStats.important_caveat} />
        </div>
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="Vegetation indices by date" info={dInfo} />
            <GroupedBars yMax={1}
              groups={temporalStats.index_comparison.map((r) => ({ label: r.index, values: [r.date1_mean, r.date2_mean] }))}
              series={legend} />
            <Legend items={legend} />
            <div className="legend-inline">
              {temporalStats.index_comparison.map((r) => (
                <span key={r.index} style={{ color: r.change < 0 ? '#e0705f' : '#8fc47f' }}>{r.index} {r.change_pct > 0 ? '+' : ''}{r.change_pct}%</span>
              ))}
            </div>
          </div>
          <div className="panel">
            <ChartTitle title="Fertility class share by date" info="Shifts mostly reflect crop growth stage at each acquisition date." />
            <GroupedBars yMax={100} ticks={4} fmt={(v) => `${Math.round(v * 10) / 10}`}
              groups={temporalStats.fertility_zone_shift.map((r) => ({ label: r.class, values: [r.date1_pct, r.date2_pct] }))}
              series={legend} />
            <Legend items={legend.map((l) => ({ ...l, name: `${l.name} (% of area)` }))} />
          </div>
        </div>
      </>
    );
  };

  /* ------------------------------- LAB ------------------------------ */
  const Lab = () => {
    if (!shc?.summary) return <NoData name="shc_status.json" />;
    return (
      <>
        <div className="callout">
          Measured Soil Health Card values for Sakri. These are laboratory results, not satellite predictions — and the satellite features did not predict them (see paper).
        </div>
        <div className="kpi-row">
          <Kpi label="Locations" value={shc.locations} info="Locations = distinct soil-testing locations. A location can have more than one reading." />
          <Kpi label="Readings" value={shc.readings} info="Readings = individual laboratory nutrient observations across all locations." />
        </div>
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="Mean level vs official limits (kg/ha)"
              info={`Bar: Low / Medium / High bands from the SHC limits. White marker: mean. Faint line: observed range. Source: ${shc.source}`} />
            {['N', 'P', 'K'].map((n) => {
              const lim = shc.limits_kg_ha?.[n], s = shc.summary[n];
              if (!lim || typeof s?.mean !== 'number') return null;
              return (
                <div className="nut-card" key={n}>
                  <h4>{NUTRIENT_SHORT[n]}</h4>
                  <BandMeter low={lim.low_below} high={lim.high_above} mean={s.mean} min={s.min} max={s.max} />
                  <StackedStatus pct={s.locations_pct} />
                </div>
              );
            })}
            <Legend items={Object.entries(STATUS_COLORS).map(([name, color]) => ({ name, color }))} />
            <div className="legend-inline">Stacked bar = share of sampled locations</div>
          </div>
          <div className="panel">
            <div className="toolbar">{NutSeg()}</div>
            <MapContainer center={stats.center} bounds={ptsBounds || bounds} zoomControl={false} style={{ height: '520px', width: '100%', borderRadius: '12px' }}>
              <ZoomControl position="bottomright" />
              <FitBounds bounds={ptsBounds || bounds} />
              {ShcMarkers({ nutrient: shcNutrient })}
            </MapContainer>
            <Legend items={Object.entries(STATUS_COLORS).map(([name, color]) => ({ name: `${name} ${NUTRIENT_SHORT[shcNutrient]}`, color }))} />
          </div>
        </div>
      </>
    );
  };

  /* ---------------------------- FERTILIZER -------------------------- */
  const Fertilizer = () => {
    const rates = stats.fertilizer_rates;
    const classes = Object.keys(rates);
    const yMax = Math.max(...classes.flatMap((c) => [rates[c].N, rates[c].P, rates[c].K])) * 1.15;
    const tot = stats.fertilizer_totals;
    return (
      <>
        <div className="banner">⚠️ Illustrative heuristic — NOT validated against laboratory data. Rates are not yet verified against current MPKV / Maharashtra recommendations.</div>
        {shc?.summary && (
          <div className="callout">
            What the lab data says: {pctOf(shc.summary.N?.locations_pct, 'Low')}% of Sakri locations are Low in nitrogen and {pctOf(shc.summary.K?.locations_pct, 'High')}% are High in potassium — a zone table cannot capture that.
          </div>
        )}
        <div className="grid-2">
          <div className="panel">
            <ChartTitle title="Cotton rate by predicted zone (kg/ha)" info="Scaled from a generic cotton recommendation by predicted fertility class. Illustrative only." />
            <GroupedBars yMax={yMax} fmt={(v) => `${Math.round(v)}`}
              groups={classes.map((c) => ({ label: c, values: [rates[c].N, rates[c].P, rates[c].K] }))}
              series={[{ name: 'N', color: SERIES_A }, { name: 'P', color: SERIES_B }, { name: 'K', color: SERIES_C }]} />
            <Legend items={[{ name: 'N', color: SERIES_A }, { name: 'P', color: SERIES_B }, { name: 'K', color: SERIES_C }]} />
          </div>
          {tot && (
            <div className="panel">
              <ChartTitle title="Total nitrogen: zone-based vs uniform (kg)" info="Both totals come from the same illustrative heuristic over the mapped area." />
              <HBars suffix=" kg" color={SERIES_A}
                rows={[{ label: 'Zone-based', value: Math.round(tot.variable_rate_N_kg) }, { label: 'Uniform', value: Math.round(tot.uniform_N_kg) }]} />
              <div className="legend-inline">Difference: {tot.difference_pct}%</div>
            </div>
          )}
        </div>
      </>
    );
  };

  /* ---------------------------- FARMER VIEW ------------------------- */
  const FARMER_MEANING = {
    N: { Low: 'Often needs nitrogen fertilizer.', Medium: 'Moderate nitrogen.', High: 'Nitrogen is sufficient.' },
    P: { Low: 'May need phosphorus.', Medium: 'Phosphorus is moderate.', High: 'Phosphorus is sufficient.' },
    K: { Low: 'May need potassium.', Medium: 'Potassium is moderate.', High: 'Potassium is sufficient.' },
  };
  const statusIcon = { Low: '🔴', Medium: '🟡', High: '🟢' };

  // Dropdown options come straight from shc_status.json points (no invented locations)
  const villageCount = {};
  shcPoints.forEach((p) => { villageCount[p.village] = (villageCount[p.village] || 0) + 1; });
  const villageSeen = {};
  const locOptions = shcPoints
    .map((p, i) => {
      villageSeen[p.village] = (villageSeen[p.village] || 0) + 1;
      const n = readingsByKey[`${p.lat},${p.lon}`];
      const label = `${p.village}${villageCount[p.village] > 1 ? ` — site ${villageSeen[p.village]}` : ''}${n != null ? ` (${n} reading${n === 1 ? '' : 's'})` : ''}`;
      return { i, label, village: p.village };
    })
    .sort((x, y) => x.label.localeCompare(y.label));
  const selected = selectedIdx != null ? shcPoints[selectedIdx] : null;
  const selReadings = selected ? readingsByKey[`${selected.lat},${selected.lon}`] : null;
  const selDist = selected && selMode === 'map' && pickedPoint ? haversineKm(pickedPoint[0], pickedPoint[1], selected.lat, selected.lon) : null;

  const pickOnMap = (latlng) => {
    if (!shcPoints.length) return;
    let best = 0, bd = Infinity;
    shcPoints.forEach((p, i) => {
      const d = haversineKm(latlng[0], latlng[1], p.lat, p.lon);
      if (d < bd) { bd = d; best = i; }
    });
    setPickedPoint(latlng);
    setSelectedIdx(best);
    setSelMode('map');
  };

  const Farmer = () => (
    <>
      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <label style={{ fontSize: 13, color: '#a9c2a3' }}>Select lab-tested location</label>
          <select value={selectedIdx ?? ''} onChange={(e) => { setSelectedIdx(e.target.value === '' ? null : Number(e.target.value)); setSelMode('dropdown'); setPickedPoint(null); }}>
            <option value="">— choose a location —</option>
            {locOptions.map((o) => <option key={o.i} value={o.i}>{o.label}</option>)}
          </select>
          <span className="disclaimer" style={{ margin: 0 }}>or click the map to find the nearest one</span>
        </div>
      </div>

      {selected ? (
        <>
          <div className="tab-title">
            <h2>📍 {selMode === 'map' ? 'Nearest available lab-tested location' : 'Selected lab-tested location'}: {selected.village}</h2>
            <span className="disclaimer">
              {selDist != null ? `${selDist.toFixed(1)} km from the point you clicked` : ''}
              {selReadings != null ? `${selDist != null ? ' · ' : ''}${selReadings} reading(s) at this location` : ''}
            </span>
          </div>
          <div className="farmer-grid">
            {['N', 'P', 'K'].map((n) => {
              const st = selected[`${n}_status`];
              return (
                <div className="status-card" key={n}>
                  <div className="big" style={{ background: `${STATUS_COLORS[st]}33`, border: `3px solid ${STATUS_COLORS[st]}` }}>{statusIcon[st]}</div>
                  <div className="nm">{NUTRIENT_SHORT[n]}</div>
                  <div className="st" style={{ color: STATUS_COLORS[st] }}>{st}</div>
                  <div className="ml">{FARMER_MEANING[n][st]}</div>
                  <div className="ml" style={{ marginTop: 6 }}>Lab value: {selected[n]} kg/ha</div>
                </div>
              );
            })}
          </div>
          <div className="callout">
            These nutrient statuses are based on available laboratory soil-test observations for the selected location. They should not be interpreted as laboratory measurements for the entire surrounding region.
          </div>
        </>
      ) : (
        <div className="callout">Choose a lab-tested location above, or click a dot on the map, to see its nutrient status.</div>
      )}

      <div className="panel">
        <div className="map-wrap">
          <MapContainer center={stats.center} bounds={ptsBounds || bounds} zoomControl={false} style={{ height: '460px', width: '100%', borderRadius: '12px' }}>
            <ZoomControl position="bottomright" />
            <FitBounds bounds={ptsBounds || bounds} />
            <ImageOverlay url={overlayMap.fertility} bounds={bounds} />
            <ClickCatcher onPick={pickOnMap} />
            {shcPoints.map((pt, i) => (
              <CircleMarker key={i} center={[pt.lat, pt.lon]} radius={i === selectedIdx ? 11 : 6}
                pathOptions={{ color: i === selectedIdx ? '#fff' : '#ffffffaa', weight: i === selectedIdx ? 3 : 1, fillColor: STATUS_COLORS[pt.N_status] || '#888', fillOpacity: 0.92, bubblingMouseEvents: false }}
                eventHandlers={{ click: () => { setSelectedIdx(i); setSelMode('dropdown'); setPickedPoint(null); } }}>
                <Popup>{pt.village}</Popup>
              </CircleMarker>
            ))}
          </MapContainer>
          <div className="map-chip">
            <div style={{ fontWeight: 600 }}>Dots: nitrogen status (lab)</div>
            {Object.entries(STATUS_COLORS).map(([c, col]) => (
              <div className="row" key={c}><span className="dot" style={{ background: col }} />{c}</div>
            ))}
            <div style={{ fontWeight: 600, marginTop: 4 }}>Background: satellite fertility</div>
          </div>
        </div>
        <div className="legend-inline">Dots are lab-tested locations only — not every field in Sakri Tehsil.</div>
      </div>
    </>
  );

  /* ------------------------------ RENDER ----------------------------- */
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">🌱</div>
          <span>Soil<b>Sight</b></span>
        </div>
        <nav>
          {TABS.map(([k, icon, label]) => (
            <a key={k} className={`nav-item ${!farmerView && tab === k ? 'active' : ''}`}
              onClick={() => { setFarmerView(false); setTab(k); window.scrollTo({ top: 0 }); }}>{icon} {label}</a>
          ))}
          <a className="nav-item" onClick={() => alert('SoilSight — satellite-based soil fertility screening and Soil Health Card nutrient status for Sakri Tehsil, Dhule, Maharashtra.')}>ℹ️ About</a>
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>{farmerView ? 'My Soil' : TABS.find((t) => t[0] === tab)[2]}</h1>
            <p>Sakri Tehsil, Dhule</p>
          </div>
          <div className="layer-toggle">
            <button className={!farmerView ? 'active' : ''} onClick={() => setFarmerView(false)}>👩‍🔬 Expert View</button>
            <button className={farmerView ? 'active' : ''} onClick={() => setFarmerView(true)}>👨‍🌾 Farmer View</button>
          </div>
        </header>

        {farmerView ? Farmer() : (
          <>
            {tab === 'overview' && Overview()}
            {tab === 'models' && Models()}
            {tab === 'validation' && Validation()}
            {tab === 'temporal' && Temporal()}
            {tab === 'lab' && Lab()}
            {tab === 'fertilizer' && Fertilizer()}
          </>
        )}

        <div className="foot-banner">⚠️ {SOIL_TEST_DISCLAIMER}</div>
      </main>
    </div>
  );
}

export default App;