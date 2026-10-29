# Arquitetura inicial

```text
main.py
  ├── zeroday/ui.py              Pygame: torre, andares, robôs e painéis
  └── zeroday/simulation.py      Orquestra os ticks e o ciclo de vida
        ├── zeroday/market.py    Preços fictícios, EMA, RSI e volatilidade
        ├── zeroday/trading.py   Decisão COMPRAR / VENDER / ESPERAR
        ├── zeroday/models.py    Robô, sinais, eventos e estado da base
        └── zeroday/config.py    Andares, risco, taxas e limites
```

## Decisões importantes

- A simulação não depende do Pygame; pode rodar em modo headless e ser testada com unittest.
- O mercado sintético é uma interface substituível. Uma futura versão pode consumir replay histórico ou serviço de dados somente leitura, mantendo as regras do jogo isoladas.
- O Pygame é a camada visual do protótipo. Para uma versão mais elaborada, a lógica de domínio pode ser portada para um backend Python com API local e cliente Godot 2D.
- SQLite pode ser introduzido para saves, eventos e estatísticas persistentes.

## Próximas etapas

1. Salvar e carregar o estado do edifício.
2. Criar sprites animados e interiores específicos por andar.
3. Implementar metas de lucro, upgrades, pesquisa e desbloqueio de filiais.
4. Adicionar replay de mercado e dificuldade configurável.
5. Expor uma API local para conectar um cliente Godot ou Web.
