# Fase 3.1 — IA Comercial do ChatbotSullato — Status

> Para retomar em uma nova sessão: **"Leia FASE_3_1_STATUS.md e continue a Fase 3.1 do ponto onde paramos."**

Última atualização: 2026-09-01. HEAD em produção/homologação: commit `58d6687`.

---

## 1. Objetivo da Fase 3.1

Transformar a IA conversacional do ChatbotSullato (só este bot — não Oficina/Clínica) em uma **assistente comercial de veículos**: reconhecer entrada vinda do site (veículo + URL) ou de redes sociais, conduzir uma conversa comercial curta e natural (uso pretendido, troca, financiamento), qualificar o lead, coletar intenção de visita (dia + período, com validação de expediente) e só então transferir para um vendedor real via o rodízio já existente — sem inventar vendedor, sem formulário, sem a IA escolher quem atende, sem a IA inventar preço/desconto/condição financeira.

Controlada pela feature flag `ASSISTENTE_COMERCIAL_ATIVO` (env var no Render) — **ativa em produção**.

## 2. Arquitetura atual

```
Cliente (WhatsApp) → webhook.py → responder.py: responder()
                                        │
                                        ├─ menu/keywords/handoff genérico (fases 1/2, intocado)
                                        │
                                        └─ texto livre → assistente_comercial.processar_mensagem()
                                                              │
                                                              ├─ identifica veículo/URL/categoria (utilitário/passeio)
                                                              ├─ ROTA D — sinal de VISITA → coleta dia → período → valida expediente
                                                              ├─ ROTA E — contato humano direto / desconto-negociação → qualifica na hora
                                                              ├─ ROTA F — mudança explícita de dia/período (mesmo pós-transferência)
                                                              │
                                             (se qualificado e sem vendedor)
                                                              │
                                        responder.py: _processar_transferencia_vendedor()
                                                              │
                                              vendedores_util()/vendedores_passeio()
                                              (rodízio já existente, _embaralhar_por_janela)
                                                              │
                                              gerar_resumo_lead() (responder_ia.py, via Claude)
                                                              │
                                              template novo_lead_vendedor → texto livre/resumo → confirma ao cliente
```

Se nenhuma rota estruturada dispara, a conversa segue por `responder_com_ia()` (Claude Haiku), com prompt montado por `_montar_system_prompt()`.

## 3. Arquivos envolvidos

| Arquivo | Papel na Fase 3.1 |
|---|---|
| `assistente_comercial.py` | Estado comercial por telefone (`_ESTADOS`, TTL 1h). Detecção de veículo/URL/categoria, rotas D/E/F, coleta de dia/período, validação de expediente/domingo fechado, setters `definir_vendedor()`/`marcar_transferencia_concluida()`. Isolado — só é importado por `responder.py`. |
| `responder_ia.py` | Monta o system prompt (`_montar_system_prompt`): `_SISTEMA_BASE` (fases 1/2, intocado) + blocos aditivos comerciais/visita/horário/transferência-concluída. `gerar_resumo_lead()` gera o resumo real para o vendedor a partir do histórico. |
| `responder.py` | `responder()` — fluxo principal. `_processar_transferencia_vendedor()` faz o handoff completo (categoria → rodízio → template → texto livre → confirmação). Rodízio: `VENDEDORES_UTIL_BASE`/`VENDEDORES_PASSEIO_BASE`, `_embaralhar_por_janela()`, `vendedores_util()`/`vendedores_passeio()` — pré-existentes, reaproveitados sem alteração de algoritmo. |
| `webhook.py` | Entrypoint real (Procfile `gunicorn webhook:app`). Não alterado nesta fase. |

## 4. Estado atual homologado

