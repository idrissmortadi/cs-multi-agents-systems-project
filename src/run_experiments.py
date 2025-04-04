from experiment_tracker import Tracker
from model import Environment


def run_experiment(params, steps=50):
    """
    Run a single experiment with given parameters
    """
    # Create tracker for this experiment
    tracker = Tracker(f"experiment_{params['seed']}")

    # Create model with tracker
    model = Environment(
        green_agents=params["green_agents"],
        yellow_agents=params["yellow_agents"],
        red_agents=params["red_agents"],
        green_wastes=params["green_wastes"],
        yellow_wastes=params["yellow_wastes"],
        red_wastes=params["red_wastes"],
        seed=params["seed"],
        tracker=tracker,
    )

    # Run simulation
    for _ in range(steps):
        model.step()

    # Save results
    tracker.save_results(f"results/experiment_{params['seed']}.csv")
    return tracker.get_results()


def run_multiple_experiments(num_experiments=3):
    """
    Run multiple experiments with different seeds
    """
    base_params = {
        "green_agents": 4,
        "yellow_agents": 2,
        "red_agents": 2,
        "green_wastes": 10,
        "yellow_wastes": 3,
        "red_wastes": 2,
    }

    results = []
    for i in range(num_experiments):
        params = base_params.copy()
        params["seed"] = i
        experiment_results = run_experiment(params)
        results.append(experiment_results)
        print(f"Completed experiment {i + 1}/{num_experiments}")

    return results


if __name__ == "__main__":
    import os

    from plot_results import main as plot_results

    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")

    # Run experiments
    results = run_multiple_experiments()

    # Print summary
    print("\nExperiment Summary:")
    for i, exp_results in enumerate(results):
        final_result = exp_results[-1]  # Get last step result
        print(
            f"Experiment {i}: Final red zone wastes = {final_result['red_zone_wastes']}"
        )

    # Create plots
    plot_results()
