# Criar uma ferramenta

Uma ferramenta é uma **entrada do catálogo**: um nome, uma descrição, que **implementação** incluída no serviço a
executa, o seu esquema, o seu nível e as aplicações a que está oferecida. A consola nunca escreve código: as
implementações vêm com o serviço, e uma ferramenta liga-se a uma delas.

## Passos

1. Clique em **+ Nova ferramenta** (vista Ferramentas) ou em **Catálogo** › **Nova ferramenta…**.
2. Dê-lhe um **nome** (letras, algarismos, sublinhados; não pode mudar depois) e um nome apresentado.
3. Escreva a **descrição** que o modelo vai ler: o que a ferramenta faz e quando usá-la.
4. Liste as **aplicações** a que é oferecida, separadas por vírgulas. A aplicação do filtro das Ferramentas é proposta.
5. Escolha o **nível** (*leitura* ou *escrita*), a **execução** (*servidor*, ou *cliente* para uma ferramenta que a
   página da aplicação executa) e a **implementação** na lista; para uma ferramenta de cliente, indique o id da
   implementação do próprio cliente.
6. Numa ferramenta de escrita, marque **destrutiva** se remove ou substitui algo; marque **idempotente** se chamá-la
   duas vezes é o mesmo que uma.
7. Escreva o **esquema de entrada** (JSON Schema): as propriedades, os tipos, as descrições, os valores por omissão e a
   lista `required`. Um **esquema de saída** é opcional. A **configuração** guarda definições por ferramenta que a
   implementação lê.
8. Clique em **Guardar…**: o registo a criar é mostrado; clique em **Guardar ferramenta**.

## Notas

- Um esquema que não seja JSON Schema válido é recusado com o motivo.
- A nova ferramenta é a versão 1; cada gravação posterior acrescenta uma versão ao seu **Histórico**.

## Ver também
- [Editar uma ferramenta](02-05-edit-a-tool.md)
- [Oferecer uma ferramenta a outra aplicação](02-07-offer-a-tool-to-another-app.md)
