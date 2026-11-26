"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Save, SlidersHorizontal, Sparkles } from "lucide-react";
import { api, date } from "../lib/api";
import { ErrorNotice } from "./ui";

export type Brand = {
  version: number;
  category_text: string | null;
  target_audience: string;
  tone: string;
  guidelines: string;
  preferred_format: string;
  analysis_elements: string[];
  saved_at: string | null;
};
const blank: Brand = {
  version: 0,
  category_text: null,
  target_audience: "",
  tone: "",
  guidelines: "",
  preferred_format: "",
  analysis_elements: [],
  saved_at: null,
};
const elements = [
  ["hook", "Gancho"],
  ["structure", "Estrutura do roteiro"],
  ["cta", "CTA"],
  ["pace", "Ritmo"],
  ["on_screen_text", "Texto na tela"],
  ["duration", "Duração"],
  ["retention", "Retenção"],
];

export function useBrandRules(enabled: string | null) {
  const [saved, setSaved] = useState<Brand>(blank);
  const [draft, setDraft] = useState<Brand>(blank);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [owner, setOwner] = useState<string | null>(null);
  const activeWorkspace = useRef(enabled);
  activeWorkspace.current = enabled;
  const loadingRequest = useRef<AbortController | null>(null);
  async function load() {
    const context = enabled;
    loadingRequest.current?.abort();
    if (!context) return;
    const controller = new AbortController();
    loadingRequest.current = controller;
    setLoaded(false);
    setOwner(context);
    setSaved(blank);
    setDraft(blank);
    setMessage("");
    setError("");
    try {
      const result = await api<Brand>("/brand-rules", {
        signal: controller.signal,
        headers: { "X-Workspace-ID": context },
      });
      if (controller.signal.aborted || activeWorkspace.current !== context)
        return;
      setSaved(result);
      setDraft(result);
      setLoaded(true);
      setError("");
    } catch (e) {
      if (!controller.signal.aborted && activeWorkspace.current === context)
        setError((e as Error).message);
    }
  }
  useEffect(() => {
    setLoaded(false);
    setSaved(blank);
    setDraft(blank);
    setBusy(false);
    if (enabled) void load();
    else {
      setLoaded(false);
      setSaved(blank);
      setDraft(blank);
    }
    return () => loadingRequest.current?.abort();
  }, [enabled]);
  async function save() {
    const context = enabled;
    if (!context || owner !== context || !loaded) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const { version, saved_at, ...content } = draft;
      const result = await api<Brand>("/brand-rules", {
        method: "PATCH",
        headers: { "X-Workspace-ID": context },
        body: JSON.stringify({ ...content, expected_version: saved.version }),
      });
      if (activeWorkspace.current !== context) return;
      setSaved(result);
      setDraft(result);
      setMessage("Regras salvas. Os próximos recortes usarão esta versão.");
    } catch (e) {
      if (activeWorkspace.current === context) setError((e as Error).message);
    } finally {
      if (activeWorkspace.current === context) setBusy(false);
    }
  }
  return {
    saved: owner === enabled ? saved : blank,
    draft: owner === enabled ? draft : blank,
    setDraft,
    loaded: loaded && owner === enabled,
    busy,
    error,
    message,
    save,
    load,
    dirty: JSON.stringify(saved) !== JSON.stringify(draft),
    clear: () => setDraft({ ...blank, version: saved.version }),
    discard: () => {
      setDraft(saved);
      setMessage("");
    },
    setMessage,
  };
}

