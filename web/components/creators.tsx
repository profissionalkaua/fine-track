"use client";

import { useEffect, useState } from "react";
import {
  Plus,
  UsersRound,
  ArrowUpRight,
  Trash2,
  Undo2,
  UserRound,
  Check,
} from "lucide-react";
import { api, date, type Video } from "../lib/api";
import { ErrorNotice, Metrics, Modal, VideoCard } from "./ui";

type Creator = {
  id: string;
  creator_id: string | null;
  handle: string;
  name: string;
  status: string;
  error: string | null;
  observed_at: string | null;
};
export function Creators({
  onIdeas,
  editable,
}: {
  onIdeas: (v: Video) => void;
  editable: boolean;
}) {
  const [profiles, setProfiles] = useState<Creator[]>([]);
  const [selected, setSelected] = useState<Creator | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [removed, setRemoved] = useState<Creator | null>(null);
  const [details, setDetails] = useState<Video | null>(null);
  const [order, setOrder] = useState("recent");
  const [videos, setVideos] = useState<Video[]>([]);
  const [videoReason, setVideoReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  async function load() {
    try {
      const result = await api<{ items: Creator[] }>("/creators");
      setProfiles(result.items);
      setSelected(
        (previous) =>
          result.items.find((v) => v.id === previous?.id) || previous,
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    if (!profiles.some((p) => p.status === "pending")) return;
    const timer = setInterval(() => void load(), 3000);
    return () => clearInterval(timer);
  }, [profiles]);
  useEffect(() => {
    setVideos([]);
    setCursor(null);
    setVideoReason("");
    if (selected?.status !== "active") return;
    const controller = new AbortController();
    setLoading(true);
    api<{ items: Video[]; reason: string | null; cursor: string | null }>(
      `/creators/${selected.id}/videos?order=${order}`,
      { signal: controller.signal },
    )
      .then((r) => {
        setVideos(r.items);
        setVideoReason(r.reason || "");
        setCursor(r.cursor);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [selected?.id, selected?.status, order]);
  async function action(path: string, method = "POST", body?: object) {
    setBusy(true);
    setError("");
    try {
      const result = await api<Creator>(path, {
        method,
        body: body ? JSON.stringify(body) : undefined,
      });
      await load();
      return result;
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>
            Criadores
            <span className="heading-dot" aria-hidden="true">
              .
            </span>
          </h1>
          <p>Um radar de referências para ampliar o seu repertório.</p>
        </div>
        <span className="count-label">
          <UsersRound size={16} />
          {profiles.filter((p) => p.status === "active").length} perfis
          acompanhados
        </span>
      </header>
      {error && <ErrorNotice message={error} retry={() => void load()} />}
      {removed && (
        <div className="notice undo-notice" role="status">
          <span>@{removed.handle} foi removido.</span>
          <button
            disabled={busy}
            onClick={async () => {
              const result = await action(`/creators/${removed.id}/restore`);
              if (result) {
                setRemoved(null);
                setSelected(result);
              }
            }}
          >
            <Undo2 size={14} />
            Desfazer
          </button>
        </div>
      )}
      <div className="creators-layout">
        <section className="form-panel profile-panel">
          <div className="section-title">
            <h2>Perfis salvos</h2>
            <span className="count-badge">{profiles.length}</span>
          </div>
          <form
            className="add-profile"
            onSubmit={async (e) => {
              e.preventDefault();
              const result = await action("/creators", "POST", { input });
              if (result) {
                setInput("");
                setSelected(result);
              }
            }}
          >
            <label>
              Usuário ou URL do TikTok
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="@perfil ou link do perfil"
                maxLength={300}
                required
                disabled={!editable}
              />
            </label>
            <button
              className="button secondary"
              disabled={!editable || busy || !input.trim()}
            >
              <Plus size={16} />
              Adicionar perfil
            </button>
          </form>
          {!profiles.length && (
            <div className="profile-empty">
              <UserRound size={28} />
              <h3>Suas referências começam aqui</h3>
              <p>
                Adicione um perfil público para acompanhar seus vídeos e
                aprender com os padrões.
              </p>
            </div>
          )}
          <div className="profile-list">
            {profiles.map((p) => (
              <article
                key={p.id}
                data-creator
                className={selected?.id === p.id ? "selected" : ""}
              >
                <div className="profile-identity">
                  <span className="profile-avatar">
                    {p.name[0].toUpperCase()}
                  </span>
                  <div>
                    <h3>{p.name}</h3>
                    <p>@{p.handle}</p>
                  </div>
                </div>
                <span className={`profile-status ${p.status}`}>
                  {{
                    pending: "Confirmando perfil…",
                    preview: "Prévia pronta para confirmar",
                    active: "Acompanhando",
                    unavailable: "Indisponível",
                  }[p.status] || p.status}
                </span>
                <div className="profile-actions">
                  <button onClick={() => setSelected(p)}>
                    Ver vídeos <ArrowUpRight size={13} />
                  </button>
                  <button
                    aria-label={`Remover @${p.handle}`}
                    disabled={!editable || busy}
                    onClick={async () => {
                      if (await action(`/creators/${p.id}`, "DELETE")) {
                        setRemoved(p);
                        if (selected?.id === p.id) setSelected(null);
                      }
                    }}
                  >
                    <Trash2 size={13} />
                    Remover
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
        <section className="creator-videos">
          <div className="creator-panel-heading">
            <div>
              <h2>Vídeos do perfil</h2>
              <p>
                {selected
                  ? `@${selected.handle} · ${selected.observed_at ? date(selected.observed_at) : "Aguardando confirmação"}`
                  : "Selecione uma referência para explorar."}
              </p>
            </div>
          </div>
          {!selected ? (
            <div className="empty-state">
              <div className="empty-icon">
                <UsersRound size={27} />
              </div>
              <h2>Um novo olhar faz diferença</h2>
              <p>
                Escolha um perfil salvo para ver os vídeos e comparar os sinais
                de crescimento.
              </p>
            </div>
          ) : selected.status === "preview" ? (
            <div className="empty-state">
              <span className="profile-avatar large">{selected.name[0]}</span>
              <h2>{selected.name}</h2>
              <p>
                @{selected.handle}
                <br />
                Confirme este perfil público antes de começar a acompanhá-lo.
              </p>
              <button
                className="button primary"
                disabled={busy || !editable}
                onClick={async () => {
                  const result = await action(
                    `/creators/${selected.id}/confirm`,
                    "POST",
                    { creator_id: selected.creator_id },
                  );
                  if (result) setSelected(result);
                }}
              >
                <Check size={16} />
                Confirmar perfil
              </button>
            </div>
          ) : selected.status !== "active" ? (
            <div className="empty-state">
              <div className="empty-icon">
                <UserRound size={27} />
              </div>
              <h2>
                {selected.status === "pending"
                  ? "Conferindo a identidade do perfil"
                  : "Não foi possível consultar este perfil"}
              </h2>
              <p>
                {selected.error ||
                  "A confirmação ocorre em background. Você pode aguardar ou remover o perfil salvo para cancelar."}
              </p>
              {selected.status === "unavailable" && (
                <button
                  className="button secondary"
                  disabled={busy || !editable}
                  onClick={() => void action(`/creators/${selected.id}/retry`)}
                >
                  Tentar novamente
                </button>
              )}
            </div>
          ) : (
            <>
              <div
                className="creator-sort segmented"
                aria-label="Ordenação de vídeos"
              >
                {[
                  ["recent", "Recentes"],
                  ["performance", "Mais performáticos"],
                  ["views", "Total de views"],
                ].map(([key, label]) => (
                  <button
                    key={key}
                    aria-pressed={order === key}
                    onClick={() => setOrder(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <p className="creator-order-note">
                {order === "performance"
                  ? "Crescimento observado nas últimas 24 horas."
                  : order === "views"
                    ? "Ordenação por views acumuladas globais."
                    : "Publicações em ordem de data."}
                {
                  " Percentil por velocidade: mesma cobertura da janela, duração observada com diferença de até uma hora; empates usam a posição média."
                }
              </p>
              {loading ? (
                <p className="muted">Carregando vídeos…</p>
              ) : !videos.length ? (
                <div className="empty-state">
                  <h2>Aguardando observações</h2>
                  <p>{videoReason}</p>
                </div>
              ) : (
                <div className="video-grid">
                  {videos.map((v) => (
                    <VideoCard
                      key={v.id}
                      video={v}
                      onDetails={setDetails}
                      onIdeas={onIdeas}
                    />
                  ))}
                </div>
              )}
              {cursor && (
                <button
                  className="button secondary"
                  onClick={async () => {
                    try {
                      const r = await api<{
                        items: Video[];
                        cursor: string | null;
                      }>(
                        `/creators/${selected.id}/videos?order=${order}&cursor=${encodeURIComponent(cursor)}`,
                      );
                      setVideos([...videos, ...r.items]);
                      setCursor(r.cursor);
                    } catch (e) {
                      setError((e as Error).message);
                    }
                  }}
                >
                  Carregar mais vídeos
                </button>
              )}
            </>
          )}
        </section>
      </div>
      <Modal
        open={!!details}
        onClose={() => setDetails(null)}
        title="Detalhes do vídeo"
        description={
          details ? `@${details.handle} · ${details.description}` : undefined
        }
      >
        {details && (
          <div className="detail-content">
            <Metrics video={details} />
            <dl className="detail-list">
              <div>
                <dt>Publicado em</dt>
                <dd>{date(details.published_at)}</dd>
              </div>
              <div>
                <dt>Observado em</dt>
                <dd>{date(details.observed_at)}</dd>
              </div>
            </dl>
            <p className="muted">
              Métricas acumuladas globais do vídeo. O crescimento é calculado
              apenas quando existem medições comparáveis.
            </p>
            <div className="form-actions">
              {details.url ? (
                <a
                  className="button secondary"
                  href={details.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Ver no TikTok
                  <ArrowUpRight size={14} />
                </a>
              ) : (
                <span className="muted">Link original indisponível</span>
              )}
              <button
                className="button primary"
                onClick={() => {
                  onIdeas(details);
                  setDetails(null);
                }}
              >
                Ideias e roteiros
              </button>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}
