# ZÉRO DAY: SWARM TRADING

<p align="center">
  <img src="assets/images/title-art.svg" alt="Zéro Day — arte de capa" width="100%" />
</p>

<p align="center">
  <strong>Construa. Gerencie. Multiplique.</strong><br/>
  Plataforma cyberpunk de gerenciamento de agentes autônomos de trading, com cliente 2D e conectores financeiros/IA.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Pygame-2D%20Prototype-00E991" alt="Pygame 2D" />
  <img src="https://img.shields.io/badge/Trading-Live%20Adapter%20Guarded-00C7D9" alt="Adaptador de trading com execução protegida" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

## Visão geral

Você administra uma torre futurista do subsolo ao 10º andar. Os agentes podem analisar dados de mercado com modelos configuráveis e propor operações sobre uma conta cripto dedicada. O motor financeiro precisa validar cada proposta antes de qualquer ordem. O mercado sintético existente permanece disponível apenas como ambiente de desenvolvimento.

<p align="center">
  <img src="assets/images/gameplay-overview.svg" alt="Demonstração conceitual de gameplay e interface" width="100%" />
</p>


> **Status financeiro:** o repositório inclui adaptadores iniciais para modelos OpenAI-compatible e exchanges via CCXT. Eles não criam uma carteira e não estão prontos para produção. Ordens reais ficam bloqueadas por padrão; nunca use chaves com permissão de saque.

## Funcionalidades implementadas

- Mercado sintético de BTC, ETH, SOL e NOVA.
- Indicadores EMA 8/21, RSI 14, momentum e volatilidade.
- Decisões autônomas: COMPRAR, VENDER ou ESPERAR.
- Perfis de risco conservador, moderado e agressivo.
- Robôs com caixa, posição e estratégia independentes.
- Taxa simulada, preço médio, stop-loss e take-profit.
- Reprodução ao atingir 100% de rendimento: patrimônio dividido em dois.
- Morte permanente por saldo abaixo do limite de sobrevivência; robô enviado ao andar -2.
- Painel de saldo, população, lucro/prejuízo diário e feed de eventos.
- Visão da torre e navegação pelos andares.
- Testes automatizados do núcleo da simulação.

## Andares

| Andar | Setor | Função |
|---:|---|---|
| 10 | Direção | Capital, metas e política de risco |
| 9 e 8 | Dormitórios | Descanso e recuperação |
| 7 | Esportes | Treinamento e upgrades futuros |
| 6 e 4 | Laboratórios | Estratégias e processamento |
| 5 | Salas de aula | Pesquisa e experimentos |
| 3 | Vida escolar | Administração e enfermaria |
| 2 | Cantina | Pausa e recarga |
| 1 | Hall principal | Recepção e acesso |
| -1 | Sala de controle | Mercado e saúde financeira |
| -2 | Sala abandonada | Agentes desativados |

## Lógica de trading

O agente observa EMA curta/longa, RSI, momentum e volatilidade. Compra quando tendência e momentum estão alinhados e o RSI está na faixa do perfil. Vende ao atingir stop-loss, take-profit ou quando detecta perda de tendência. Sem sinal consistente, espera.

| Perfil | Alocação por entrada | Stop-loss | Take-profit |
|---|---:|---:|---:|
| Conservador | 18% | 7% | 12% |
| Moderado | 32% | 12% | 20% |
| Agressivo | 55% | 20% | 32% |

Ao atingir 2x o capital de nascimento, o robô divide seu patrimônio em dois agentes. Como operações sem alavancagem não costumam levar um saldo positivo exatamente a zero, o protótipo considera saldo inferior a ₡ 0,50 como falência efetiva.

Veja a explicação detalhada em [docs/TRADING_LOGIC.md](docs/TRADING_LOGIC.md).

## Instalação

### Windows (PowerShell)

```powershell
git clone https://github.com/stylesxzz/Zero-Day.git
cd Zero-Day
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

### Linux / Ubuntu / Kali

```bash
git clone https://github.com/stylesxzz/Zero-Day.git
cd Zero-Day
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### Termux (Android)

O Pygame precisa de uma camada gráfica. O protótipo atual é desktop; em Termux, use Termux:X11 e instale as dependências SDL/X11 antes.

```bash
pkg update && pkg upgrade
pkg install python git clang make pkg-config sdl2 sdl2-image sdl2-mixer sdl2-ttf
git clone https://github.com/stylesxzz/Zero-Day.git
cd Zero-Day
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Configuração e execução

```bash
# Capital fictício de 25 mil, 12 robôs e risco moderado
python main.py --capital 25000 --robots 12 --risk moderado

# Execução reprodutível
python main.py --capital 5000 --robots 6 --seed 42

