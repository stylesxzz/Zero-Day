# Arquitetura de trading real — Zéro Day

O projeto passa a planejar operações reais por meio de uma conta cripto dedicada. A torre 2D é o painel de gerenciamento; o mercado sintético existente permanece apenas como ambiente de desenvolvimento.

## Componentes
- Cliente 2D: torre, andares, agentes, ordens, saúde e feed de eventos.
- API de aplicação: autenticação, configurações, logs e comandos de gestão.
- Orquestrador: agenda agentes isolados e aplica limites antes de qualquer ordem.
- Adaptadores de IA: endpoint OpenAI-compatible configurável por URL, chave e modelo.
- Dados de mercado: tickers/preços da exchange com verificação de frescor.
- Adaptador financeiro: CCXT para exchanges suportadas, saldo e ordens spot.
- Ledger persistente: SQLite para desenvolvimento; PostgreSQL recomendado para operação contínua.
- Worker e monitoramento: execução persistente, alertas, recuperação e kill switch.

## Carteira dedicada e segurança
Para a primeira integração, use uma subconta exclusiva de uma exchange ou conta dedicada com saldo pequeno. Crie uma API key sem permissão de saque/transferência; habilite apenas leitura e spot trading necessários; configure allowlist de IP quando disponível. Não compartilhe seed phrase de carteira autocustodial com agentes e não envie chaves privadas para provedores de IA.

O código atual não cria carteira, não deposita dinheiro e não opera automaticamente ao iniciar. O adaptador exige duas flags para enviar ordens reais, símbolo permitido e teto por ordem. Isso é uma barreira inicial, não uma auditoria nem garantia contra perdas. Mantenha a execução desativada até concluir testes, revisão independente e configuração dos limites.

## Decisão de IA não é autorização financeira
1. O modelo recebe um snapshot minimizado e retorna uma proposta estruturada.
2. Um parser estrito rejeita respostas fora do esquema; texto livre nunca é executado como ordem.
3. O motor determinístico verifica símbolo, lado, quantidade, exposição, posição e perda diária.
4. O executor revalida preço e saldo antes da ordem.
5. A resposta da exchange é reconciliada com fills e taxas reais.
6. O ledger e o painel registram modelo, proposta, ordem, resultado e motivo de bloqueio.

O modelo não recebe chaves financeiras nem ferramentas de saque. Trate a saída como não confiável. Produção ainda exige idempotência, proteção contra ordens duplicadas, slippage máximo, limites de frequência e parada automática em caso de dados obsoletos ou desconexão.

## Configuração local
1. Instale as dependências com pip install -r requirements.txt.
2. Copie .env.example para .env e preencha apenas localmente.
3. Para IA, use um endpoint compatível com OpenAI Chat Completions.
4. Para finanças, configure uma exchange suportada pelo CCXT e uma chave dedicada sem saques.
5. Mantenha ZERO_DAY_LIVE_TRADING=false durante desenvolvimento e teste.
6. Nunca envie .env, credenciais, seeds ou logs com segredos ao GitHub.

## Compatibilidade de API
"Qualquer API" não pode ser garantido universalmente. O adaptador de IA funciona com serviços que implementam o formato OpenAI Chat Completions. APIs proprietárias precisam de adaptadores específicos. O suporte financeiro depende das exchanges e dos recursos expostos pelo CCXT.

## Ainda necessário antes de produção
- autenticação e armazenamento cifrado de segredos;
- PostgreSQL, migrations e ledger de dupla entrada;
- dados históricos e feeds confiáveis;
- parser JSON/schema estrito para sinais;
- serviço de risco central que agentes não possam contornar;
- reconciliação de ordens parciais, métricas, alertas e backups;
- testes em sandbox/testnet e revisão de segurança independente;
- análise legal, fiscal e dos termos da exchange aplicável.

Este software é infraestrutura experimental, não recomendação financeira. Trading real pode perder todo o capital alocado por bugs, slippage, indisponibilidade ou comprometimento de credenciais.
