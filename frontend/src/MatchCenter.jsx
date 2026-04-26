import React, { useState, useEffect, useRef } from 'react';
import './MatchCenter.css';

const WS_BASE = 'ws://localhost:8000/ws/v1';
const LOCAL_COLOR = '#22c55e';
const VISIT_COLOR = '#a78bfa';

function getIniciales(nombre) {
  return nombre.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

function EventIcon({ tipo }) {
  const t = (tipo || '').toLowerCase();
  if (t === 'gol') return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="7" stroke="#fbbf24" strokeWidth="1.5"/>
      <path d="M8 4l1.2 2.4L12 7l-2 1.9.47 2.7L8 10.4l-2.47 1.2L6 8.9 4 7l2.8-.6z" fill="#fbbf24"/>
    </svg>
  );
  if (t === 'parada') return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="4" width="12" height="8" rx="1" stroke="#60a5fa" strokeWidth="1.5"/>
      <path d="M8 4v8M2 8h12" stroke="#60a5fa" strokeWidth="1"/>
    </svg>
  );
  if (['tarjeta_roja', 'falta', 'tarjeta_amarilla'].includes(t)) return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="7" stroke="#f87171" strokeWidth="1.5"/>
      <path d="M5 5l6 6M11 5l-6 6" stroke="#f87171" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M3 8h10M9 4l4 4-4 4" stroke="#a3e635" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function eventColor(tipo) {
  const t = (tipo || '').toLowerCase();
  if (t === 'gol') return '#fbbf24';
  if (t === 'parada') return '#60a5fa';
  if (['tarjeta_roja', 'falta', 'tarjeta_amarilla'].includes(t)) return '#f87171';
  return '#a3e635';
}

