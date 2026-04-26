import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Users, 
  Settings, 
  Play, 
  BarChart3, 
  Shield, 
  Search,
  ChevronRight,
  TrendingUp,
  Activity,
  Zap,
  X
} from 'lucide-react';
import './App.css';
import MatchCenter from './MatchCenter';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('teams');
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [matchData, setMatchData] = useState(null);
  const [instantResult, setInstantResult] = useState(null);

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      const response = await axios.get(`${API_BASE}/teams`);
      setTeams(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching teams:", error);
      setLoading(false);
    }
  };

  const handleSelectTeam = async (id) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/teams/${id}`);
      setSelectedTeam(response.data);
      setActiveTab('team-detail');
      setLoading(false);
    } catch (error) {
      console.error("Error fetching team detail:", error);
      setLoading(false);
    }
  };

  const startQuickMatch = async () => {
    try {
      const response = await axios.post(`${API_BASE}/simulations/match`, {
        local_id: 154,
        visitante_id: 149
      });
      const { simulation_id, local, visitante } = response.data;
      setMatchData({ id: simulation_id, local: { id: 154, nombre: local }, visitante: { id: 149, nombre: visitante } });
      setActiveTab('match-center');
    } catch (err) {
      console.error("Error iniciando simulación:", err);
    }
  };

  const startInstantMatch = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/simulations/match/instant`, {
        local_id: 154,
        visitante_id: 149
      });
      setInstantResult(response.data);
      setActiveTab('instant-result');
      setLoading(false);
    } catch (err) {
      console.error("Error en simulación instantánea:", err);
      setLoading(false);
    }
  };

  const closeInstantResult = () => {
    setInstantResult(null);
    setActiveTab('home');
  };

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar glass">
        <div className="logo">
          <Trophy className="primary-icon" />
          <span>FM ENGINE</span>
        </div>
        
        <nav>
          <NavItem 
            active={activeTab === 'teams' || activeTab === 'team-detail'} 
            onClick={() => setActiveTab('teams')}
            icon={<Shield size={20} />} 
            label="Equipos" 
          />
          <NavItem 
            active={activeTab === 'players'} 
            onClick={() => setActiveTab('players')}
            icon={<Users size={20} />} 
            label="Jugadores" 
          />
          <NavItem 
            active={activeTab === 'instant-result'} 
            onClick={startInstantMatch}
            icon={<Zap size={20} />} 
            label="Resultado Instantáneo" 
          />
          <NavItem 
            active={activeTab === 'match-center'} 
            onClick={startQuickMatch}
            icon={<Play size={20} />} 
            label="Simular Partido" 
          />
          <NavItem 
            active={activeTab === 'stats'} 
            onClick={() => setActiveTab('stats')}
            icon={<BarChart3 size={20} />} 
            label="Estadísticas" 
          />
        </nav>

        <div className="sidebar-footer">
          <NavItem icon={<Settings size={20} />} label="Ajustes" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="content">
        <header className="header glass">
          <div className="search-bar">
            <Search size={18} className="text-muted" />
            <input type="text" placeholder="Buscar jugadores, equipos..." />
          </div>
          <div className="user-profile">
            <div className="status-badge">
              <Activity size={14} />
              <span>Motor Activo</span>
            </div>
            <div className="avatar">JD</div>
          </div>
        </header>

        <div className="main-scroll">
          <AnimatePresence mode="wait">
            {activeTab === 'teams' && (
              <motion.div 
                key="teams"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="view"
              >
                <div className="view-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
                  <div>
                    <h1>LaLiga 24/25</h1>
                    <p>Explora los equipos y sus métricas de rendimiento.</p>
                  </div>
                  <button className="play-btn-large" onClick={startQuickMatch}>
                    <Play size={18} fill="currentColor" /> Simular Clásico
                  </button>
                </div>

                <div className="team-grid">
                  {teams.map(team => (
                    <TeamCard 
                      key={team.id} 
                      team={team} 
                      onClick={() => handleSelectTeam(team.id)} 
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'team-detail' && selectedTeam && (
              <motion.div 
                key="team-detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="view"
              >
                <button className="back-btn" onClick={() => setActiveTab('teams')}>
                  &larr; Volver a equipos
                </button>
                
                <div className="team-banner glass">
                  <div className="team-info-big">
                    <div className="team-logo-placeholder">
                      {selectedTeam.nombre_corto}
                    </div>
                    <div>
                      <h1>{selectedTeam.nombre}</h1>
                      <div className="badges">
                        <span className="badge">Overall {selectedTeam.overall_medio.toFixed(1)}</span>
                        <span className="badge">LaLiga</span>
                      </div>
                    </div>
                  </div>
                </div>

                <section className="roster-section">
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                    <h2>Plantilla</h2>
                    <button className="play-btn-small" onClick={async () => {
                        try {
                          const rival = teams.find(t => t.id !== selectedTeam.id) || teams[0];
                          const response = await axios.post(`${API_BASE}/simulations/match`, {
                            local_id: selectedTeam.id,
                            visitante_id: rival.id
                          });
                          const { simulation_id, local, visitante } = response.data;
                          setMatchData({ id: simulation_id, local: { id: selectedTeam.id, nombre: local }, visitante: { id: rival.id, nombre: visitante } });
                          setActiveTab('match-center');
                        } catch (err) {
                          console.error("Error iniciando simulación:", err);
                        }
                    }}>
                      <Play size={14} fill="currentColor" /> Jugar Amistoso
                    </button>
                  </div>
                  <div className="roster-grid glass">
                    <table className="roster-table">
                      <thead>
                        <tr>
                          <th>Jugador</th>
                          <th>Posición</th>
                          <th>Overall</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedTeam.plantilla.map(player => (
                          <tr key={player.id}>
                            <td>
                              <div className="player-name-cell">
                                <span className="player-icon">👤</span>
                                {player.nombre}
                              </div>
                            </td>
                            <td>{player.posicion}</td>
                            <td>
                              <div className="overall-bar-container">
                                <div className="overall-bar-bg">
                                  <div 
                                    className="overall-bar" 
                                    style={{ width: `${player.overall}%` }}
                                  ></div>
                                </div>
                                <span style={{minWidth: '25px', textAlign: 'right'}}>{player.overall}</span>
                              </div>
                            </td>
                            <td>
                              <button className="icon-btn"><ChevronRight size={16} /></button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </motion.div>
            )}

            {activeTab === 'match-center' && matchData && (
              <motion.div
                key="match-center"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05 }}
              >
                <MatchCenter 
                  matchData={matchData}
                  onBack={() => setActiveTab('teams')} 
                />
              </motion.div>
            )}

            {activeTab === 'instant-result' && instantResult && (
              <motion.div
                key="instant-result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05 }}
                className="instant-result-view"
              >
                <div className="result-header">
                  <h2>Resultado del Partido</h2>
                  <button className="close-btn" onClick={closeInstantResult}>
                    <X size={24} />
                  </button>
                </div>
                
                <div className="result-scoreboard">
                  <div className="team-result">
                    <div className="team-logo">{instantResult.local.nombre}</div>
                    <div className="score">{instantResult.local.goles}</div>
                  </div>
                  <div className="score-separator">-</div>
                  <div className="team-result">
                    <div className="score">{instantResult.visitante.goles}</div>
                    <div className="team-logo">{instantResult.visitante.nombre}</div>
                  </div>
                </div>

                <div className="result-details">
                  <div className="detail-section">
                    <h3>Goleadores {instantResult.local.nombre}</h3>
                    {instantResult.local.goleadores.length > 0 ? (
                      <ul>
                        {instantResult.local.goleadores.map((g, i) => (
                          <li key={i}>⚽ {g.minuto}' - {g.descripcion}</li>
                        ))}
                      </ul>
                    ) : <p className="no-data">Sin goles</p>}
                  </div>
                  <div className="detail-section">
                    <h3>Goleadores {instantResult.visitante.nombre}</h3>
                    {instantResult.visitante.goleadores.length > 0 ? (
                      <ul>
                        {instantResult.visitante.goleadores.map((g, i) => (
                          <li key={i}>⚽ {g.minuto}' - {g.descripcion}</li>
                        ))}
                      </ul>
                    ) : <p className="no-data">Sin goles</p>}
                  </div>
                </div>

                <div className="result-cards">
                  <div className="card-section">
                    <h3>Tarjetas {instantResult.local.nombre}</h3>
                    {instantResult.local.tarjetas.length > 0 ? (
                      <ul>
                        {instantResult.local.tarjetas.map((t, i) => (
                          <li key={i}>{t.minuto}' - {t.descripcion}</li>
                        ))}
                      </ul>
                    ) : <p className="no-data">Sin tarjetas</p>}
                  </div>
                  <div className="card-section">
                    <h3>Tarjetas {instantResult.visitante.nombre}</h3>
                    {instantResult.visitante.tarjetas.length > 0 ? (
                      <ul>
                        {instantResult.visitante.tarjetas.map((t, i) => (
                          <li key={i}>{t.minuto}' - {t.descripcion}</li>
                        ))}
                      </ul>
                    ) : <p className="no-data">Sin tarjetas</p>}
                  </div>
                </div>

                <div className="result-timeline">
                  <h3> Cronología</h3>
                  <div className="timeline-list">
                    {instantResult.eventos.slice(0, 20).map((ev, i) => (
                      <div key={i} className={`timeline-item ${ev.tipo.toLowerCase()}`}>
                        <span className="timeline-minute">{ev.minuto}'</span>
                        <span className="timeline-icon">
                          {ev.tipo === 'GOL' ? '⚽' : ev.tipo === 'TARJETA_AMARILLA' ? '🟨' : ev.tipo === 'TARJETA_ROJA' ? '🟥' : ev.tipo === 'FALTA' ? '⚠️' : ev.tipo === 'TIRO' ? '🚀' : ev.tipo === 'PARADA' ? '🧤' : '•'}
                        </span>
                        <span className="timeline-desc">{ev.descripcion}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      className={`nav-item ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function TeamCard({ team, onClick }) {
  return (
    <motion.div 
      whileHover={{ scale: 1.02 }}
      className="team-card glass glow-hover"
      onClick={onClick}
    >
      <div className="team-card-header">
        <div className="team-logo">{team.nombre_corto}</div>
        <div className="overall-badge">OVR {team.overall_medio.toFixed(1)}</div>
      </div>
      <h3>{team.nombre}</h3>
      <div className="team-card-stats">
        <div className="stat">
          <span className="stat-label">Plantilla</span>
          <span className="stat-value">24</span>
        </div>
        <div className="stat">
          <span className="stat-label">Tendencia</span>
          <span className="stat-value text-success"><TrendingUp size={16} /></span>
        </div>
      </div>
    </motion.div>
  );
}

export default App;
