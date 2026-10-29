"""Launch the Zéro Day: Swarm Trading desktop prototype."""

from __future__ import annotations

import argparse

from zeroday.simulation import SimulationEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zéro Day: Swarm Trading — simulador 2D")
    parser.add_argument("--capital", type=float, default=10_000.0, help="capital fictício inicial (padrão: 10000)")
    parser.add_argument("--robots", type=int, default=8, help="quantidade de robôs iniciais (padrão: 8)")
    parser.add_argument("--risk", choices=("conservador", "moderado", "agressivo"), default="moderado")
    parser.add_argument("--seed", type=int, default=None, help="semente para reproduzir a simulação")
    parser.add_argument("--headless-ticks", type=int, default=0, help="executa sem janela e imprime um resumo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = SimulationEngine(
        starting_capital=args.capital,
        initial_robots=args.robots,
        risk_name=args.risk,
        seed=args.seed,
    )
    if args.headless_ticks > 0:
        engine.run(args.headless_ticks)
        print("ZÉRO DAY — RESUMO DA SIMULAÇÃO")
        print(f"Ticks: {engine.tick_count}")
        print(f"Saldo: {engine._money(engine.total_balance())}")
        print(f"Robôs vivos: {len(engine.alive_robots)}")
        print(f"Robôs mortos: {len(engine.dead_robots)}")
        print(f"Filiais: {engine.building.branch_count}")
        return

    # Import only for graphical sessions; headless mode does not need Pygame.
    from zeroday.ui import GameApp

    GameApp(engine).run()


if __name__ == "__main__":
    main()