- **IA comercial de veículos ativa**, identifica o veículo a partir da mensagem/link vindo do site.
- **Conversa comercial curta** (instrução de brevidade em `responder_ia.py`, sem tocar `_SISTEMA_BASE`).
- **IA nunca inventa preço, desconto ou condição financeira** — reconhece o que o cliente informa (à vista, entrada, financiamento, parcelas, troca, desconto) de forma neutra, sem avaliar/elogiar como boa/forte/vantajosa.
- **Pedidos comerciais fortes são encaminhados ao vendedor**: pedido explícito de vendedor ("quero falar com vendedor", "me passe um vendedor", "quem pode me atender?"), intenção comercial forte (compra à vista, "quero fechar", "quero comprar") e pedido de desconto/negociação ("quero desconto", "tem desconto?", "qual o melhor preço?", "tem negociação?") acionam a **mesma camada estruturada** de transferência (`_eh_sinal_transferencia()`), sem a IA interrogar o cliente sobre orçamento/uso/urgência antes de transferir.
- **Intenção de visita tem prioridade** quando visita e contato comercial aparecem na mesma mensagem (`_eh_sinal_visita()` é checado antes de `_eh_sinal_transferencia()`).
- **Coleta de dia e período da visita** (`estagio_visita`: `None → aguardando_dia → aguardando_periodo → completo`), em turnos separados ou na mesma mensagem.
- Um "sim" isolado só é interpretado como aceite de visita quando a **última mensagem da própria IA** convidou claramente para conhecer o veículo na loja (parâmetro `ultima_mensagem_ia`, via `_HIST_IA`) — nunca presumido de um "sim" sem esse contexto.
- **Validação de horário de funcionamento** por operação, e **domingo fechado nas três operações**:

  | Operação | Segunda a sexta | Sábado |
  |---|---|---|
  | Utilitários | 9h–18h | 9h–14h |
  | Passeio | 9h–18h | 9h–17h |
  | Oficina* | 9h–18h | 9h–13h |

  \* Oficina documentada por completude — `categoria` do assistente comercial só produz `"utilitario"`/`"passeio"`; o fluxo de oficina/peças roda por menu separado, não pela IA comercial.

  Horário fora do expediente não é confirmado — a IA informa o expediente correto e pede novo horário (`aviso_horario`/`aviso_dia`). Mudança de dia/período só ocorre com pedido explícito do cliente ("mudar", "trocar", "prefiro", "melhor", "não consigo") — mensagens neutras ("ok", "obrigado") nunca alteram dado já registrado.
- **Vendedor escolhido exclusivamente pelo rodízio existente** (`vendedores_util()`/`vendedores_passeio()`/`_embaralhar_por_janela()` — algoritmo intocado).
- **Vanessa removida** de `VENDEDORES_PASSEIO_BASE` (confirmado explicitamente por Anderson).
- **Vinicius corrigido** para `5511911260469` (estava com número divergente).
- **Template `novo_lead_vendedor` ativo** (Utilidade, pt_BR, 5 variáveis de corpo: nome, telefone sem "+"/"55", veículo, resumo, visita) — enviado ao vendedor **antes** do texto livre, para abrir/reabrir a janela de conversa.
- **Parâmetros do template sanitizados** (quebras de linha/tabs/espaços duplicados removidos antes do envio).
- **Fallback para texto livre preservado**: falha no template só é logada, nunca bloqueia a transferência.
- **Proteção contra segunda transferência**: idempotente por telefone — vendedor e template não se repetem após `transferencia_concluida=True`; perguntas factuais pós-transferência (endereço, horário, "domingo abre?") são respondidas normalmente sem reabrir a qualificação.
- **Resumo real enviado ao vendedor** (`gerar_resumo_lead()`, a partir do histórico real, nunca inventado).
- **Cliente recebe nome e WhatsApp do vendedor** já selecionado (nunca escolhido pela IA).

## 5. Homologação real confirmada em produção

Teste mais recente: cliente informou intenção de compra à vista.
```
Backend reconheceu intenção comercial forte
  → selecionou vendedor pelo fluxo estruturado (rodízio)
  → vendedor selecionado no teste: Solange Ap.
  → enviou template novo_lead_vendedor → Meta HTTP 200
  → enviou mensagem/resumo complementar ao vendedor → Meta HTTP 200
  → enviou confirmação ao cliente → Meta HTTP 200
```
Fluxo principal de transferência comercial (identificação → intenção forte → rodízio → template → resumo → confirmação) **validado em produção de ponta a ponta**.

Testes anteriores no mesmo dia também confirmaram em produção: Peugeot Boxer + troca (VW Kombi 2012, ~100 mil km) + uso comercial + "quarta-feira" + "de manhã" → handoff correto com resumo e confirmação ao cliente.

## 6. Commits da Fase 3.1 (mais recente primeiro)

