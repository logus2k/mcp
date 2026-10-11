# Criar uma competência

## Passos

1. Clique em **+ Nova competência** (vista Competências) ou em **Catálogo** › **Nova competência…**.
2. Dê-lhe um **nome** (não pode mudar depois), um nome apresentado e uma **descrição** de uma linha: para que serve.
3. Liste as **aplicações** a que é oferecida, as **etiquetas** e as **ferramentas** que espera (separadas por
   vírgulas).
4. Declare os seus **argumentos** como uma lista JSON: `[{"name": "kb_tool", "description": "…", "required": false, "default": "…"}]`.
5. Escreva o **conteúdo**: a própria instrução. Escreva `{{kb_tool}}` onde entra um argumento.
6. Clique em **Guardar…**, leia o registo, clique em **Guardar competência**.

## Notas

- Mantenha o conteúdo curto e no imperativo: é lido por um modelo em cada turno.
- Um argumento obrigatório sem valor por omissão faz `prompts/get` recusar uma chamada que não o indique.

## Ver também
- [O que é uma competência e o que pertence aqui](03-01-what-a-skill-is.md)
- [Experimentar uma competência](03-03-try-a-skill.md)
