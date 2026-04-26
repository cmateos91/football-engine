import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Activity, ChevronLeft, Play, AlertCircle } from 'lucide-react';
import './MatchCenter.css';

const WS_BASE = 'ws://localhost:8000/ws/v1';

const EVENT_ICONS = {
  GOL: '⚽',
  TIRO: '🚀',
  TARJETA_AMARILLA: '🟨',
  TARJETA_ROJA: '🟥',
  FALTA: '⚠️',
  INICIO: '🏁',
  FINAL: '🔚',
  PARADA: '🧤',
  RECUPERACION: '🔄',
  PENALTI: '🎯',
  TIRO_LIBRE: '🧱',
  CORNER: '🚩',
  CONTRAATAQUE: '⚡',
  CENTRO: '🏹',
  DUELO_AEREO: '🪂'
};

function MatchCenter({ onBack, local, visitante }) {
  const [minuto, setMinuto] = useState(0);
  const [golesL, setGolesL] = useState(0);
  const [golesV, setGolesV] = useState(0);
  const [eventos, setEventos] = useState([]);
  const [posesion, setPosesion] = useState([50, 50]);
  const [estado, setEstado] = useState('conectando');
  const [goalFlash, setGoalFlash] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Iniciar conexión WebSocket
    const simId = 'test-match'; // En producción esto vendría del POST /simulations/match
    const socket = new WebSocket(`${WS_BASE}/match/${simId}`);
    socketRef.current = socket;

    socket.onopen = () => {
      setEstado('en_vivo');
      console.log("WebSocket Connected");
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.tipo === 'EVENTO') {
        const { minuto, tipo_evento, descripcion, marcador, posesion } = msg.data;
        
        setMinuto(minuto);
        setPosesion(posesion);
        
        // Si hay gol, activar animación
        if (tipo_evento === 'GOL') {
          setGoalFlash(true);
          setTimeout(() => setGoalFlash(false), 2000);
          setGolesL(marcador[0]);
          setGolesV(marcador[1]);
        }

        const newEvent = {
          id: Date.now(),
          minuto,
          tipo: tipo_evento,
          descripcion,
          isLocal: msg.data.equipo_id === 154 // TODO: Usar ID real del local
        };

        setEventos(prev => [newEvent, ...prev]);

        if (tipo_evento === 'FINAL') {
          setEstado('finalizado');
        }
      }
    };

    socket.onclose = () => {
      setEstado('finalizado');
      console.log("WebSocket Closed");
    };

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  return (
    <div className={`match-center-view ${goalFlash ? 'goal-flash' : ''}`}>
      <header className="match-header glass">
        <button className="back-btn-match" onClick={onBack}>
          <ChevronLeft size={20} /> Volver
        </button>
        <div className="match-title">
          <Trophy size={18} />
          <span>LALIGA EA SPORTS</span>
        </div>
      </header>

      <div className="scoreboard-container glass">
        <div className="scoreboard-layout">
          {/* Local */}
          <div className="team-score-info local">
            <div className="team-badge-large">{local.nombre_corto}</div>
            <h2>{local.nombre}</h2>
          </div>

          {/* Score */}
          <div className="score-main">
            <div className="score-numbers">
              <motion.span 
                key={golesL}
                initial={{ scale: 1 }}
                animate={goalFlash ? { scale: [1, 1.3, 1], color: ['#fff', '#fbbf24', '#fff'] } : {}}
                className="score-digit"
              >
                {golesL}
              </motion.span>
              <span className="score-divider">—</span>
              <motion.span 
                key={golesV}
                initial={{ scale: 1 }}
                animate={goalFlash ? { scale: [1, 1.3, 1], color: ['#fff', '#fbbf24', '#fff'] } : {}}
                className="score-digit"
              >
                {golesV}
              </motion.span>
            </div>
            <div className="match-status-pill">
              {estado === 'en_vivo' && <span className="live-dot"></span>}
              <span className="match-time">{estado === 'finalizado' ? 'FINAL' : `${minuto}'`}</span>
            </div>
          </div>

          {/* Visitante */}
          <div className="team-score-info visitante">
            <div className="team-badge-large">{visitante.nombre_corto}</div>
            <h2>{visitante.nombre}</h2>
          </div>
        </div>

        {/* Possession Bar */}
        <div className="possession-stats">
          <div className="possession-labels">
            <span>{posesion[0]}%</span>
            <span className="stat-name">POSESIÓN</span>
            <span>{posesion[1]}%</span>
          </div>
          <div className="possession-track">
            <div 
              className="possession-fill local" 
              style={{ width: `${posesion[0]}%` }}
            ></div>
          </div>
        </div>
      </div>

      <main className="match-content-grid">
        {/* Timeline */}
        <section className="timeline-section glass">
          <div className="timeline-track">
            <div className="timeline-progress" style={{ width: `${(minuto/90)*100}%` }}></div>
            <div className="timeline-marker" style={{ left: `${(minuto/90)*100}%` }}></div>
          </div>
          <div className="timeline-labels">
            <span>0'</span>
            <span>45'</span>
            <span>90'</span>
          </div>
        </section>

        {/* Event Feed */}
        <section className="event-feed-section">
          <h3>Sucedido en el partido</h3>
          <div className="event-list hide-scroll">
            <AnimatePresence>
              {eventos.map((ev) => (
                <motion.div 
                  key={ev.id}
                  initial={{ opacity: 0, x: ev.isLocal ? -20 : 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`event-item-card ${ev.tipo === 'GOL' ? 'is-goal' : ''}`}
                >
                  <span className="event-min">{ev.minuto}'</span>
                  <span className="event-icon-box">{EVENT_ICONS[ev.tipo] || '•'}</span>
                  <p className="event-desc">{ev.descripcion}</p>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </section>
      </main>
    </div>
  );
}

export default MatchCenter;
