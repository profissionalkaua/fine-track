"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Check,
  Copy,
  Download,
  FileText,
  Lightbulb,
  Play,
  RotateCcw,
  X,
  Info,
} from "lucide-react";
import { api, date, type FeedData, type Video } from "../lib/api";
import type { Brand } from "./brand-rules";
import type { Filters } from "./feed";
import { ErrorNotice, Modal } from "./ui";

type Idea = {
  title: string;
  premise: string;
  justification: string;
  reference_ids: string[];
  intent: string;
  hook: string;
  script: { label: string; text: string }[];
  on_screen_text: string;
  cta: string;
  estimated_duration_seconds: number;
  basis: string;
};
type Visual = {
  state: string;
  reason?: string;
  segments?: {
    start_ms: number;
    end_ms: number;
    movement?: string;
    scene?: string;
    lighting?: string;
    clothing?: string;
    camera?: string;
    dance_style?: string;
    confidence?: number;
    people_count?: number | null;
  }[];
};
type Frozen = {
  country: string;
  period: string;
  category: string | null;
  hashtag: string | null;
  rules_version: number;
  captured_at: string;
  references: (Video & { origins: string[] })[];
  creator_groups: {
    handle: string;
    references: string[];
    warnings: string[];
  }[];
  rules: Brand;
};
export type AnalysisRun = {
  id: string;
  scope: string;
  state: string;
  progress: number;
  processed: number;
  frozen: Frozen;
  created_at: string;
  result: {
    ideas: Idea[];
    evidence: {
      video_id: string;
      observation: string;
      kind: string;
      source: string;
    }[];
    analise_visual: Visual;
    model_version?: string;
    methodology?: string;
  } | null;
  errors: { stage: string; code: string; message: string }[];
};
const terminal = new Set(["completed", "partial", "failed", "cancelled"]);
const labels: Record<string, string> = {
  queued: "Na fila",
  collecting: "Preparando referências",
  analyzing: "Analisando sinais",
  generating: "Criando ideias",
  completed: "Análise concluída",
  partial: "Resultado parcial",
  failed: "Não foi possível concluir",
  cancelled: "Execução cancelada",
};
const periodNames: Record<string, string> = {
  day: "Dia · últimas 24 horas",
  week: "Semana · últimos 7 dias",
  month: "Mês · últimos 30 dias",
};

export function useAnalysisRun(enabled: string | null) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setRun(null);
    if (!enabled) return;
    api<{ items: AnalysisRun[] }>("/runs")
      .then((r) => setRun(r.items.find((v) => v.scope === "feed") || null))
      .catch((e) => setError(e.message));
  }, [enabled]);
  useEffect(() => {
    if (!run || terminal.has(run.state)) return;
    const timer = setInterval(
      () =>
        api<AnalysisRun>(`/runs/${run.id}`)
          .then(setRun)
          .catch((e) => setError(e.message)),
      1500,
    );
    return () => clearInterval(timer);
  }, [run?.id, run?.state]);
  return { run, setRun, error, setError };
}

function scriptText(idea: Idea) {
  return [
    idea.title,
    `Gancho: ${idea.hook}`,
    ...idea.script.map((b) => `${b.label}: ${b.text}`),
    `CTA: ${idea.cta}`,
    `Texto na tela: ${idea.on_screen_text}`,
    `Duração estimada: ${idea.estimated_duration_seconds}s`,
  ].join("\n\n");
}

