import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from model import Environment

sns.set_theme(style="whitegrid")


def run_experiment(params, steps=500):
    """
    Run a single experiment with given parameters
    """

    # Create model with tracker
    model = Environment(
        green_agents=params["green_agents"],
        yellow_agents=params["yellow_agents"],
        red_agents=params["red_agents"],
        green_wastes=params["green_wastes"],
        yellow_wastes=params["yellow_wastes"],
        red_wastes=params["red_wastes"],
        seed=params["seed"],
        width=params["width"],
        height=params["height"],
    )

    # Run simulation
    for _ in range(steps):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    # Compute stationary step
    diffs = df.diff().fillna(0)
    activity = diffs.abs().sum(axis=1) > 0
    if activity.any():
        last_active_step = np.where(activity)[0][-1]
    else:
        last_active_step = 0

    # Extract variable values at stationary step
    stationary_vars = {}
    for var in [
        "green_wastes",
        "yellow_wastes",
        "red_wastes",
        "wastes_in_drop_zone",
        "wastes_not_in_drop_zone",
        "wastes_in_inventories",
    ]:
        if var in df.columns:
            stationary_vars[var] = df.iloc[last_active_step][var]
        else:
            stationary_vars[var] = None

    return df, last_active_step, stationary_vars


def run_multiple_experiments(num_runs, parameter_variations):
    """
    Run multiple experiments with different parameters.
    Returns results and a list of dicts, one per run x benchmark, for reporting.
    """
    base_params = {
        "green_agents": 1,
        "yellow_agents": 1,
        "red_agents": 1,
        "green_wastes": 8,
        "yellow_wastes": 4,
        "red_wastes": 2,
        "width": 24,
        "height": 12,
    }

    results = []
    run_infos = []

    # Run with base parameters if no variations
    if not parameter_variations:
        exp_name = "baseline"
        params = base_params.copy()
        stationary_steps = []
        for i in range(num_runs):
            run_params = params.copy()
            run_params["seed"] = i
            df, last_active_step, stationary_vars = run_experiment(run_params)
            results.append(df)
            stationary_steps.append(last_active_step)
            run_infos.append(
                {
                    "experiment": exp_name,
                    "run": i + 1,
                    **{
                        k: params[k]
                        for k in [
                            "green_agents",
                            "yellow_agents",
                            "red_agents",
                            "green_wastes",
                            "yellow_wastes",
                            "red_wastes",
                            "width",
                            "height",
                        ]
                    },
                    "stationary_step": last_active_step,
                    **stationary_vars,
                }
            )
            print(f"Completed experiment {i + 1}/{num_runs} with base parameters")
        # Add average row
        avg_vars = {
            k: np.mean([info[k] for info in run_infos if isinstance(info["run"], int)])
            for k in stationary_vars
        }
        run_infos.append(
            {
                "experiment": exp_name,
                "run": "avg",
                **{
                    k: params[k]
                    for k in [
                        "green_agents",
                        "yellow_agents",
                        "red_agents",
                        "green_wastes",
                        "yellow_wastes",
                        "red_wastes",
                        "width",
                        "height",
                    ]
                },
                "stationary_step": np.mean(stationary_steps),
                **avg_vars,
            }
        )
    else:
        # Run with parameter variations
        for variation_name, param_changes in parameter_variations.items():
            params = base_params.copy()
            params.update(param_changes)
            stationary_steps = []
            run_stationary_vars = []
            for i in range(num_runs):
                exp_params = params.copy()
                exp_params["seed"] = i
                df, last_active_step, stationary_vars = run_experiment(exp_params)
                results.append((variation_name, df))
                stationary_steps.append(last_active_step)
                run_stationary_vars.append(stationary_vars)
                run_infos.append(
                    {
                        "experiment": variation_name,
                        "run": i + 1,
                        **{
                            k: params[k]
                            for k in [
                                "green_agents",
                                "yellow_agents",
                                "red_agents",
                                "green_wastes",
                                "yellow_wastes",
                                "red_wastes",
                                "width",
                                "height",
                            ]
                        },
                        "stationary_step": last_active_step,
                        **stationary_vars,
                    }
                )
                print(f"Completed experiment {i + 1}/{num_runs} with {variation_name}")
            # Add average row
            avg_vars = {
                k: np.mean([vars_[k] for vars_ in run_stationary_vars])
                for k in run_stationary_vars[0]
            }
            run_infos.append(
                {
                    "experiment": variation_name,
                    "run": "avg",
                    **{
                        k: params[k]
                        for k in [
                            "green_agents",
                            "yellow_agents",
                            "red_agents",
                            "green_wastes",
                            "yellow_wastes",
                            "red_wastes",
                            "width",
                            "height",
                        ]
                    },
                    "stationary_step": np.mean(stationary_steps),
                    **avg_vars,
                }
            )

    return results, run_infos


