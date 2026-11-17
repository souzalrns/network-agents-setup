export const FORMATS = ["reportagem", "notícia", "explicador", "entrevista", "agenda", "podcast", "vídeo", "opinião", "crónica"];
export const CLAIM_KIND_LABEL: Record<string, string> = {
  fact: "Facto documentado", statement: "Declaração", inference: "Inferência", unconfirmed: "Não confirmada",
};
export const CLAIM_KIND_HELP: Record<string, string> = {
  fact: "Só fica verificado com evidência e por uma pessoa.",
  statement: "Diz sempre quem declarou.",
  inference: "Apresenta-se como hipótese.",
  unconfirmed: "Não pode ir no artigo: bloqueia a aprovação.",
};
export const VERIFICATION_LABEL: Record<string, string> = {
  pending: "Por verificar", verified: "Verificada", disputed: "Contestada", unsupported: "Sem suporte",
};
export const USAGE_LABEL: Record<string, string> = { on_record: "Identificada", background: "Contexto", off_record: "Sob anonimato" };
export const CONF_LABEL: Record<string, string> = { public: "Pública", internal: "Interna", protected: "Protegida" };
export const CHANNEL_LABEL: Record<string, string> = { instagram: "Instagram", youtube: "YouTube", podcast: "Podcast", newsletter: "Newsletter", other: "Outro" };
export const DIST_STATE_LABEL: Record<string, string> = {
  draft: "Rascunho", in_review: "Em revisão", approved: "Aprovado", handed_off: "Enviado ao agendador", published: "Publicado", discarded: "Descartado",
};
export const OUTPUT_KIND_LABEL: Record<string, string> = {
  story_suggestions: "Sugestões de pautas", research_dossier: "Dossiê de investigação", factcheck_report: "Relatório de verificação",
  edit_review: "Revisão assistida", distribution_pack: "Pacote de distribuição",
};
