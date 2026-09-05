# Fase 3.1 — IA Comercial do ChatbotSullato — Status

> Para retomar em uma nova sessão: **"Leia FASE_3_1_STATUS.md e continue a Fase 3.1 do ponto onde paramos."**

Última atualização: 2026-09-04. HEAD em produção/homologação: commit `09b5f4c` (ver seção 9 — Multi-número Meta).

> **Entre 2026-09-01 (commit `58d6687`) e 2026-09-04 houve uma sequência extensa de correções críticas no assistente comercial (Fases 3.1H a 3.1N — categoria por posição/contraste, vendedor determinístico, isolamento do bloco institucional, colisão com Oficina/Peças, barreira de código contra vendedor inventado) e, na sequência, a Fase 3.1O/3.1P (suporte a múltiplos números Meta no mesmo chatbot). Essas fases não têm seção própria detalhada neste arquivo (ver histórico de commits e memória do projeto) — a seção 9 abaixo documenta o estado mais recente, já homologado em produção.

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
- **(novo, ver seção 9)** Roteamento por `sender_phone_number_id` (`webhook.py`: extração de `metadata.phone_number_id`; `responder.py`: propagação em todos os envios ao cliente; `assistente_comercial.py`: `_chave_estado()`/`_chave_hist()`) — não alterar sem evidência real de problema.

---

## 9. Multi-número Meta (94054 / 2030 / 2542) — Homologação 04/09/2026

### 9.1 Estado operacional

O chatbot do Grupo Sullato está atualmente operando com **3 números de produção na mesma estrutura Meta/WABA** ("Grupo Sullato Chatbot's"), todos apontando para o **mesmo serviço Render, o mesmo webhook e a mesma base de código** — não são três chatbots, são três portas de entrada para o mesmo chatbot:

| Número | Variável de ambiente |
|---|---|
| 94054 (original) | `PHONE_NUMBER_ID` |
| 2030 | `PHONE_NUMBER_ID_2030` |
| 2542 | `PHONE_NUMBER_ID_2542` |

- Os três números executam **exatamente a mesma lógica**: menus e botões, IA, identificação de categoria (passeio/utilitário) pelo conteúdo da conversa, assistente comercial, seleção/rodízio de vendedor, oficina/peças, visita/agendamento, financiamento/troca e informações institucionais (endereços, horários, redes sociais, site, Maps, "quem criou o chatbot").
- **Roteamento de saída é dinâmico**, baseado em `metadata.phone_number_id` recebido no webhook da Meta (`webhook.py`) — não há nenhuma lista/comparação fixa de números no código de produção. Cada número responde sempre por si mesmo (nunca por outro).
- **Isolamento de sessão**: a chave de estado/histórico passou a ser composta por `(sender_phone_number_id, numero_do_cliente)` (`assistente_comercial._chave_estado()`, `responder._chave_hist()`). O mesmo telefone de cliente pode conversar simultaneamente com os três números sobre assuntos diferentes sem misturar categoria, vendedor, handoff, contexto de IA ou histórico.
- **`PHONE_NUMBER_ID` (94054) continua como fallback** para qualquer chamada antiga que não informe `sender_phone_number_id` — compatibilidade total mantida.
- **Notificações a vendedor/atendente permanecem na regra já existente** (saem pelo `PHONE_NUMBER_ID` padrão, decisão consciente documentada no código — template `novo_lead_vendedor` aprovado por número/WABA, sem confirmação de que vale para os números novos) — **não alterada** só por existirem múltiplos números.
- O número empresarial receptor determina **somente** (1) por qual número a resposta sai e (2) a chave de isolamento — nunca influencia categoria, seleção de vendedor ou conteúdo da IA (auditado exaustivamente: nenhuma função de decisão comercial recebe `sender_phone_number_id`/`numero` como parâmetro).

### 9.2 Testes automatizados de regressão (todos passando)

```
teste_assistente_comercial.py                    11/11 OK
teste_fase31h_categoria_independente.py           7/7 OK
teste_regressao_van_passeio_real.py               3/3 OK
teste_regressao_sprinter_mercedes_real.py         5/5 OK
teste_regressao_utilitario_para_passeio_real.py   4/4 OK
teste_regressao_oficina_vendedor_pendente.py      7/7 OK
teste_regressao_vendedor_vs_institucional.py      5/5 OK
teste_regressao_multiplos_numeros_meta.py         6/6 OK na rodada inicial (94054+2030),
                                                   ampliado depois com o terceiro número (2542)
                                                   e os casos de ciclo comercial/paridade funcional
```

