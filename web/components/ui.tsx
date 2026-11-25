'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { X, ArrowUpRight, Activity, Eye, Heart, MessageCircle, Share2 } from 'lucide-react';
import type { Video } from '../lib/api';
import { metric, date } from '../lib/api';

export function Logo() {
  return <span className="logo"><Activity size={27} strokeWidth={2.7} aria-hidden="true" /><span>pulso<span className="logo-dot">.</span></span></span>;
}

export function Modal({ open, onClose, title, description, children }: {
  open: boolean; onClose: () => void; title: string; description?: string; children: React.ReactNode;
}) {
  return <Dialog.Root open={open} onOpenChange={v => { if (!v) onClose(); }}>
    <Dialog.Portal><Dialog.Overlay className="modal-overlay" />
      <Dialog.Content className="modal-content" onCloseAutoFocus={event => {
        // This controlled modal is opened by buttons outside a Dialog.Trigger.
        event.preventDefault();
        const element = document.querySelector<HTMLElement>('[data-modal-origin="true"]');
        element?.focus(); element?.removeAttribute('data-modal-origin');
      }}>
        <div className="modal-heading"><div><Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description>{description || 'Informações e ações do vídeo selecionado.'}</Dialog.Description></div>
          <Dialog.Close className="icon-button" aria-label="Fechar janela"><X size={20} /></Dialog.Close></div>
        {children}
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>;
}

export function rememberFocus() {
  if (document.activeElement instanceof HTMLElement) document.activeElement.setAttribute('data-modal-origin', 'true');
}

export function Metrics({ video }: { video: Video }) {
  return <dl className="video-metrics">{[
    { icon: Eye, label: 'Views', value: video.views }, { icon: Heart, label: 'Curtidas', value: video.likes },
    { icon: MessageCircle, label: 'Comentários', value: video.comments }, { icon: Share2, label: 'Shares', value: video.shares },
  ].map(({ icon: Icon, label, value }) => <div key={label}><dt><Icon size={13} aria-hidden="true" />{label}</dt>
    <dd className={value == null ? 'unavailable' : ''}>{metric(value)}</dd></div>)}</dl>;
}

export function Poster({ video }: { video: Video }) {
  if (video.thumbnail) return <div className="poster"><img src={video.thumbnail} alt="" loading="lazy" referrerPolicy="no-referrer" /></div>;
  const palettes = [['#e4ded1', '#7a624a'], ['#dce2da', '#576d58'], ['#e5dce8', '#7b6385'], ['#e1d6ce', '#9a6046']];
  const palette = palettes[Number(video.id.slice(-2)) % palettes.length];
  return <div className="poster" style={{ background: palette[0], color: palette[1] }}>
    <svg className="poster-art" viewBox="0 0 400 200" aria-hidden="true">
      <circle cx="310" cy="105" r="91" fill="currentColor" opacity=".12" />
      <rect x="232" y="43" width="88" height="132" rx="44" fill="currentColor" opacity=".17" transform="rotate(25 276 109)" />
      <path d="M200 165 Q260 20 365 170" fill="none" stroke="currentColor" strokeWidth="2" opacity=".35" />
      <circle cx="300" cy="95" r="27" fill="none" stroke="currentColor" strokeWidth="2" opacity=".4" />
    </svg>
    <span className="poster-kicker">{video.synthetic ? 'ESTÚDIO DE EXEMPLOS' : 'PRÉVIA INDISPONÍVEL'}</span>
    <span className="poster-text">{video.categories[0]?.text || 'Conteúdo em foco'}<span>Um novo ponto de vista.</span></span>
    <span className="poster-duration">{video.duration ? `0:${String(Math.round(video.duration)).padStart(2, '0')}` : 'Sem miniatura'}</span>
  </div>;
}

export function VideoCard({ video, onDetails, onIdeas }: {
  video: Video; onDetails: (video: Video) => void; onIdeas: (video: Video) => void;
}) {
  return <article className="video-card" data-video-card>
    <div className="poster-wrap"><Poster video={video} />
      {video.rank && <span className="rank-badge">{String(video.rank).padStart(2, '0')}</span>}
      {video.partial_window && <span className="partial-badge">Janela parcial</span>}</div>
    <div className="card-body"><span className="creator-handle">@{video.handle}</span>
      <h3>{video.description}</h3>
      <div className="growth"><ArrowUpRight size={17} aria-hidden="true" /><strong>{metric(video.velocity)}<span> views/h</span></strong>
        <span>+{metric(video.delta_views)} no período</span></div>
      <Metrics video={video} />
      <div className="tags">{video.hashtags.slice(0, 3).map(tag => <span key={tag.key}>#{tag.label}</span>)}</div>
      <div className="card-meta">Publicado em {date(video.published_at, false)}{video.synthetic && <span>Exemplo fictício</span>}</div>
    </div>
    <div className="card-actions"><button onClick={() => { rememberFocus(); onDetails(video); }}>Ver detalhes</button>
      <button onClick={() => { rememberFocus(); onIdeas(video); }}>Ideias e roteiros <ArrowUpRight size={15} /></button></div>
  </article>;
}

export function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="notice error" role="alert"><span>{message}</span>{retry && <button onClick={retry}>Tentar novamente</button>}</div>;
}
