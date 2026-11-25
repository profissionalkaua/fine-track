'use client';

import { useCallback, useEffect, useState } from 'react';
import { ChartNoAxesCombined, UsersRound, SlidersHorizontal, Lightbulb, ArrowUpRight, LogOut, CircleHelp, ChevronDown, Activity } from 'lucide-react';
import { api, setSession, type Identity, type Video } from '../lib/api';
import { ErrorNotice, Logo, Modal } from './ui';
import { Feed, type Filters } from './feed';

const areas = [
  { key: 'videos', label: 'Vídeos em alta', icon: ChartNoAxesCombined },
  { key: 'criadores', label: 'Criadores', icon: UsersRound },
  { key: 'marca', label: 'Regras da marca', icon: SlidersHorizontal },
  { key: 'ideias', label: 'Gerar ideias', icon: Lightbulb },
];

function Login({ onLogin }: { onLogin: (identity: Identity) => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  return <main className="login-page"><div className="login-brand"><Logo /><div><div className="eyebrow">MENOS ACHISMO. MAIS DIREÇÃO.</div>
    <h1>O próximo sinal<br />já está por aí<span>.</span></h1><p>Descubra o que está crescendo.<br />Transforme referências em ideias com a sua voz.</p></div>
    <small>Inteligência de conteúdo para quem cria.</small></div><section className="login-form"><div className="login-box"><span className="eyebrow">SEU ESPAÇO DE CRIAÇÃO</span>
      <h2>Entre no seu workspace</h2><p>Acompanhe os sinais e continue de onde parou.</p>
      <form onSubmit={async e => { e.preventDefault(); const form = new FormData(e.currentTarget); setBusy(true); setError('');
        try { const identity = await api<Identity>('/auth/login', {method:'POST', body:JSON.stringify({email:form.get('email'), password:form.get('password')})});
          setSession(identity); onLogin(identity); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }}>
        <label>Email<input name="email" type="email" autoComplete="username" placeholder="voce@seuestudio.com" required /></label>
        <label>Senha<input name="password" type="password" autoComplete="current-password" placeholder="Sua senha" required /></label>
        {error && <ErrorNotice message={error} />}<button className="button primary" disabled={busy}>{busy ? 'Entrando…' : 'Entrar no workspace'}<ArrowUpRight size={18} /></button>
      </form><p className="login-help">Seu acesso é criado pelo administrador do workspace.</p></div></section></main>;
}

export function Dashboard() {
  const [identity, setIdentity] = useState<Identity | null>(null); const [booting, setBooting] = useState(true);
  const [area, setArea] = useState('videos');
  const [filters, setFilters] = useState<Filters>({country:'BR', period:'day', hashtag:''});
  const [idea, setIdea] = useState<Video | null>(null); const [help, setHelp] = useState(false);
  const [error, setError] = useState('');
  const readLocation = useCallback((country?: string) => {
    const params = new URLSearchParams(window.location.search);
    setArea(areas.some(a => a.key === params.get('area')) ? params.get('area')! : 'videos');
    setFilters({country:params.get('country') || country || 'BR', period:params.get('period') || 'day', hashtag:params.get('hashtag') || ''});
  }, []);
  useEffect(() => {
    api<Identity>('/auth/me').then(i => { setSession(i); setIdentity(i); readLocation(i.user.country); }).catch(() => {}).finally(() => setBooting(false));
    const back = () => readLocation(); window.addEventListener('popstate', back); return () => window.removeEventListener('popstate', back);
  }, [readLocation]);
  const changeFilters = useCallback((next: Filters) => {
    setFilters(next); const params = new URLSearchParams(window.location.search);
    params.set('country', next.country); params.set('period', next.period); if (next.hashtag) params.set('hashtag', next.hashtag); else params.delete('hashtag');
    const url = `/?${params}`; if (url !== window.location.pathname + window.location.search) window.history.pushState({}, '', url);
  }, []);
  function navigate(next: string) {
    setArea(next); const params = new URLSearchParams(window.location.search); params.set('area', next);
    window.history.pushState({}, '', `/?${params}`);
  }
  if (booting) return <main className="boot-state" role="status"><Logo /><span className="spinner" />Abrindo seu espaço…</main>;
  if (!identity) return <Login onLogin={i => { setIdentity(i); readLocation(i.user.country); }} />;
  return <div className="app-shell"><a href="#main-content" className="skip-link">Ir para o conteúdo</a>
    <aside className="sidebar"><a className="brand-link" href="/" aria-label="Pulso, início"><Logo /></a>
      <div className="workspace-card"><span className="workspace-avatar">{identity.workspace.name.slice(0,1)}</span><div><strong>{identity.workspace.name}</strong><small>Workspace</small></div><ChevronDown size={13} /></div>
      <div className="nav-caption">SEU RADAR CRIATIVO</div><nav aria-label="Navegação principal">{areas.map(({key, label, icon: Icon}) =>
        <button key={key} className={area === key ? 'active' : ''} aria-current={area === key ? 'page' : undefined} onClick={() => navigate(key)}><Icon size={18} />{label}{area === key && <span className="active-mark" />}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-note"><Activity size={19} /><p>Referências inspiram.<br /><strong>A sua voz diferencia.</strong></p></div>
        <button className="sidebar-help" onClick={() => setHelp(true)}><CircleHelp size={17} />Como funciona</button>
        <div className="account"><span className="account-avatar">{identity.user.email[0].toUpperCase()}</span><div><strong>{identity.user.email.split('@')[0]}</strong><small>{identity.workspace.role === 'owner' ? 'Proprietário' : identity.workspace.role === 'editor' ? 'Editor' : 'Visualizador'}</small></div>
          <button aria-label="Sair da conta" onClick={async () => { try { await api('/auth/logout', {method:'POST'}); setSession(null); setIdentity(null); } catch(e) { setError((e as Error).message); } }}><LogOut size={17} /></button></div></div>
    </aside><div className="main-wrap"><div className="topbar"><span>Workspace <span>/</span> <strong>{areas.find(a => a.key === area)?.label}</strong></span><span className="topbar-caption"><span className="live-dot" />Crie com intenção</span></div>
      <main id="main-content" className="page-content">{error && <ErrorNotice message={error} />}
        {area === 'videos' ? <Feed filters={filters} onFilters={changeFilters} onNavigate={navigate} onIdeas={setIdea} /> : <header className="page-heading"><h1>{areas.find(a => a.key === area)?.label}</h1></header>}
      </main></div>
    <Modal open={!!idea} onClose={() => setIdea(null)} title="Ideias e roteiros" description={idea ? `@${idea.handle} · ${idea.description}` : undefined}><p className="muted">A análise deste vídeo ficará disponível quando o pipeline estiver configurado.</p></Modal>
    <Modal open={help} onClose={() => setHelp(false)} title="Do sinal à sua próxima ideia"><ol className="help-list"><li>Escolha um país e período para consultar o ranking observado.</li><li>Salve criadores e configure a direção da sua marca.</li><li>Analise referências para produzir roteiros com evidências.</li></ol><p className="muted">A cobertura depende das fontes disponíveis. Métricas públicas são totais globais, e hipóteses editoriais são identificadas nos resultados.</p></Modal>
  </div>;
}