async function downloadRun(run: AnalysisRun) {
  const content = await api<object>(`/runs/${run.id}/export`);
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(content, null, 2)], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = `pulso-${run.id}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function IdeaContent({
  idea,
  run,
  individual = false,
}: {
  idea: Idea;
  run: AnalysisRun;
  individual?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const ref = run.frozen.references.find((v) =>
    idea.reference_ids.includes(v.id),
  );
  return (
    <div className="idea-content">
      <span className="idea-basis">
        {idea.basis === "editorial_hypothesis"
          ? "Hipótese editorial"
          : "Sugestão apoiada em evidências"}
      </span>
      <h3>{idea.title}</h3>
      <p className="idea-premise">{idea.premise}</p>
      <div className="script-hook">
        <span>GANCHO ORIGINAL</span>
        <p>{idea.hook}</p>
      </div>
      <div className="script-blocks">
        {idea.script.map((block, i) => (
          <div key={i}>
            <h4>{block.label}</h4>
            <p>{block.text}</p>
          </div>
        ))}
        <div>
          <h4>CTA</h4>
          <p>{idea.cta}</p>
        </div>
        <div>
          <h4>Texto sugerido na tela</h4>
          <p>{idea.on_screen_text || "Sem sugestão de texto."}</p>
        </div>
      </div>
      <div className="duration-note">
        Duração estimada: {idea.estimated_duration_seconds} segundos
      </div>
      <details className="evidence-details">
        <summary>
          Por que esta ideia? · {idea.reference_ids.length} referência(s)
        </summary>
        <p>{idea.justification}</p>
        <p>Intenção: {idea.intent}</p>
        {run.result?.evidence
          .filter((e) => idea.reference_ids.includes(e.video_id))
          .map((e, i) => (
            <div key={i}>
              <strong>
                {e.kind === "observed" ? "Observado" : "Hipótese"} · {e.source}
              </strong>
              <p>{e.observation}</p>
              <small>Referência: {e.video_id}</small>
            </div>
          ))}
      </details>
      {error && <ErrorNotice message={error} />}
      <div className="idea-actions">
        <button
          className="button secondary"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(scriptText(idea));
              setCopied(true);
              setTimeout(() => setCopied(false), 2500);
            } catch {
              setError(
                "Não foi possível copiar. Selecione o roteiro e copie manualmente.",
              );
            }
          }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          <span role="status">
            {copied ? "Roteiro copiado" : "Copiar roteiro"}
          </span>
        </button>
        <button
          className="button secondary"
          onClick={() => downloadRun(run).catch((e) => setError(e.message))}
        >
          <Download size={14} />
          Exportar JSON
        </button>
        {!individual &&
          (ref?.url ? (
            <a
              className="reference-link"
              href={ref.url}
              rel="noreferrer"
              target="_blank"
            >
              Ver vídeo de referência
              <ArrowUpRight size={13} />
            </a>
          ) : (
            <span className="muted">Link de referência indisponível</span>
          ))}
      </div>
    </div>
  );
}

export function Analysis({
  filters,
  brand,
  feed,
  state,
  onNavigate,
  editable,
}: {
  filters: Filters;
  brand: Brand;
  feed: FeedData | null;
  state: ReturnType<typeof useAnalysisRun>;
  onNavigate: (area: string) => void;
  editable: boolean;
}) {
  const [preview, setPreview] = useState<{
    eligible_count: number;
    frozen: Frozen;
    model_configured: boolean;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState("");
  const { run, setRun } = state;
  const body = useMemo(
    () => ({
      scope: "feed",
      country: filters.country,
      period: filters.period,
      hashtag: filters.hashtag || null,
      rules_version: brand.version,
      ...(feed?.country === filters.country &&
      feed.period === filters.period &&
      feed.version
        ? {
            ranking_version: feed.version,
            video_ids: feed.items
              .filter(
                (v) =>
                  !filters.hashtag ||
                  v.hashtags.some((t) => t.key === filters.hashtag),
              )
              .slice(0, 20)
              .map((v) => v.id),
          }
        : {}),
    }),
    [filters, brand.version, feed],
  );
  useEffect(() => {
    const controller = new AbortController();
    setPreview(null);
    setLocalError("");
    api<typeof preview>("/runs/preview", {
      method: "POST",
      body: JSON.stringify(body),
      signal: controller.signal,
    })
      .then(setPreview)
      .catch((e) => {
        if (e.name !== "AbortError") setLocalError(e.message);
      });
    return () => controller.abort();
  }, [body]);
  async function start(resume = false) {
    setBusy(true);
    setLocalError("");
    try {
      const result = await api<AnalysisRun>(
        resume && run ? `/runs/${run.id}/resume` : "/runs",
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify(body),
        },
      );
      setRun(result);
    } catch (e) {
      setLocalError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const active = !!run && !terminal.has(run.state);
  const changed =
    run &&
    (run.frozen.country !== filters.country ||
      run.frozen.period !== filters.period ||
      run.frozen.category !== brand.category_text ||
      (run.frozen.hashtag || "") !== filters.hashtag ||
      run.frozen.rules_version !== brand.version);
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>
            Gerar ideias
            <span className="heading-dot" aria-hidden="true">
              .
            </span>
          </h1>
          <p>Transforme os sinais do seu radar em conteúdo com intenção.</p>
        </div>
      </header>
      {(localError || state.error) && (
        <ErrorNotice message={localError || state.error} />
      )}
      <div className="analysis-grid">
        <section className="form-panel">
          <div className="panel-heading">
            <span className="panel-icon">
              <Lightbulb size={18} />
            </span>
            <div>
              <h2>Configuração da análise</h2>
              <p>Confira as referências antes de começar.</p>
            </div>
          </div>
          <dl className="config-list">
            <div>
              <dt>País</dt>
              <dd>
                {new Intl.DisplayNames(["pt-BR"], { type: "region" }).of(
                  filters.country,
                )}
              </dd>
            </div>
            <div>
              <dt>Período</dt>
              <dd>{periodNames[filters.period]}</dd>
            </div>
            <div>
              <dt>Categoria da marca</dt>
              <dd>{brand.category_text || "Todos os nichos"}</dd>
            </div>
            <div>
              <dt>Hashtag</dt>
              <dd>
                {filters.hashtag ? `#${filters.hashtag}` : "Todas as hashtags"}
              </dd>
            </div>
            <div>
              <dt>Vídeos do feed</dt>
              <dd>
                {preview
                  ? preview.frozen.references.filter((v) =>
                      v.origins.includes("top_video"),
                    ).length
                  : "…"}
              </dd>
            </div>
            <div>
              <dt>Perfis ativos</dt>
              <dd>{preview?.frozen.creator_groups.length ?? "…"}</dd>
            </div>
            <div>
              <dt>Regras aplicadas</dt>
              <dd>
                {brand.version
                  ? `Versão ${brand.version}`
                  : "Padrão do workspace"}
              </dd>
            </div>
          </dl>
          <div className="reference-total">
            <span>Referências elegíveis</span>
            <strong>{preview?.eligible_count ?? "—"}</strong>
          </div>
          {preview && preview.eligible_count < 5 && (
            <p className="muted">
              A análise geral precisa de pelo menos cinco referências. Aguarde a
              coleta ou ajuste o recorte.
            </p>
          )}
          {preview && !preview.model_configured && (
            <div className="notice">
              <Info size={15} />
              <span>
                O serviço de geração ainda precisa de um modelo local
                configurado.
              </span>
            </div>
          )}
          <div className="analysis-config-actions">
            <button
              className="text-button"
              onClick={() => onNavigate("videos")}
            >
              Ajustar filtros
              <ArrowUpRight size={13} />
            </button>
            <button
              className="button primary"
              disabled={!editable || busy || active || !preview}
              onClick={() => void start()}
            >
              <Play size={14} />
              {busy
                ? "Iniciando…"
                : changed
                  ? "Analisar recorte atual"
                  : "Iniciar análise"}
            </button>
          </div>
        </section>
        <section className="form-panel progress-panel">
          <div className="panel-heading">
            <span className="panel-icon">
              <FileText size={18} />
            </span>
            <div>
              <h2>Progresso</h2>
              <p>
                {run
                  ? "Acompanhe cada etapa da execução."
                  : "Sua próxima ideia começa nas referências."}
              </p>
            </div>
          </div>
          {!run ? (
            <div className="progress-empty">
              <div className="empty-icon">
                <Lightbulb size={28} />
              </div>
              <h3>Pronto para conectar os pontos?</h3>
              <p>
                Inicie a análise para organizar os sinais e gerar propostas com
                evidências.
              </p>
            </div>
          ) : (
            <>
              <div className={`run-state state-${run.state}`} role="status">
                {labels[run.state]}
              </div>
              <div
                className="progress-bar"
                role="progressbar"
                aria-label="Progresso da análise"
                aria-valuenow={run.progress}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <span style={{ width: `${run.progress}%` }} />
              </div>
              <div className="progress-caption">
                <span>
                  {run.processed} de {run.frozen.references.length} referências
                  processadas
                </span>
                <strong>{run.progress}%</strong>
              </div>
              <ol className="stage-list">
                {[
                  ["collecting", "Preparar referências"],
                  ["analyzing", "Analisar sinais"],
                  ["generating", "Gerar ideias e roteiros"],
                  ["completed", "Validar e salvar"],
                ].map(([key, label], i) => {
                  const current = [
                    "queued",
                    "collecting",
                    "analyzing",
                    "generating",
                    "completed",
                  ].indexOf(run.state);
                  const done = current > i + 1 || run.state === "completed";
                  return (
                    <li
                      key={key}
                      className={
                        done ? "done" : run.state === key ? "current" : ""
                      }
                    >
                      <span>{done ? <Check size={13} /> : i + 1}</span>
                      <div>
                        <strong>{label}</strong>
                        {run.state === key && <small>Em andamento</small>}
                      </div>
                    </li>
                  );
                })}
              </ol>
              <div className="frozen-context">
                <strong>Recorte congelado</strong>
                <p>
                  {run.frozen.country} · {periodNames[run.frozen.period]} ·{" "}
                  {run.frozen.category || "Todos os nichos"}
                  {run.frozen.hashtag ? ` · #${run.frozen.hashtag}` : ""}
                </p>
                <small>
                  Capturado em {date(run.frozen.captured_at)} · regras v
                  {run.frozen.rules_version}
                </small>
              </div>
              {changed && (
                <p className="muted">
                  Os filtros atuais mudaram. Este resultado mantém o recorte
                  original.
                </p>
              )}
              {run.errors.map((e, i) => (
                <div className="notice error" key={i} role="alert">
                  {e.message}
                </div>
              ))}
              {active ? (
                <button
                  className="button secondary cancel-button"
                  disabled={busy || !editable}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      setRun(
                        await api<AnalysisRun>(`/runs/${run.id}/cancel`, {
                          method: "POST",
                        }),
                      );
                    } catch (e) {
                      setLocalError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  <X size={14} />
                  Cancelar execução
                </button>
              ) : (
                ["failed", "partial", "cancelled"].includes(run.state) && (
                  <button
                    className="button secondary"
                    disabled={busy || !editable}
                    onClick={() => void start(true)}
                  >
                    <RotateCcw size={14} />
                    Retomar análise
                  </button>
                )
              )}
            </>
          )}
        </section>
      </div>
      {!!run?.result?.ideas.length && (
        <section className="ideas-section">
          <div className="feed-context">
            <div>
              <h2>
                Ideias e roteiros
                <span className="count-badge">{run.result.ideas.length}</span>
              </h2>
              <p>{run.result.methodology}</p>
            </div>
          </div>
          <div className="ideas-grid">
            {run.result.ideas.map((idea, i) => (
              <article className="form-panel" key={i}>
                <IdeaContent idea={idea} run={run} />
              </article>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

export function IndividualIdeas({
  video,
  brand,
  filters,
  onClose,
  editable,
}: {
  video: Video | null;
  brand: Brand;
  filters: Filters;
  onClose: () => void;
  editable: boolean;
}) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [tab, setTab] = useState("script");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function start() {
    if (!video) return;
    setBusy(true);
    setError("");
    try {
      setRun(
        await api<AnalysisRun>("/runs", {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({
            scope: "video",
            video_id: video.id,
            rules_version: brand.version,
            country: filters.country,
            period: filters.period,
          }),
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    setRun(null);
    setError("");
    setTab("script");
    if (!video) return;
    const controller = new AbortController();
    api<{ items: AnalysisRun[] }>("/runs", { signal: controller.signal })
      .then((r) => {
        const cached = r.items.find(
          (v) =>
            v.scope === "video" &&
            v.frozen.references[0]?.id === video.id &&
            v.frozen.rules_version === brand.version &&
            v.state === "completed",
        );
        if (cached) setRun(cached);
        else if (editable) void start();
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [video?.id]);
  useEffect(() => {
    if (!video || !run || terminal.has(run.state)) return;
    const timer = setInterval(
      () =>
        api<AnalysisRun>(`/runs/${run.id}`)
          .then(setRun)
          .catch((e) => setError(e.message)),
      1500,
    );
    return () => clearInterval(timer);
  }, [run?.id, run?.state, video?.id]);
  const visual = run?.result?.analise_visual;
  return (
    <Modal
      open={!!video}
      onClose={onClose}
      title="Ideias e roteiros"
      description={
        video ? `@${video.handle} · ${video.description}` : undefined
      }
    >
      <div
        className="modal-tabs"
        role="tablist"
        aria-label="Resultado do vídeo"
      >
        {[
          ["script", "Roteiro"],
          ["visual", "Análise visual"],
        ].map(([key, label]) => (
          <button
            role="tab"
            key={key}
            id={`tab-${key}`}
            aria-selected={tab === key}
            aria-controls={`panel-${key}`}
            tabIndex={tab === key ? 0 : -1}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                const next = key === "script" ? "visual" : "script";
                setTab(next);
                document.getElementById(`tab-${next}`)?.focus();
              }
            }}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {error && <ErrorNotice message={error} retry={() => void start()} />}
      <div
        role="tabpanel"
        id={`panel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        tabIndex={0}
      >
        {tab === "script" ? (
          run?.result?.ideas[0] ? (
            <IdeaContent idea={run.result.ideas[0]} run={run} individual />
          ) : (
            <div className="individual-pending">
              <div className="empty-icon">
                <FileText size={28} />
              </div>
              <h3>
                {run
                  ? labels[run.state]
                  : busy
                    ? "Preparando análise…"
                    : editable
                      ? "Preparando referências"
                      : "Nenhum roteiro disponível"}
              </h3>
              <p>
                {run && !terminal.has(run.state)
                  ? "A execução acontece em background. O roteiro aparecerá aqui quando estiver disponível."
                  : "O roteiro usa esta referência e a versão salva das regras da marca."}
              </p>
              {run?.errors.map((e, i) => (
                <ErrorNotice key={i} message={e.message} />
              ))}
              {run && terminal.has(run.state) && editable && (
                <button
                  className="button secondary"
                  disabled={busy}
                  onClick={() => void start()}
                >
                  Tentar novamente
                </button>
              )}
            </div>
          )
        ) : visual?.state === "completed" ? (
          <div className="visual-segments">
            {visual.segments?.map((s, i) => (
              <article key={i}>
                <strong>
                  {(s.start_ms / 1000).toFixed(1)}s —{" "}
                  {(s.end_ms / 1000).toFixed(1)}s
                </strong>
                <dl>
                  {[
                    ["Movimento", s.movement],
                    [
                      "Estilo da dança",
                      s.dance_style || "Estilo não identificado",
                    ],
                    ["Ambiente", s.scene],
                    ["Iluminação", s.lighting],
                    ["Figurino", s.clothing],
                    ["Pessoas visíveis", s.people_count],
                    ["Câmera", s.camera],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <dt>{label}</dt>
                      <dd>{value ?? "Indisponível"}</dd>
                    </div>
                  ))}
                </dl>
                <small>
                  Confiança: {Math.round((s.confidence || 0) * 100)}%
                </small>
              </article>
            ))}
          </div>
        ) : (
          <div className="individual-pending">
            <div className="empty-icon">
              <Info size={27} />
            </div>
            <h3>Análise visual indisponível</h3>
            <p>
              {visual?.reason ||
                "Mídia autorizada não disponível para esta análise."}
            </p>
            <p>
              Movimentos, iluminação, figurino e câmera exigem evidência visual.
              Esses campos permanecem indisponíveis.
            </p>
          </div>
        )}
      </div>
      {tab === "visual" && run && (
        <div className="form-actions">
          <button
            className="button secondary"
            onClick={() => downloadRun(run).catch((e) => setError(e.message))}
          >
            <Download size={14} />
            Exportar JSON
          </button>
        </div>
      )}
    </Modal>
  );
}
