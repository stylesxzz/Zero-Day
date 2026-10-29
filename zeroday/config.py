"""Shared configuration for the Zéro Day simulation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskProfile:
    name: str
    buy_rsi_min: float
    buy_rsi_max: float
    allocation_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    description: str


RISK_PROFILES = {
    "conservador": RiskProfile(
        name="Conservador", buy_rsi_min=42.0, buy_rsi_max=62.0,
        allocation_pct=0.18, stop_loss_pct=0.07, take_profit_pct=0.12,
        description="Pouca exposição, entradas seletivas e proteção curta.",
    ),
    "moderado": RiskProfile(
        name="Moderado", buy_rsi_min=35.0, buy_rsi_max=68.0,
        allocation_pct=0.32, stop_loss_pct=0.12, take_profit_pct=0.20,
        description="Equilíbrio entre frequência de operações e proteção.",
    ),
    "agressivo": RiskProfile(
        name="Agressivo", buy_rsi_min=28.0, buy_rsi_max=74.0,
        allocation_pct=0.55, stop_loss_pct=0.20, take_profit_pct=0.32,
        description="Maior exposição e tolerância a oscilações fortes.",
    ),
}

FLOORS = {
    10: ("Direção", "Define metas, capital e política de risco."),
    9: ("Dormitórios femininos", "Descanso e recuperação dos agentes."),
    8: ("Dormitórios masculinos", "Descanso e recuperação dos agentes."),
    7: ("Esportes e treinamento", "Treinamento de desempenho dos robôs."),
    6: ("Laboratório", "Aprendizado e processamento de estratégias."),
    5: ("Salas de aula", "Análise de indicadores e experimentos."),
    4: ("Laboratório", "Testes de algoritmos e validação de sinais."),
    3: ("Vida escolar", "Administração, enfermaria e serviços."),
    2: ("Cantina", "Pausa e recarga dos agentes."),
    1: ("Hall principal", "Recepção, verificação e acesso aos andares."),
    -1: ("Sala de controle", "Mercado simulado, gráficos e saúde financeira."),
    -2: ("Sala abandonada", "Memorial dos agentes desativados."),
}

ASSETS = ("BTC", "ETH", "SOL", "NOVA")
FEE_RATE = 0.001
BANKRUPTCY_FLOOR = 0.50
REPRODUCTION_MULTIPLIER = 2.0
DAY_LENGTH_TICKS = 120
MAX_EVENT_LOG = 80
