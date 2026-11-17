/** Quem actua numa transacção. É este contexto que a base de dados usa para decidir o que cada um vê e faz. */
export type Role = "admin" | "director" | "editor" | "journalist" | "contributor" | "reviewer";
export type ActorKind = "human" | "agent" | "system" | "public";

export interface Ctx {
  publicationId: string;
  kind: ActorKind;
  userId?: string;
  role?: Role;
  /** Nome a mostrar no histórico (pessoa, agente ou tarefa do sistema). */
  label?: string;
}

export const ROLES: Role[] = ["admin", "director", "editor", "journalist", "contributor", "reviewer"];

export const ROLE_LABEL: Record<Role, string> = {
  admin: "Administração",
  director: "Direção editorial",
  editor: "Edição",
  journalist: "Jornalista",
  contributor: "Colaboração",
  reviewer: "Leitura e revisão",
};

export const isLead = (r?: Role) => r === "admin" || r === "director";
export const isDesk = (r?: Role) => isLead(r) || r === "editor";
export const canWrite = (r?: Role) => r !== undefined && r !== "reviewer";

export const humanCtx = (publicationId: string, userId: string, role: Role, label = ""): Ctx =>
  ({ publicationId, kind: "human", userId, role, label });
export const publicCtx = (publicationId: string): Ctx => ({ publicationId, kind: "public" });
export const systemCtx = (publicationId: string, label = "sistema"): Ctx => ({ publicationId, kind: "system", label });
export const agentCtx = (publicationId: string, label: string): Ctx => ({ publicationId, kind: "agent", label });
