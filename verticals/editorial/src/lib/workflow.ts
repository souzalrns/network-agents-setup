import { canWrite, isDesk, type Role } from "./context";

/** Os 11 estados editoriais, pela ordem do fluxo. */
export const STATES = [
  "idea", "pitch_proposed", "pitch_approved", "researching", "interviewing",
  "writing", "in_review", "approved", "scheduled", "published", "archived",
] as const;
export type State = (typeof STATES)[number];

export const STATE_LABEL: Record<State, string> = {
  idea: "Ideia",
  pitch_proposed: "Pauta proposta",
  pitch_approved: "Pauta aprovada",
  researching: "Em investigação",
  interviewing: "Em entrevistas",
  writing: "Em redação",
  in_review: "Em revisão",
  approved: "Aprovada",
  scheduled: "Agendada",
  published: "Publicada",
  archived: "Arquivada",
};

/** Grupos para o painel. */
export const PITCH_STATES: State[] = ["idea", "pitch_proposed", "pitch_approved"];
export const WORK_STATES: State[] = ["researching", "interviewing", "writing"];
export const DESK_STATES: State[] = ["in_review", "approved", "scheduled"];

type Who = "owner" | "desk";
interface Rule { to: State; who: Who; label: string }

/**
 * Transições permitidas. `owner` = responsável, autor ou quem criou a peça (com papel de escrita);
 * `desk` = edição, direção ou administração. Uma ideia sem dono pode ser adoptada por qualquer redactor.
 * A base de dados volta a verificar o essencial (aprovar, agendar, publicar, quatro olhos, afirmações).
 */
const RULES: Record<State, Rule[]> = {
  idea: [
    { to: "pitch_proposed", who: "owner", label: "Propor como pauta" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  pitch_proposed: [
    { to: "pitch_approved", who: "desk", label: "Aprovar pauta" },
    { to: "idea", who: "owner", label: "Voltar a ideia" },
    { to: "archived", who: "desk", label: "Recusar e arquivar" },
  ],
  pitch_approved: [
    { to: "researching", who: "owner", label: "Começar investigação" },
    { to: "interviewing", who: "owner", label: "Passar a entrevistas" },
    { to: "writing", who: "owner", label: "Começar a escrever" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  researching: [
    { to: "interviewing", who: "owner", label: "Passar a entrevistas" },
    { to: "writing", who: "owner", label: "Começar a escrever" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  interviewing: [
    { to: "writing", who: "owner", label: "Começar a escrever" },
    { to: "researching", who: "owner", label: "Voltar à investigação" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  writing: [
    { to: "in_review", who: "owner", label: "Enviar para revisão" },
    { to: "interviewing", who: "owner", label: "Voltar a entrevistas" },
    { to: "researching", who: "owner", label: "Voltar à investigação" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  in_review: [
    { to: "approved", who: "desk", label: "Aprovar" },
    { to: "writing", who: "owner", label: "Devolver à redação" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  approved: [
    { to: "published", who: "desk", label: "Publicar agora" },
    { to: "scheduled", who: "desk", label: "Agendar" },
    { to: "in_review", who: "desk", label: "Reabrir revisão" },
    { to: "archived", who: "desk", label: "Arquivar" },
  ],
  scheduled: [
    { to: "published", who: "desk", label: "Publicar agora" },
    { to: "approved", who: "desk", label: "Cancelar agendamento" },
    { to: "in_review", who: "desk", label: "Reabrir revisão" },
  ],
  published: [{ to: "archived", who: "desk", label: "Retirar e arquivar" }],
  archived: [
    { to: "idea", who: "desk", label: "Reabrir como ideia" },
    { to: "published", who: "desk", label: "Voltar a publicar" },
  ],
};

export interface StoryActors { assigneeId?: string | null; authorId?: string | null; createdBy?: string | null }

export function isOwner(userId: string | undefined, s: StoryActors): boolean {
  return !!userId && [s.assigneeId, s.authorId, s.createdBy].includes(userId);
}

/** Ideia sem dono (veio de um agente ou do radar): qualquer redactor pode adoptá-la ao propô-la. */
export const isUnowned = (s: StoryActors): boolean => !s.assigneeId && !s.authorId && !s.createdBy;

function allowed(who: Who, role: Role | undefined, owner: boolean): boolean {
  if (!canWrite(role)) return false;
  if (isDesk(role)) return true;
  return who === "owner" && owner;
}

/** Transições que este utilizador pode pedir a partir do estado actual. */
export function nextSteps(from: State, role: Role | undefined, userId: string | undefined, s: StoryActors): Rule[] {
  const owner = isOwner(userId, s) || (from === "idea" && isUnowned(s));
  return RULES[from].filter((r) => allowed(r.who, role, owner));
}

export function canTransition(from: State, to: State, role: Role | undefined, userId: string | undefined, s: StoryActors): boolean {
  return nextSteps(from, role, userId, s).some((r) => r.to === to);
}

export const isState = (v: unknown): v is State => typeof v === "string" && (STATES as readonly string[]).includes(v);