def analyze_results(results: List[Tuple[str, pd.DataFrame]]):
    """
    Analyze and compare results from multiple experiments.
    Plots all variables over time and determines steps to stationary state.
    For each variable, all runs are merged in a single plot with different shades.
    """
    print("Analyzing results...")

    NUMBER_PLOT_COLS = 3  # Number of columns in the variable plots grid

    # Color mapping for variables
    base_colors = {
        "green_wastes": "green",
        "yellow_wastes": "gold",
        "red_wastes": "red",
        "wastes_in_drop_zone": "blue",
    }

    def prettify(varname):
        return varname.replace("_", " ").title()

    # Organize results by experiment name
    exp_dict = {}
    for item in results:
        if isinstance(item, tuple):
            exp_name, df = item
        else:
            exp_name, df = "baseline", item
        exp_dict.setdefault(exp_name, []).append(df)

    for exp_name, runs in exp_dict.items():
        print(f"\nExperiment: {exp_name}")
        num_runs = len(runs)
        variables = runs[0].columns
        num_vars = len(variables)
        ncols = NUMBER_PLOT_COLS
        nrows = (num_vars + ncols - 1) // ncols

        # Compute stationary steps for all runs
        stationary_steps = []
        for df in runs:
            diffs = df.diff().fillna(0)
            activity = diffs.abs().sum(axis=1) > 0
            if activity.any():
                last_active_step = np.where(activity)[0][-1]
            else:
                last_active_step = 0
            stationary_steps.append(last_active_step)
        max_stationary = max(stationary_steps)

        fig, axes = plt.subplots(
            nrows, ncols, figsize=(4 * ncols, 4 * nrows), squeeze=False
        )
        axes = axes.flatten()

        for j, var in enumerate(variables):
            ax = axes[j]
            base_color = base_colors.get(var, "gray")
            for i, df in enumerate(runs):
                alpha = 0.4 + 0.6 * (i / max(1, num_runs - 1))
                ax.plot(
                    df.index,
                    df[var],
                    label=f"Run {i + 1}",
                    color=base_color,
                    alpha=alpha,
                )
                # Draw stationary line for this run
                ax.axvline(
                    stationary_steps[i],
                    color=base_color,
                    linestyle="--",
                    alpha=alpha * 0.7,
                )
            ax.set_title(prettify(var))
            ax.set_xlabel("Step")
            ax.set_ylabel(prettify(var))
            ax.set_xlim(0, max_stationary * 1.1)
            ax.legend()
        # Hide unused subplots
        for k in range(num_vars, len(axes)):
            fig.delaxes(axes[k])
        plt.tight_layout()
        plt.suptitle(f"Experiment: {prettify(exp_name)}", y=1.02)
        plt.savefig(f"results/{exp_name}_plots.png", bbox_inches="tight")


