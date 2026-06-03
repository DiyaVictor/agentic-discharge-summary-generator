import argparse
import os
from src.logger import TraceLogger
from src.agent import DischargeSummaryAgent

def main():
    parser = argparse.ArgumentParser(description="Discharge Summary Agent")
    parser.add_argument("--mode", type=str, default="mock", help="Run mode: mock or part2")
    args = parser.parse_args()

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    logger = TraceLogger(os.path.join(output_dir, "trace.log"))
    agent = DischargeSummaryAgent(logger)

    if args.mode == "mock":
        print("Running in mock mode...")
        agent.run_mock(output_dir)
        print(f"Outputs generated successfully in '{output_dir}/'")
    elif args.mode == "part2":
        from src.part2_learning import run_learning_loop
        run_learning_loop(output_dir)
    else:
        print("Unsupported mode. Use --mode mock or --mode part2.")

if __name__ == "__main__":
    main()