Testes específicos de múltiplos números comprovaram (100% mockado — zero mensagens reais durante os testes):
- número A (94054) recebe → responde pelo 94054;
- número B (2030) recebe → responde pelo 2030;
- número C (2542) recebe → responde pelo 2542;
- mesmo cliente conversando simultaneamente nos três números → estados completamente independentes (categoria, vendedor, histórico);
- chamada antiga sem `sender_phone_number_id` → cai no `PHONE_NUMBER_ID` padrão (fallback preservado);
- categoria PASSEIO seleciona vendedor corretamente (lista/rodízio de passeio) nos três números;
- categoria UTILITÁRIO seleciona vendedor corretamente (lista/rodízio de utilitários) nos três números;
- **vendedor informado ao cliente é sempre o mesmo que recebe o lead/resumo** (verificado nos três números, inclusive com conversas entrelaçadas/concorrentes);
- resumo/lead é gerado e enviado corretamente nos três números;
- conversas simultâneas mantêm categoria, vendedor e estado isolados mesmo quando duas delas são da mesma categoria em números diferentes (rodízio real, sem duplicar vendedor);
- menus e respostas institucionais determinísticas (oficina/peças, endereços, crédito, governamentais, assinatura, trabalhe conosco, listas de veículos por categoria) são **idênticas byte a byte** nos três números;
- "Quem criou o chatbot?" chega à IA com a mesma mensagem/histórico/contexto nos três números — resposta institucional não varia por número;
- endereços, horários, redes sociais, site, Maps, oficina/peças e demais informações institucionais são compartilhados igualmente entre os três;
- a IA em texto livre recebe o mesmo contexto e regras nos três números (nenhuma diferença de conhecimento/instrução por número receptor).

### 9.3 Testes reais em produção (pós-deploy manual)

Deploy feito **manualmente por Anderson no Render** — ficou **Live**. Testes reais realizados nos três números confirmaram:
- os três números responderam corretamente;
- mesma saudação/menu inicial nos três;
- IA funcionando;
- fluxo de passeio e de utilitário funcionando;
- oficina/peças funcionando;
- informações institucionais funcionando;
- registro de contatos na planilha (Google Sheets) funcionando;
- fluxo comercial de utilitário testado com uma van escolar — categoria identificada corretamente;
- vendedor **Silvano** foi selecionado pelo rodízio real em um dos testes e informado corretamente ao cliente;
- em outro teste, **Magali** foi selecionada conforme o estado/fluxo daquela conversa;
- "Quem criou esse chatbot?" continuou respondendo corretamente;
- endereço da **Sullato Micros e Vans** e horário de sábado foram respondidos corretamente quando perguntados explicitamente;
- **nenhuma regressão identificada** que justifique nova alteração de produção neste momento.

### 9.4 Decisão operacional atual (04/09/2026)

**Não alterar mais o código agora.** Os três números ficarão em produção para observação de conversas reais.

Próxima etapa, ao retomar:
1. Analisar o comportamento real dos três números em uso contínuo.
2. Confirmar, em leads reais (não só em teste), que o vendedor informado ao cliente é exatamente o vendedor que recebe o resumo/lead.
3. Observar a distribuição do rodízio real entre vendedores de passeio e de utilitários ao longo do tempo.
4. Verificar se surge qualquer mistura de sessão/estado entre os três números em uso real.
5. **Só depois disso**, revisar/refinar respostas da IA.
6. Evitar alterações preventivas sem evidência de problema real observado.

### 9.5 Commits desta etapa (mais recente primeiro)

| Commit | Mensagem |
|---|---|
| `09b5f4c` | Fase 3.1P: testes de terceiro numero Meta (2542) e paridade funcional |
| `f34606e` | Fase 3.1O: suporte a multiplos Phone Number IDs Meta no mesmo chatbot |
| `779ad97` | Fase 3.1M/3.1N: vendedor deterministico + resposta institucional preservada |
| `6d1364b` | Fase 3.1L: prioriza pedido comercial de vendedor pendente sobre Oficina/Pecas |
| `5d83d08` | Fase 3.1K: corrige handoff entre categorias em linguagem natural do mundo real |
| `891423f` | Fase 3.1J: corrige travamento de categoria, pedido de vendedor, menu e vazamento institucional |
| `f2c36e5` | Fase 3.1I: corrige classificacao van/utilitario e fallback perigoso de categoria |

**HEAD atual: `09b5f4c`** (main, sincronizada com `origin/main`).

---

### Observação sobre Render

Auto-deploy está **desativado** — deploys são sempre Manual Deploy feitos por Anderson no painel do Render. Claude Code não tem e não deve tentar acesso ao Render.
