# O que é uma competência e o que pertence aqui

Uma **competência** é uma instrução que um modelo deve seguir, gerida aqui, com versões, e oferecida às aplicações que
precisam dela. Um cliente MCP recebe-a como **prompt** (`prompts/get`, com os argumentos preenchidos) e como
**recurso** (`skill://nome`, o texto tal como foi escrito).

## O que pertence aqui

Instruções que **vários** consumidores têm de aplicar da **mesma forma**, e que alguém tem de poder alterar num só
lugar:

- a convenção de citação das passagens da base de conhecimento (`cite_with_tag`);
- a regra do português europeu (`pt_pt_style`);
- o aviso de que uma resposta foi gerada por um modelo (`ai_generated_disclosure`).

## O que não pertence aqui

O **prompt de sistema** de uma aplicação, afinado para o seu modelo e medido nos seus próprios testes. Os prompts do
Cortex e do Slides ficam nos seus repositórios.

## As partes de uma competência

- **Conteúdo** — a instrução, em Markdown. `{{nome}}` marca um argumento.
- **Argumentos** — o que um cliente pode preencher (`kb_tool`, por exemplo), cada um com uma descrição, se é
  obrigatório e um valor por omissão.
- **Aplicações** — quem a recebe. **Espera as ferramentas** — as ferramentas a que a instrução se refere; a consola
  avisa quando uma aplicação não as recebe aqui (podem ser da própria aplicação). **Etiquetas** — para a encontrar.

## Ver também
- [Criar uma competência](03-02-create-a-skill.md)
- [Experimentar uma competência](03-03-try-a-skill.md)