# Rodar 2.000 ticks sem abrir janela
python main.py --capital 10000 --robots 8 --headless-ticks 2000
```

## Controles

| Ação | Controle |
|---|---|
| Pausar / retomar | Espaço ou botão PAUSAR |
| Risco conservador / moderado / agressivo | Teclas 1 / 2 / 3 |
| Voltar à visão da torre | B ou botão do setor |
| Entrar em um andar | Clique no andar à direita |
| Criar robô | Botão + CRIAR ROBÔ |
| Sair | Esc |

## Testes

```bash
python -m unittest discover -s tests -v
```

## Arquitetura

```text
Zero-Day/
├── main.py
├── zeroday/
│   ├── backend/        # FastAPI, SQLite, dados reais e carteiras read-only
│   ├── providers/      # adaptador OpenAI-compatible
│   ├── execution/      # risco e executor fail-closed (ordens bloqueadas)
│   ├── web/            # painel cyberpunk responsivo ligado à API
│   ├── config.py       # parâmetros, risco e andares
│   ├── models.py       # entidades e estados
│   ├── market.py       # mercado sintético para desenvolvimento
│   ├── trading.py      # estratégia do protótipo
│   ├── simulation.py   # ciclo de vida do protótipo
│   └── ui.py           # interface Pygame 2D
├── docs/
├── tests/
├── assets/images/
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── LICENSE
```

O núcleo foi isolado do Pygame para permitir uma futura migração visual para Godot 2D ou cliente Web sem reescrever as regras. Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Integração financeira e de IA

- [Arquitetura de trading real](docs/REAL_TRADING_ARCHITECTURE.md).
- [Exemplo de configuração](.env.example).
- [Adaptador de IA configurável](zeroday/providers/llm.py).
- [Adaptador spot CCXT com bloqueio de ordens por padrão](zeroday/execution/exchange.py).
- [Validações iniciais de risco](zeroday/execution/risk.py).

O adaptador de IA aceita serviços compatíveis com OpenAI Chat Completions. APIs proprietárias precisam de adaptadores próprios; não existe compatibilidade universal automática com literalmente qualquer API.

## Próximas versões

- Migração de SQLite para PostgreSQL para implantações multiusuário.
- Interiores exclusivos, sprites animados e sons por andar.
- Metas de lucro, upgrades, pesquisa e filiais com mapa próprio.
- Eventos de mercado, replay histórico e campanhas.
- Autenticação, autorização e proxy seguro para acesso remoto.

## Licença

Distribuído sob a licença [MIT](LICENSE).


## Backend conectado (dados reais, sem envio de ordens)

O repositório agora inclui uma API FastAPI e um painel web responsivo, separados do protótipo Pygame. A aplicação consulta preços públicos, mantém agentes e propostas em SQLite, consulta saldo de exchange (se configurado) e lê o saldo nativo de endereços EVM públicos. **Não assina transações on-chain, não movimenta fundos e não envia ordens de exchange.**

### Executar o backend local

Linux / Kali / Termux com Python compatível:

```bash
cp .env.example .env
# Edite .env localmente; nunca cole chaves no GitHub.
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn zeroday.backend.api:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000. A documentação interativa da API fica em http://127.0.0.1:8000/docs.

### Configurar mais de um provedor de IA

O modo simples usa `ZERO_DAY_AI_BASE_URL`, `ZERO_DAY_AI_API_KEY` e `ZERO_DAY_AI_MODEL`. Para perfis múltiplos, defina `ZERO_DAY_AI_PROVIDERS_JSON` no arquivo `.env` como uma lista JSON, por exemplo:

```json
[
  {"id":"openai","name":"OpenAI","base_url":"https://api.openai.com/v1","model":"MODEL_ID","api_key_env":"ZERO_DAY_OPENAI_API_KEY"},
  {"id":"gateway","name":"Meu gateway compatível","base_url":"https://gateway.example/v1","model":"MODEL_ID","api_key_env":"MY_GATEWAY_API_KEY"}
]
```

Adicione `ZERO_DAY_OPENAI_API_KEY=` e `MY_GATEWAY_API_KEY=` ao `.env` local. Use IDs reais de modelos disponibilizados pelo provedor. O protocolo esperado é OpenAI Chat Completions; APIs com formatos proprietários precisam de adaptadores específicos. A API nunca devolve os valores das chaves, apenas o nome da variável de ambiente.

### Conectar as duas carteiras separadamente

- **Exchange:** configure `ZERO_DAY_EXCHANGE_ID`, `ZERO_DAY_EXCHANGE_API_KEY` e `ZERO_DAY_EXCHANGE_SECRET`. Nesta versão o backend só consulta saldo; crie uma chave com permissão de leitura, sem trading e sem saque, quando a exchange permitir.
- **Carteira on-chain:** configure uma URL RPC para a rede desejada (`ZERO_DAY_RPC_ETHEREUM`, `ZERO_DAY_RPC_BASE`, `ZERO_DAY_RPC_POLYGON`, `ZERO_DAY_RPC_ARBITRUM`, `ZERO_DAY_RPC_OPTIMISM` ou `ZERO_DAY_RPC_BSC`). Informe no painel somente o endereço público 0x. O conector lê apenas o saldo do ativo nativo; não consulta tokens ERC-20 nesta versão.

### Docker

```bash
cp .env.example .env
# Edite .env localmente
docker compose up --build -d
```

O Compose publica a porta apenas em `127.0.0.1:8000`. Não exponha a API diretamente à internet: autenticação, autorização e um proxy seguro ainda precisam ser implementados antes de acesso remoto.

### Rotas principais

- `GET /api/health` e `GET /api/status` — estado do serviço.
- `GET/POST /api/agents` — listar e criar agentes.
- `POST /api/agents/{id}/analyze` — consultar mercado e criar uma proposta da IA.
- `GET /api/proposals` e `GET /api/events` — histórico persistido.
- `GET /api/market/ticker` — ticker público da exchange.
- `GET /api/wallet/exchange` — consulta de saldo da exchange.
- `POST /api/wallet/onchain` — consulta de saldo nativo por endereço público.
- `GET /api/providers` — perfis sanitizados de provedores.
- `POST /api/orders/execute` — retorna HTTP 423; execução real está deliberadamente bloqueada.

As propostas de IA são texto não confiável e nunca viram ordens automaticamente. O sistema ainda precisa de autenticação, ledger contábil robusto, idempotência, reconciliação de fills, limites de risco ligados à execução, testes em sandbox e revisão independente antes de qualquer trading real.
