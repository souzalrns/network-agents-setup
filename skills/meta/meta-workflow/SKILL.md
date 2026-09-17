---
name: meta-workflow
action: meta_workflow
version: 1
role: meta_technique
priority: P0
---

# Skill — meta-workflow

## Trigger

Qualquer tarefa não-trivial que envolva escrever ou alterar código — antes de tocar em qualquer ficheiro.

## Inputs

- O pedido/tarefa a resolver
- Acesso para correr comandos de verificação (testes, build, lint)

## Passos

1. **Objetivo** — define claramente o que precisa de acontecer.
2. **Plano** — esboça a sequência de passos antes de escrever código.
3. **Teste** — identifica como vais verificar que funciona, antes de implementar.
4. **Execução** — implementa.
5. **Revisão** — relê o que fizeste.
6. **Evidência** — corre o comando de verificação NESTA sessão e mostra o output completo. "Devia funcionar" não é prova.

## Done When

- [ ] Os 6 passos foram seguidos, nessa ordem
- [ ] Existe output real de um comando de verificação corrido nesta sessão
- [ ] Nenhuma afirmação de sucesso sem essa evidência anexada

## Anti-padrões

- Complicar uma tarefa simples
- Inventar API que não existe
- Partir algo que já funcionava
- Dizer "pronto" sem testar
- Afirmar sucesso sem evidência fresca

## Knowledge Ref

Adaptado do projecto **obra/superpowers** (MIT) — framework de skills focado em disciplina de processo, não em conhecimento de domínio.