if __name__ == "__main__":
    import os

    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")

    # Define parameter variations to test
    parameter_variations = {
        "baseline": {},
        "waste_load_low": {
            "green_wastes": 5,
            "yellow_wastes": 5,
            "red_wastes": 5,
        },
        "waste_load_medium": {
            "green_wastes": 10,
            "yellow_wastes": 10,
            "red_wastes": 10,
        },
        "waste_load_high": {
            "green_wastes": 20,
            "yellow_wastes": 20,
            "red_wastes": 20,
        },
        "high_green_agents": {
            "green_agents": 6,
            "yellow_agents": 1,
            "red_agents": 1,
        },
        "high_yellow_agents": {
            "green_agents": 1,
            "yellow_agents": 6,
            "red_agents": 1,
        },
        "high_red_agents": {
            "green_agents": 1,
            "yellow_agents": 1,
            "red_agents": 6,
        },
        "balanced_agents_medium": {
            "green_agents": 3,
            "yellow_agents": 3,
            "red_agents": 3,
        },
        "balanced_agents_high": {
            "green_agents": 5,
            "yellow_agents": 5,
            "red_agents": 5,
        },
        "imbalanced_wastes_g_dominant": {
            "green_wastes": 20,
            "yellow_wastes": 5,
            "red_wastes": 2,
        },
        "imbalanced_wastes_r_dominant": {
            "green_wastes": 2,
            "yellow_wastes": 5,
            "red_wastes": 20,
        },
        "more_green_agents_less_green_waste": {
            "green_agents": 6,
            "green_wastes": 4,
        },
        "fewer_agents_more_waste": {
            "green_agents": 1,
            "yellow_agents": 1,
            "red_agents": 1,
            "green_wastes": 15,
            "yellow_wastes": 15,
            "red_wastes": 15,
        },
        "only_green_zone": {
            "green_agents": 4,
            "yellow_agents": 0,
            "red_agents": 0,
            "green_wastes": 20,
            "yellow_wastes": 0,
            "red_wastes": 0,
        },
        "only_yellow_zone": {
            "green_agents": 0,
            "yellow_agents": 4,
            "red_agents": 0,
            "green_wastes": 0,
            "yellow_wastes": 20,
            "red_wastes": 0,
        },
        "only_red_zone": {
            "green_agents": 0,
            "yellow_agents": 0,
            "red_agents": 4,
            "green_wastes": 0,
            "yellow_wastes": 0,
            "red_wastes": 20,
        },
        "unbalanced_agents_low_red": {
            "green_agents": 3,
            "yellow_agents": 3,
            "red_agents": 1,
        },
        "unbalanced_agents_high_red": {
            "green_agents": 2,
            "yellow_agents": 2,
            "red_agents": 6,
        },
        "high_agents_low_waste": {
            "green_agents": 5,
            "yellow_agents": 5,
            "red_agents": 5,
            "green_wastes": 2,
            "yellow_wastes": 2,
            "red_wastes": 2,
        },
        "low_agents_high_waste": {
            "green_agents": 1,
            "yellow_agents": 1,
            "red_agents": 1,
            "green_wastes": 20,
            "yellow_wastes": 20,
            "red_wastes": 20,
        },
        "opposite_balance": {
            "green_agents": 5,
            "yellow_agents": 2,
            "red_agents": 1,
            "green_wastes": 2,
            "yellow_wastes": 10,
            "red_wastes": 15,
        },
        "swap_balance": {
            "green_agents": 2,
            "yellow_agents": 5,
            "red_agents": 3,
            "green_wastes": 15,
            "yellow_wastes": 4,
            "red_wastes": 6,
        },
        "edge_case_empty_waste": {
            "green_wastes": 0,
            "yellow_wastes": 0,
            "red_wastes": 0,
        },
        "edge_case_zero_red_agents": {
            "red_agents": 0,
            "red_wastes": 10,
        },
        "edge_case_zero_green_agents": {
            "green_agents": 0,
            "green_wastes": 12,
        },
        "conflicting_agents_vs_wastes": {
            "green_agents": 5,
            "yellow_agents": 1,
            "red_agents": 2,
            "green_wastes": 1,
            "yellow_wastes": 10,
            "red_wastes": 8,
        },
        "even_waste_unbalanced_agents": {
            "green_agents": 1,
            "yellow_agents": 4,
            "red_agents": 2,
            "green_wastes": 10,
            "yellow_wastes": 10,
            "red_wastes": 10,
        },
    }

    # Run experiments with parameter variations
    results, run_infos = run_multiple_experiments(
        num_runs=3, parameter_variations=parameter_variations
    )

    # Save run_infos as CSV: one line per run x benchmark
    df_infos = pd.DataFrame(run_infos)
    df_infos.to_csv("results/experiment_stationary_steps.csv", index=False)

    # Bar plot for average stationary time per experiment
    plt.figure(figsize=(2 * len(df_infos["experiment"].unique()), 4))
    # Fix: compute average from rows where run == "avg"
    avg_df = df_infos[df_infos["run"] == "avg"][["experiment", "stationary_step"]]
    plt.bar(avg_df["experiment"], avg_df["stationary_step"], color="skyblue")
    plt.ylabel("Average Stationary Time")
    plt.xlabel("Experiment")
    plt.title("Average Stationary Time per Experiment")
    plt.tight_layout()
    plt.savefig("results/avg_stationary_time_barplot.png")

    # Analyze and compare results
    print("Analyzing results...")
    analyze_results(results)
