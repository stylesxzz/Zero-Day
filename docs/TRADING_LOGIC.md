# Lógica de decisão dos agentes

Cada robô possui caixa, posição, preço médio, perfil de risco, geração e histórico próprios. Ele não compartilha a posição de outro agente.

## Dados analisados

- **EMA 8 e EMA 21:** médias móveis exponenciais para estimar a direção da tendência.
- **RSI 14:** mede a força relativa dos movimentos recentes.
- **Momentum de 5 amostras:** confirma se o preço está acelerando para cima ou para baixo.
- **Volatilidade recente:** bloqueia novas entradas quando as oscilações estão anormalmente altas.
- **Stop-loss e take-profit:** saídas automáticas calculadas a partir do preço médio da posição.

## Regras simplificadas

1. **COMPRAR:** sem posição aberta, EMA curta acima da longa, momentum positivo, RSI dentro da faixa do perfil e volatilidade controlada.
2. **VENDER:** stop-loss atingido, take-profit atingido, RSI excessivamente alto ou tendência de baixa confirmada durante uma posição.
3. **ESPERAR:** sinais conflitantes, tendência de baixa sem posição, mercado lateral ou volatilidade elevada.

| Perfil | Alocação máxima | Stop-loss | Alvo de lucro |
|---|---:|---:|---:|
| Conservador | 18% | 7% | 12% |
| Moderado | 32% | 12% | 20% |
| Agressivo | 55% | 20% | 32% |

Esses percentuais são parâmetros de balanceamento do jogo, não recomendações financeiras.

## Reprodução e morte

Quando o patrimônio alcança duas vezes o capital de nascimento, o agente converte seu patrimônio em caixa e divide em duas metades: uma permanece no agente atual e a outra cria um novo agente. O patrimônio total é preservado no instante da divisão.

Como operações sem alavancagem não costumam levar um saldo matematicamente positivo a exatamente zero, o protótipo usa um limite de sobrevivência de ₡ 0,50. Ao atingir esse valor, o robô é liquidado, marcado como morto e transferido para o andar -2 (Sala Abandonada).

## Limites

O mercado é sintético e gerado localmente com ruído, ciclos e deriva. Não há conexão com corretoras, APIs financeiras, carteiras ou ordens reais. O algoritmo é determinístico em sua lógica, mas o mercado usa aleatoriedade controlada por uma semente opcional.
