import json
import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from agents import Drone
from tracker import Tracker
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

        # After each step, record additional metrics about drones and wastes
        # This would require adding hooks in the model.py to report to the tracker
        for agent in model.agents:
            if isinstance(agent, Drone):
                tracker.track_agent_movement(
                    agent.unique_id,
                    agent.pos,
                    len(agent.knowledge["inventory"]),
                    agent.knowledge["actions"][-1]
                    if agent.knowledge["actions"]
                    else "none",
                )

    # Calculate metrics
    tracker.calculate_metrics()

    # Log experiment parameters
    tracker.log_experiment_params(params)

    # Save results and metrics
    tracker.save_results(f"results/experiment_{params['seed']}_steps.csv")
    tracker.save_metrics(f"results/experiment_{params['seed']}_metrics.json")

    return tracker


def run_multiple_experiments(num_experiments=3, parameter_variations=None):
    """
    Run multiple experiments with different parameters
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

    # Run with base parameters if no variations
    if not parameter_variations:
        for i in range(num_experiments):
            params = base_params.copy()
            params["seed"] = i
            tracker = run_experiment(params)
            results.append(tracker)
            print(
                f"Completed experiment {i + 1}/{num_experiments} with base parameters"
            )
    else:
        # Run with parameter variations
        for variation_name, param_changes in parameter_variations.items():
            params = base_params.copy()
            params.update(param_changes)

            for i in range(num_experiments):
                exp_params = params.copy()
                exp_params["seed"] = i
                tracker = run_experiment(exp_params)
                results.append((variation_name, tracker))
                print(
                    f"Completed experiment {i + 1}/{num_experiments} with {variation_name}"
                )

    return results


def analyze_results(results):
    """
    Analyze and compare results from multiple experiments
    """
    if not results:
        print("No results to analyze")
        return

    # If results contain parameter variations
    if isinstance(results[0], tuple):
        variation_metrics = {}

        # Group results by variation
        for variation_name, tracker in results:
            if variation_name not in variation_metrics:
                variation_metrics[variation_name] = []
            variation_metrics[variation_name].append(tracker.get_metrics())

        # Compare metrics across variations
        comparison = {}
        for variation_name, metrics_list in variation_metrics.items():
            # Average metrics across runs with same parameters
            avg_metrics = {}
            for metric_category in metrics_list[0].keys():
                if isinstance(metrics_list[0][metric_category], dict):
                    avg_metrics[metric_category] = {}
                    for metric_name, value in metrics_list[0][metric_category].items():
                        if isinstance(value, (int, float)):
                            avg_metrics[metric_category][metric_name] = np.mean(
                                [m[metric_category][metric_name] for m in metrics_list]
                            )

            comparison[variation_name] = avg_metrics

        # Save comparison to file
        with open("results/parameter_comparison.json", "w") as f:
            json.dump(comparison, f, indent=4)

        # Create comparison visualizations
        plot_comparisons(comparison)
    else:
        # Simple case - just average metrics across runs with same parameters
        all_metrics = [tracker.get_metrics() for tracker in results]

        avg_metrics = {}
        for metric_category in all_metrics[0].keys():
            avg_metrics[metric_category] = {}
            for metric_name, value in all_metrics[0][metric_category].items():
                if isinstance(value, (int, float)):
                    avg_metrics[metric_category][metric_name] = np.mean(
                        [m[metric_category][metric_name] for m in all_metrics]
                    )

        # Save average metrics
        with open("results/average_metrics.json", "w") as f:
            json.dump(avg_metrics, f, indent=4)


def plot_comparisons(comparison):
    """Create visualizations comparing different parameter settings"""
    # Create directory for plots
    if not os.path.exists("results/plots"):
        os.makedirs("results/plots")

    # Use Seaborn style
    sns.set_theme(style="whitegrid")

    # List of key metrics to plot
    key_metrics = [
        ("system_metrics", "total_processed"),
        ("system_metrics", "avg_throughput"),
        ("processing_efficiency", "avg_processing_time"),
        ("agent_behavior", "avg_idle_percentage"),
    ]

    # Create a bar chart for each key metric
    for category, metric in key_metrics:
        values = []
        labels = []

        for variation_name, metrics in comparison.items():
            if category in metrics and metric in metrics[category]:
                values.append(metrics[category][metric])
                labels.append(variation_name)

        if values:
            plt.figure(figsize=(10, 6))
            sns.barplot(x=labels, y=values, palette="viridis")
            plt.title(f"{category} - {metric.replace('_', ' ').capitalize()}")
            plt.ylabel(metric.replace("_", " ").capitalize())
            plt.xlabel("Parameter Variations")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"results/plots/{category}_{metric}.png")
            plt.close()

    # Additional plots for deeper analysis
    # Plot clearance rates for each zone
    if "zone_performance" in next(iter(comparison.values())):
        for zone in ["zone_0", "zone_1", "zone_2"]:
            clearance_rates = []
            labels = []

            for variation_name, metrics in comparison.items():
                if zone in metrics["zone_performance"]:
                    clearance_rates.append(
                        metrics["zone_performance"][zone].get("clearance_rate", 0)
                    )
                    labels.append(variation_name)

            if clearance_rates:
                plt.figure(figsize=(10, 6))
                sns.barplot(x=labels, y=clearance_rates, palette="coolwarm")
                plt.title(f"Clearance Rate - {zone.replace('_', ' ').capitalize()}")
                plt.ylabel("Clearance Rate")
                plt.xlabel("Parameter Variations")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(f"results/plots/clearance_rate_{zone}.png")
                plt.close()

    # Plot congestion levels for each zone
    for zone in ["zone_0", "zone_1", "zone_2"]:
        congestion_levels = []
        labels = []

        for variation_name, metrics in comparison.items():
            if zone in metrics["zone_performance"]:
                congestion_levels.append(
                    metrics["zone_performance"][zone].get("congestion_level", 0)
                )
                labels.append(variation_name)

        if congestion_levels:
            plt.figure(figsize=(10, 6))
            sns.barplot(x=labels, y=congestion_levels, palette="magma")
            plt.title(f"Congestion Level - {zone.replace('_', ' ').capitalize()}")
            plt.ylabel("Congestion Level")
            plt.xlabel("Parameter Variations")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"results/plots/congestion_level_{zone}.png")
            plt.close()

    # Plot bottleneck scores for each zone
    if "system_metrics" in next(iter(comparison.values())):
        bottleneck_scores = {"green_zone": [], "yellow_zone": [], "red_zone": []}
        labels = []

        for variation_name, metrics in comparison.items():
            if "bottleneck_score" in metrics["system_metrics"]:
                for zone in bottleneck_scores.keys():
                    bottleneck_scores[zone].append(
                        metrics["system_metrics"]["bottleneck_score"].get(zone, 0)
                    )
                labels.append(variation_name)

        for zone, scores in bottleneck_scores.items():
            if scores:
                plt.figure(figsize=(10, 6))
                sns.barplot(x=labels, y=scores, palette="cubehelix")
                plt.title(f"Bottleneck Score - {zone.replace('_', ' ').capitalize()}")
                plt.ylabel("Bottleneck Score")
                plt.xlabel("Parameter Variations")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(f"results/plots/bottleneck_score_{zone}.png")
                plt.close()


if __name__ == "__main__":
    import os

    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")

    # Define parameter variations to test
    parameter_variations = {
        "baseline": {},  # Base parameters
        "more_green_agents": {"green_agents": 6},
        "more_yellow_agents": {"yellow_agents": 4},
        "more_red_agents": {"red_agents": 4},
        "equal_distribution": {"green_agents": 3, "yellow_agents": 3, "red_agents": 3},
        "high_waste_load": {"green_wastes": 20, "yellow_wastes": 6, "red_wastes": 4},
    }

    # Run experiments with parameter variations
    results = run_multiple_experiments(
        num_experiments=3, parameter_variations=parameter_variations
    )

    # Analyze and compare results
    analyze_results(results)

    print("\nExperiment Summary:")
    if isinstance(results[0], tuple):
        for variation_name, tracker in results:
            metrics = tracker.get_metrics()
            print(f"\n{variation_name}:")
            print(
                f"  Total processed waste: {metrics['system_metrics']['total_processed']}"
            )
            print(
                f"  Average throughput: {metrics['system_metrics']['avg_throughput']:.2f} items/step"
            )
            print(
                f"  Bottleneck scores: {metrics['system_metrics']['bottleneck_score']}"
            )
            print(
                f"  Average processing time: {metrics['processing_efficiency']['avg_processing_time']:.2f} steps"
            )
    else:
        for i, tracker in enumerate(results):
            metrics = tracker.get_metrics()
            print(f"\nExperiment {i}:")
            print(
                f"  Total processed waste: {metrics['system_metrics']['total_processed']}"
            )
            print(
                f"  Average throughput: {metrics['system_metrics']['avg_throughput']:.2f} items/step"
            )
