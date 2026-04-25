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
  Activity
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

  const startQuickMatch = () => {
    // Para el demo, usamos Madrid (154) vs Barça (149)
    const local = teams.find(t => t.id === 154) || teams[0];
    const visitante = teams.find(t => t.id === 149) || teams[1];
    
    setMatchData({ local, visitante });
    setActiveTab('match-center');
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
                    <button className="play-btn-small" onClick={() => {
                        setMatchData({ local: selectedTeam, visitante: teams.find(t => t.id === 149) || teams[0] });
                        setActiveTab('match-center');
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
                  local={matchData.local} 
                  visitante={matchData.visitante} 
                  onBack={() => setActiveTab('teams')} 
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <style jsx global>{`
        .play-btn-large {
          background: var(--primary);
          color: var(--bg-main);
          font-weight: 800;
          padding: 12px 24px;
          display: flex;
          align-items: center;
          gap: 10px;
          border-radius: 30px;
          box-shadow: 0 0 20px var(--primary-glow);
          font-family: 'Barlow Condensed', sans-serif;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .play-btn-small {
          background: var(--bg-accent);
          color: var(--primary);
          border: 1px solid var(--primary);
          font-weight: 700;
          padding: 8px 16px;
          display: flex;
          align-items: center;
          gap: 8px;
          border-radius: 20px;
          font-size: 0.8rem;
          font-family: 'Barlow Condensed', sans-serif;
          text-transform: uppercase;
        }
      `}</style>
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