export function BrandRules({
  state,
  editable,
}: {
  state: ReturnType<typeof useBrandRules>;
  editable: boolean;
}) {
  const { draft, setDraft, saved, dirty } = state;
  function field(key: keyof Brand, value: string) {
    setDraft({ ...draft, [key]: value });
    state.setMessage("");
  }
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>
            Regras da marca
            <span className="heading-dot" aria-hidden="true">
              .
            </span>
          </h1>
          <p>Defina a sua direção. Deixe as ideias com a sua voz.</p>
        </div>
        <span className={`save-state ${dirty ? "unsaved" : ""}`} role="status">
          {dirty
            ? "Alterações não salvas"
            : saved.version
              ? `Versão ${saved.version} salva`
              : "Configuração opcional"}
        </span>
      </header>
      {state.error && (
        <ErrorNotice message={state.error} retry={() => void state.load()} />
      )}
      {state.message && (
        <div className="notice success" role="status">
          <Check size={16} />
          {state.message}
        </div>
      )}
      {!state.loaded ? (
        <p className="muted">Carregando regras…</p>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void state.save();
          }}
        >
          <fieldset className="brand-grid" disabled={!editable || state.busy}>
            <section className="form-panel">
              <div className="panel-heading">
                <span className="panel-icon">
                  <SlidersHorizontal size={18} />
                </span>
                <div>
                  <h2>Público e direção</h2>
                  <p>Para quem você cria e o que quer comunicar.</p>
                </div>
              </div>
              <label>
                Categoria (opcional)
                <input
                  value={draft.category_text || ""}
                  maxLength={250}
                  placeholder="Ex.: culinária vegana, fitness, cerâmica autoral"
                  onChange={(e) => field("category_text", e.target.value)}
                />
                <small>
                  Define o nicho do feed e da coleta. Deixe vazio para explorar
                  todos os nichos.
                </small>
              </label>
              <label>
                Público-alvo
                <textarea
                  rows={3}
                  value={draft.target_audience}
                  maxLength={4000}
                  placeholder="Descreva interesses, necessidades e contexto do seu público."
                  onChange={(e) => field("target_audience", e.target.value)}
                />
              </label>
              <label>
                Tom de voz
                <input
                  value={draft.tone}
                  maxLength={2000}
                  placeholder="Ex.: próximo, direto e bem-humorado"
                  onChange={(e) => field("tone", e.target.value)}
                />
              </label>
              <label>
                Diretrizes da marca
                <textarea
                  rows={5}
                  value={draft.guidelines}
                  maxLength={8000}
                  placeholder="O que sua marca valoriza? Quais termos usar ou evitar?"
                  onChange={(e) => field("guidelines", e.target.value)}
                />
              </label>
            </section>
            <section className="form-panel">
              <div className="panel-heading">
                <span className="panel-icon">
                  <Sparkles size={18} />
                </span>
                <div>
                  <h2>Roteiro e análise</h2>
                  <p>Escolha o que observar e como transformar.</p>
                </div>
              </div>
              <label>
                Formato preferido
                <input
                  value={draft.preferred_format}
                  list="formats"
                  maxLength={1000}
                  placeholder="Escolha ou escreva um formato"
                  onChange={(e) => field("preferred_format", e.target.value)}
                />
                <datalist id="formats">
                  {[
                    "Storytelling",
                    "Lista",
                    "Antes/depois",
                    "Tutorial rápido",
                    "Demonstração",
                  ].map((t) => (
                    <option key={t} value={t} />
                  ))}
                </datalist>
              </label>
              <fieldset className="elements-field">
                <legend>Elementos de análise</legend>
                <p>Selecione os sinais que importam para suas ideias.</p>
                <div className="checkbox-list">
                  {elements.map(([key, label]) => (
                    <label key={key}>
                      <input
                        type="checkbox"
                        checked={draft.analysis_elements.includes(key)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            analysis_elements: e.target.checked
                              ? [...draft.analysis_elements, key]
                              : draft.analysis_elements.filter(
                                  (v) => v !== key,
                                ),
                          })
                        }
                      />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="context-note">
                <strong>Direção, sem limitar sua criatividade.</strong>
                <p>
                  As regras são opcionais. Campos sem evidência aparecem como
                  indisponíveis. Com dados públicos, retenção é uma hipótese
                  editorial.
                </p>
              </div>
            </section>
          </fieldset>
          <div className="brand-footer">
            <span>
              {saved.saved_at
                ? `Última versão salva em ${date(saved.saved_at)}`
                : "Ainda não há regras salvas."}
            </span>
            <div>
              <button
                type="button"
                className="text-button"
                disabled={!dirty || state.busy}
                onClick={state.discard}
              >
                Descartar alterações
              </button>
              <button
                type="button"
                className="button secondary"
                disabled={!editable || state.busy}
                onClick={state.clear}
              >
                Limpar campos
              </button>
              <button
                className="button primary"
                disabled={!editable || state.busy || !dirty}
              >
                <Save size={15} />
                {state.busy ? "Salvando…" : "Salvar regras"}
              </button>
            </div>
          </div>
        </form>
      )}
    </>
  );
}