function TeamBadge({ nombre, color }) {
  return (
    <div style={{
      width: 56, height: 56, borderRadius: '50%',
      background: `${color}22`,
      border: `2px solid ${color}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <span style={{ fontFamily: 'Barlow Condensed', fontWeight: 800, fontSize: 18, color, letterSpacing: '0.05em' }}>
        {nombre ? getIniciales(nombre) : '--'}
      </span>
    </div>
  );
}

function PosesionBar({ posLocal, localColor, visitColor, localNombre, visitNombre }) {
  return (
    <div className="mc-posesion-wrap">
      <div className="mc-posesion-row">
        <span className="mc-posesion-pct" style={{ color: localColor, textAlign: 'right' }}>{posLocal}%</span>
        <div className="mc-posesion-track">
          <div
            className="mc-posesion-fill"
            style={{
              width: posLocal + '%',
              background: `linear-gradient(90deg, ${localColor}, ${localColor}cc)`,
              boxShadow: `0 0 8px ${localColor}88`,
            }}
          />
        </div>
        <span className="mc-posesion-pct" style={{ color: visitColor }}>{100 - posLocal}%</span>
      </div>
      <div className="mc-posesion-labels">
        <span className="mc-posesion-label">{localNombre}</span>
        <span className="mc-posesion-label" style={{ letterSpacing: '0.1em', textTransform: 'uppercase', fontSize: 10 }}>Posesión</span>
        <span className="mc-posesion-label" style={{ textAlign: 'right' }}>{visitNombre}</span>
      </div>
    </div>
  );
}

function Timeline({ minutoActual }) {
  const pct = Math.min((minutoActual / 90) * 100, 100);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ position: 'relative', height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'visible' }}>
        <div style={{ position: 'absolute', left: '50%', top: -3, width: 1, height: 10, background: 'rgba(255,255,255,0.15)' }} />
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: pct + '%',
          background: 'linear-gradient(90deg,#22c55e,#a3e635)',
          borderRadius: 2,
          transition: 'width 0.8s linear',
          boxShadow: '0 0 10px #22c55e66',
        }} />
        <div style={{
          position: 'absolute', top: '50%',
          left: `calc(${pct}% - 7px)`,
          transform: 'translateY(-50%)',
          width: 14, height: 14, borderRadius: '50%',
          background: 'white', border: '2px solid #22c55e',
          transition: 'left 0.8s linear',
          boxShadow: '0 0 8px #22c55e',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', fontFamily: 'Barlow Condensed', letterSpacing: '0.06em' }}>
        <span>0'</span><span>45'</span><span>90'</span>
      </div>
    </div>
  );
}

function EventItem({ ev, isLocal, animate }) {
  const color = isLocal ? LOCAL_COLOR : VISIT_COLOR;
  const tipo = (ev.tipo || '').toLowerCase();
  const isGol = tipo === 'gol';

  return (
    <div
      className={`mc-event-item ${animate ? (isLocal ? 'slide-left' : 'slide-right') : ''}`}
      style={{
        background: isGol
          ? `linear-gradient(135deg, ${color}22, ${color}08)`
          : 'rgba(255,255,255,0.035)',
        border: isGol ? `1px solid ${color}55` : '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {isGol && (
        <div style={{
          position: 'absolute', inset: 0,
          background: `radial-gradient(ellipse at ${isLocal ? 'left' : 'right'}, ${color}18, transparent 70%)`,
          pointerEvents: 'none',
        }} />
      )}
      <EventIcon tipo={ev.tipo} />
      <span className="mc-event-desc" style={{ color: eventColor(ev.tipo) }}>{ev.descripcion}</span>
    </div>
  );
}

function MatchCenter({ onBack, matchData }) {
  const { id: simId, local, visitante } = matchData;
  const [minuto, setMinuto] = useState(0);
  const [golesL, setGolesL] = useState(0);
  const [golesV, setGolesV] = useState(0);
  const [eventos, setEventos] = useState([]);
  const [posesion, setPosesion] = useState([50, 50]);
  const [estado, setEstado] = useState('conectando');
  const [goalFlash, setGoalFlash] = useState(false);
  const [lastGolIsLocal, setLastGolIsLocal] = useState(null);
  const [scoreAnim, setScoreAnim] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = new WebSocket(`${WS_BASE}/match/${simId}`);
    socketRef.current = socket;

    socket.onopen = () => setEstado('en_vivo');

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.tipo === 'TICK') {
        const { minuto: min, marcador, posesion: pos } = msg.data;
        setMinuto(min);
        if (pos) setPosesion(pos);
        if (marcador) {
          setGolesL(marcador[0]);
          setGolesV(marcador[1]);
        }
        return;
      }

      if (msg.tipo !== 'EVENTO') return;
      const { minuto: min, tipo_evento, descripcion, marcador, posesion: pos, equipo_id } = msg.data;

      setMinuto(min);
      if (pos) setPosesion(pos);

      const isLocal = equipo_id === local?.id;

      if (tipo_evento === 'GOL') {
        setGolesL(marcador[0]);
        setGolesV(marcador[1]);
        setGoalFlash(true);
        setScoreAnim(true);
        setLastGolIsLocal(isLocal);
        setTimeout(() => { setGoalFlash(false); setScoreAnim(false); }, 1500);
      }

      setEventos(prev => [{
        id: Date.now(),
        minuto: min,
        tipo: tipo_evento,
        descripcion,
        isLocal,
      }, ...prev].slice(0, 30));

      if (tipo_evento === 'FINAL') setEstado('finalizado');
    };

    socket.onclose = () => setEstado('finalizado');

    return () => { if (socketRef.current) socketRef.current.close(); };
  }, [local?.id]);

  const goalColor = lastGolIsLocal ? LOCAL_COLOR : VISIT_COLOR;

  return (
    <div
      className="match-center-wrap"
      style={{
        background: goalFlash
          ? `radial-gradient(ellipse 60% 40% at 50% 20%, ${goalColor}18, transparent 70%)`
          : 'transparent',
      }}
    >
      {/* Header */}
      <div className="mc-header">
        <button className="back-btn-match" onClick={onBack}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Volver
        </button>
        <div style={{ fontFamily: 'Barlow Condensed', letterSpacing: '0.25em', fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase' }}>
          Motor de Fútbol
        </div>
        <div style={{ width: 70 }} />
      </div>

      {/* Scoreboard */}
      <div
        className="mc-scoreboard"
        style={{ boxShadow: goalFlash ? `0 0 60px 4px ${goalColor}33` : 'none' }}
      >
        <div className="mc-scoreboard-lines" />

        <div className="mc-team-row">
          {/* Local */}
          <div className="mc-team-local">
            <TeamBadge nombre={local?.nombre} color={LOCAL_COLOR} />
            <span className="mc-team-name" style={{ textAlign: 'right' }}>{local?.nombre}</span>
          </div>

          {/* Score */}
          <div className="mc-score-center">
            <div className="mc-score-numbers">
              <span
                className="mc-score-digit"
                style={{ animation: scoreAnim && lastGolIsLocal ? 'scorePop 0.6s ease forwards' : 'none' }}
              >
                {golesL}
              </span>
              <span className="mc-score-sep">—</span>
              <span
                className="mc-score-digit"
                style={{ animation: scoreAnim && lastGolIsLocal === false ? 'scorePop 0.6s ease forwards' : 'none' }}
              >
                {golesV}
              </span>
            </div>

            <div className="mc-status-row">
              {estado === 'en_vivo' && <span className="mc-live-dot" />}
              {estado === 'finalizado' && <span className="mc-fin-dot" />}
              <span
                className="mc-status-time"
                style={{ color: estado === 'en_vivo' ? '#ef4444' : 'var(--dimmed)' }}
              >
                {estado === 'conectando' ? '···' : estado === 'finalizado' ? 'FIN' : `${minuto}'`}
              </span>
              {estado === 'en_vivo' && <span className="mc-status-live">EN VIVO</span>}
            </div>
          </div>

          {/* Visitante */}
          <div className="mc-team-visit">
            <TeamBadge nombre={visitante?.nombre} color={VISIT_COLOR} />
            <span className="mc-team-name">{visitante?.nombre}</span>
          </div>
        </div>

        <PosesionBar
          posLocal={posesion[0]}
          localColor={LOCAL_COLOR}
          visitColor={VISIT_COLOR}
          localNombre={local?.nombre}
          visitNombre={visitante?.nombre}
        />
      </div>

      {/* Timeline */}
      <div className="mc-timeline-wrap">
        <Timeline minutoActual={minuto} />
      </div>

      {/* Event Feed */}
      {eventos.length > 0 && (
        <div>
          <div className="mc-feed-title">Eventos del partido</div>
          <div
            className="hide-scroll"
            style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 420, overflowY: 'auto', paddingRight: 4, scrollbarWidth: 'none' }}
          >
            {eventos.map((ev, i) => (
              <div key={ev.id} className="mc-event-row">
                <div>{ev.isLocal && <EventItem ev={ev} isLocal={true} animate={i === 0} />}</div>
                <div className="mc-event-min">{ev.minuto}'</div>
                <div>{!ev.isLocal && <EventItem ev={ev} isLocal={false} animate={i === 0} />}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default MatchCenter;