| Commit | Mensagem |
|---|---|
| `58d6687` | fix: direciona pedidos de desconto para vendedor |
| `6135b80` | fix: neutraliza avaliacoes financeiras da IA comercial |
| `71d3fcf` | fix: cobertura de pedido de vendedor, "sim" contextual e restricoes de preco/financeiro |
| `a5cdc2c` | fix: bloqueia domingo e estabiliza fluxo pos-transferencia |
| `c44612a` | fix: valida horario de visitas e remove Vanessa da rotacao |
| `cf10f85` | fix: sanitiza template de vendedor e corrige telefone do Vinicius |
| `fdfd228` | feat: envia template novo_lead_vendedor antes do resumo comercial |
| `75b0d23` | fix: reduz verbosidade da IA comercial (blocos aditivos, sem tocar _SISTEMA_BASE) |
| `1f0c35f` | fix: reconhece "quando posso ir"/"quando eu for" como sinal de visita |
| `a1f8be4` | feat: coleta dia/periodo da visita antes de transferir e confirmacao natural ao cliente |
| `3689f12` | fix: classificacao por origem do lead e IA nao desiste da venda cedo |
| `22466cb` | fix: transferencia de vendedor dispara antes da IA e respeita loja de origem |
| `8d7a4ae` | feat: fecha ciclo do lead comercial (Fase 3.1D) - selecao de vendedor pelo backend |
| `6b16e03` | fix: bloco comercial da IA proibe citar telefone/e-mail nesta fase |
| `3cbb483` | fix: assistente comercial reconhece entrada real de anuncio sem URL detectada |
| `8eceb37` | Fase 3.1 - assistente comercial com contexto de veiculo |

**HEAD atual: `58d6687`** (main, sincronizada com `origin/main`).

## 7. Pendência para amanhã — investigar, NÃO corrigir sem análise isolada

**Erro observado no Render (não bloqueante):**
```
Erro ao atualizar interesse no Google Sheets: expected str, bytes or os.PathLike object, not NoneType
```
Não impediu atendimento, transferência, template, resumo ao vendedor nem resposta ao cliente — é um erro isolado na gravação de interesse no Sheets (path/objeto `None` em algum ponto de `atualizar_interesse`/`atualizar_google_sheets.py`). **Investigar isoladamente a origem do `NoneType` antes de alterar qualquer coisa.**

Também continuar homologando frases reais diferentes de clientes antes de ampliar qualquer lógica nova.

Itens de backlog mais antigos, ainda válidos:
- Avaliar reforçar "normalmente uma pergunta por mensagem" se a IA voltar a fazer duas perguntas na mesma mensagem no início da conversa.
- Não mexer no rodízio de vendedores só por um vendedor aparecer repetido nos testes — investigar a janela de distribuição (`_embaralhar_por_janela`, slots de 6h) antes de presumir viés.
- Não existe calendário real de disponibilidade — a IA pode dizer que vai "deixar a visita organizada", mas nunca deve inventar disponibilidade real ou confirmar reserva sem backend de agenda.

## 8. Pontos que NÃO devem ser alterados sem nova análise

- `vendedores_util()`, `vendedores_passeio()`, `_embaralhar_por_janela()`, `VENDEDORES_UTIL_BASE`, `VENDEDORES_PASSEIO_BASE`
- Remoção da Vanessa / telefone do Vinicius (`5511911260469`)
- `_SISTEMA_BASE` (prompt-base, fases 1/2)
- `_HIST_IA` (histórico de conversa)
- Template `novo_lead_vendedor`, seus 5 parâmetros, sanitização e fallback
- Validação de expediente/domingo fechado
- Google Sheets / CRM (inclusive a duplicação de linhas na "Página1" e o erro `NoneType` do item 7 — diagnosticados, não corrigidos, tratados à parte)
- `webhook.py`
- Menu, áudio, templates Meta (demais), janela de 24h
- Identificação atual do veículo, fluxo de troca, fluxo de financiamento, endereço por categoria
- Qualquer outro fluxo homologado fora do escopo desta fase

---

### Observação sobre Render

Auto-deploy está **desativado** — deploys são sempre Manual Deploy feitos por Anderson no painel do Render. Claude Code não tem e não deve tentar acesso ao Render.
