# Encontrar uma ferramenta

**Ferramentas** lista todas as ferramentas que o serviço oferece, com as aplicações a que estão oferecidas, o nível,
onde correm, a implementação, quando foram usadas pela última vez e quantas chamadas tiveram nas últimas 24 horas.

## Passos

1. Clique em **Ferramentas** no menu lateral (ou prima `/`).
2. Escreva no filtro: corresponde ao nome, à descrição, à implementação e às aplicações.
3. Clique numa aplicação para ver só o que essa aplicação recebe; **leitura** ou **escrita** para ver um nível; **só
   ativas** para esconder o que está desativado.
4. Selecione uma linha: o painel abre na **Visão geral** da ferramenta.

## O que significam as colunas

- **Aplicações** — as aplicações a que a ferramenta está oferecida. A mesma ferramenta é definida uma vez e oferecida a
  várias.
- **Nível** — as ferramentas de *leitura* só consultam; as de *escrita* alteram algo fora do serviço e precisam sempre
  de uma chave ou de um administrador.
- **Execução** — *servidor*: o serviço executa-a; *cliente*: a própria página da aplicação executa-a, e o serviço só
  serve o seu esquema.
- **Última utilização** — do registo; *nunca* significa nenhuma chamada na janela retida; *cliente* significa que o
  serviço nunca a executa.
- **Ativa** — o interruptor; uma ferramenta desativada desaparece da lista de todas as aplicações.

## Ver também
- [Ler o esquema de uma ferramenta](02-02-read-a-tools-schema.md)
- [Experimentar uma ferramenta](02-03-try-a-tool.md)
