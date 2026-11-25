'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, SlidersHorizontal, RotateCcw, ArrowDown, Info, TrendingUp, Clock3 } from 'lucide-react';
import { api, date, metric, type FeedData, type Video } from '../lib/api';
import { ErrorNotice, Metrics, Modal, VideoCard } from './ui';

export type Filters = { country: string; period: string; hashtag: string };
export function Feed({ filters, onFilters, onNavigate, onIdeas, revision = 0 }: {
  filters: Filters; onFilters: (next: Filters) => void;
  onNavigate: (area: string) => void; onIdeas: (video: Video) => void; revision?: number;
}) {
  const [data, setData] = useState<FeedData | null>(null);
  const [countries, setCountries] = useState<{ code: string; name: string }[]>([]);
  const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState<Video | null>(null);
  const [reload, setReload] = useState(0);
  const countryNames = useMemo(() => new Intl.DisplayNames(['pt-BR'], { type: 'region' }), []);
  useEffect(() => { api<{code: string; name: string}[]>('/countries').then(setCountries).catch(e => setError(e.message)); }, []);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError(''); setData(null);
    api<FeedData>(`/top-videos?country=${filters.country}&period=${filters.period}`, { signal: controller.signal })
      .then(result => setData(result)).catch(e => { if (e.name !== 'AbortError') setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [filters.country, filters.period, revision, reload]);
  const tags = useMemo(() => [...new Map((data?.items || []).flatMap(v => v.hashtags).map(t => [t.key, t])).values()]
    .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR')), [data?.items]);
  useEffect(() => {
    if (data && filters.hashtag && !tags.some(t => t.key === filters.hashtag)) onFilters({ ...filters, hashtag: '' });
  }, [data, tags, filters, onFilters]);
  const visible = data?.items.filter(v => !filters.hashtag || v.hashtags.some(t => t.key === filters.hashtag)) || [];
  async function more() {
    if (!data?.cursor || loading) return; setLoading(true); setError('');
    try {
      const next = await api<FeedData>(`/top-videos?country=${filters.country}&period=${filters.period}&cursor=${encodeURIComponent(data.cursor)}`);
      setData({ ...next, items: [...data.items, ...next.items] });
    } catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }
  function setCountry(country: string) {
    onFilters({ ...filters, country });
    api('/preferences', { method: 'PATCH', body: JSON.stringify({country}) }).catch(e => setError(e.message));
  }
  return <>
    <header className="page-heading"><div><div className="eyebrow">DESCUBRA O PRÓXIMO MOVIMENTO</div>
      <h1>Vídeos em alta<span className="heading-dot" aria-hidden="true">.</span></h1><p>Encontre os sinais. Entenda o contexto. Crie algo seu.</p></div>
      <button className="button primary" onClick={() => onNavigate('ideias')}>Analisar recorte <ArrowUpRight size={17} /></button></header>
    <section className="filters-panel" aria-label="Filtros do feed"><div className="filters-row">
      <label>País<select aria-label="País" value={filters.country} onChange={e => setCountry(e.target.value)}>
        {(countries.length ? [...countries].sort((a, b) => (countryNames.of(a.code) || a.name).localeCompare(countryNames.of(b.code) || b.name, 'pt-BR')) : [{code:'BR', name:'Brasil'}])
          .map(c => <option key={c.code} value={c.code}>{countryNames.of(c.code) || c.name}</option>)}
      </select></label>
      <fieldset className="period-field"><legend>Período</legend><div className="segmented">{[['day', 'Dia'], ['week', 'Semana'], ['month', 'Mês']].map(([key, text]) =>
        <button key={key} aria-pressed={filters.period === key} onClick={() => onFilters({ ...filters, period: key })}>{text}</button>)}</div></fieldset>
      <label>Hashtag<select aria-label="Hashtag" disabled={!tags.length} value={filters.hashtag} onChange={e => onFilters({ ...filters, hashtag: e.target.value })}>
        <option value="">Todas as hashtags</option>{tags.map(t => <option key={t.key} value={t.key}>#{t.label}</option>)}
      </select></label>
      <button className="text-button reset-filters" onClick={() => { setCountry('BR'); onFilters({country:'BR', period:'day', hashtag:''}); }}><RotateCcw size={14} /> Limpar filtros</button>
    </div><div className="category-row"><span><SlidersHorizontal size={14} />Categoria da marca <strong>{data?.category || 'Todos os nichos'}</strong></span>
      <button onClick={() => onNavigate('marca')}>Editar categoria <ArrowUpRight size={13} /></button></div></section>
    <section className="ranking-banner"><span className="ranking-icon"><TrendingUp size={22} /></span><div><h2>Ranking por crescimento</h2>
      <p>Vídeos associados ao recorte selecionado · Métricas globais do vídeo</p></div>
      <div className="ranking-update"><span className="live-dot" /><span>{date(data?.as_of)}<small>Horário de Brasília</small></span></div></section>
    {error && <ErrorNotice message={error} retry={() => setReload(n => n+1)} />}
    {data?.items.some(v => v.synthetic) && <div className="demo-note"><Info size={15} /> Ambiente de demonstração · Todos os vídeos e métricas desta amostra são fictícios.</div>}
    <div className="feed-context"><div><h2>{filters.hashtag ? `#${tags.find(t => t.key === filters.hashtag)?.label || filters.hashtag}` : 'No radar agora'}
      <span className="count-badge">{data?.eligible_count || 0}</span></h2><p>{filters.hashtag ? `${visible.length} de ${data?.items.length} vídeos carregados` : `${data?.items.length || 0} vídeos carregados · ${data?.eligible_count || 0} elegíveis na consulta`}</p></div>
      <span className="window-caption"><Clock3 size={13} />{data ? `${date(data.window_start)} — ${date(data.window_end)}` : 'Carregando recorte'}</span></div>
    {data?.coverage_status === 'partial_coverage' && <div className="notice"><Info size={16} /><span>Cobertura parcial: {data.eligible_count} vídeos elegíveis. Você pode ampliar o período ou editar a categoria.</span></div>}
    {data?.is_stale && <div className="notice">Este ranking está desatualizado. Aguarde uma nova coleta.</div>}
    {loading && !data && <div className="feed-loading" role="status"><span className="spinner" />Buscando os sinais do seu recorte…</div>}
    {data && !data.items.length && <div className="empty-state"><div className="empty-icon"><TrendingUp size={30} /></div>
      <h2>{data.coverage_status === 'collecting' ? 'Estamos buscando novos sinais' : data.coverage_status === 'source_unavailable' ? 'A fonte ainda está indisponível' : 'Nenhum vídeo elegível neste recorte'}</h2>
      <p>{data.reason || 'Altere o país, amplie o período ou ajuste a categoria. Os resultados aparecerão quando houver evidência suficiente.'}</p>
      <button className="button secondary" onClick={() => setReload(n => n+1)}>Atualizar consulta</button></div>}
    <div className="video-grid">{visible.map(v => <VideoCard key={v.id} video={v} onDetails={setDetails} onIdeas={onIdeas} />)}</div>
    {data?.cursor && <div className="load-more"><button className="button secondary" disabled={loading} onClick={more}>{loading ? 'Carregando…' : 'Carregar mais vídeos'}<ArrowDown size={16} /></button></div>}
    {!!data?.most_viewed.length && <section className="most-viewed"><h2>Mais vistos da amostra</h2><p>Views acumuladas. Estes vídeos ainda não têm medições suficientes para o ranking por crescimento.</p>
      <div className="video-grid">{data.most_viewed.map(v => <VideoCard key={v.id} video={v} onDetails={setDetails} onIdeas={onIdeas} />)}</div></section>}
    <footer className="page-footer"><span>Pulso · Inteligência para criar com intenção</span><span>As métricas representam os totais públicos dos vídeos.</span></footer>
    <Modal open={!!details} onClose={() => setDetails(null)} title="Detalhes do vídeo" description={details ? `@${details.handle} · ${details.description}` : undefined}>
      {details && <div className="detail-content"><Metrics video={details} /><dl className="detail-list">
        <div><dt>Publicado em</dt><dd>{date(details.published_at)}</dd></div><div><dt>Observado em</dt><dd>{date(details.observed_at)}</dd></div>
        <div><dt>Crescimento na janela</dt><dd>+{metric(details.delta_views)} views · {metric(details.velocity)} views/h</dd></div>
        <div><dt>Associação ao país</dt><dd>{details.country} · {details.geo_evidence.reason}</dd></div></dl>
        <p className="muted">Views, curtidas, comentários e shares são acumulados globais. Crescimento corresponde apenas à janela observada.</p>
        <div className="tags">{details.hashtags.map(t => <span key={t.key}>#{t.label}</span>)}</div>
        <div className="form-actions">{details.url ? <a href={details.url} target="_blank" rel="noreferrer" className="button secondary">Ver no TikTok <ArrowUpRight size={16} /></a> : <span className="muted">Link original indisponível</span>}
          <button className="button primary" onClick={() => { onIdeas(details); setDetails(null); }}>Ideias e roteiros</button></div></div>}
    </Modal>
  </>;
}
