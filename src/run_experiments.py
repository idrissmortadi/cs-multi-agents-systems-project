import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml  # Add yaml import

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
        agent_implementation=params[
            "agent_implementation"
        ],  # Pass agent implementation
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


def run_multiple_experiments(
    num_runs, base_params, parameter_variations, agent_implementations
):
    """
    Run multiple experiments with different parameters for each agent implementation.
    Returns results and a list of dicts, one per run x benchmark, for reporting.
    """
    # base_params are now passed as an argument
    # parameter_variations are now passed as an argument

    results = []
    run_infos = []

    for agent_impl in agent_implementations:
        print(f"\n--- Running experiments for Agent Implementation: {agent_impl} ---")
        # Run with base parameters if no variations
        if not parameter_variations:
            exp_name = f"baseline_{agent_impl}"  # Include agent impl in name
            params = base_params.copy()
            params["agent_implementation"] = agent_impl  # Add agent impl to params
            stationary_steps = []
            run_stationary_vars_list = []  # Store stationary vars for each run
            for i in range(num_runs):
                run_params = params.copy()
                run_params["seed"] = i
                df, last_active_step, stationary_vars = run_experiment(run_params)
                results.append((exp_name, df))  # Store exp_name with df
                stationary_steps.append(last_active_step)
                run_stationary_vars_list.append(stationary_vars)  # Append run's vars
                run_infos.append(
                    {
                        "experiment": exp_name,
                        "agent_implementation": agent_impl,  # Add agent impl info
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
                print(f"Completed experiment {i + 1}/{num_runs} for {exp_name}")
            # Add average row
            if run_stationary_vars_list:  # Check if list is not empty
                avg_vars = {
                    k: np.mean(
                        [
                            vars_[k]
                            for vars_ in run_stationary_vars_list
                            if vars_ is not None and k in vars_
                        ]
                    )
                    for k in run_stationary_vars_list[0]
                    if run_stationary_vars_list[0] is not None
                }
            else:
                avg_vars = {}

            run_infos.append(
                {
                    "experiment": exp_name,
                    "agent_implementation": agent_impl,  # Add agent impl info
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
                    "stationary_step": np.mean(stationary_steps)
                    if stationary_steps
                    else 0,
                    **avg_vars,
                }
            )
        else:
            # Run with parameter variations
            for variation_name, param_changes in parameter_variations.items():
                exp_name = (
                    f"{variation_name}_{agent_impl}"  # Include agent impl in name
                )
                params = base_params.copy()
                params.update(param_changes)
                params["agent_implementation"] = agent_impl  # Add agent impl to params
                stationary_steps = []
                run_stationary_vars_list = []  # Store stationary vars for each run
                for i in range(num_runs):
                    exp_params = params.copy()
                    exp_params["seed"] = i
                    df, last_active_step, stationary_vars = run_experiment(exp_params)
                    results.append((exp_name, df))  # Store exp_name with df
                    stationary_steps.append(last_active_step)
                    run_stationary_vars_list.append(
                        stationary_vars
                    )  # Append run's vars
                    run_infos.append(
                        {
                            "experiment": exp_name,
                            "agent_implementation": agent_impl,  # Add agent impl info
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
                    print(f"Completed experiment {i + 1}/{num_runs} for {exp_name}")
                # Add average row
                if run_stationary_vars_list:  # Check if list is not empty
                    avg_vars = {
                        k: np.mean(
                            [
                                vars_[k]
                                for vars_ in run_stationary_vars_list
                                if vars_ is not None and k in vars_
                            ]
                        )
                        for k in run_stationary_vars_list[0]
                        if run_stationary_vars_list[0] is not None
                    }
                else:
                    avg_vars = {}

                run_infos.append(
                    {
                        "experiment": exp_name,
                        "agent_implementation": agent_impl,  # Add agent impl info
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
                        "stationary_step": np.mean(stationary_steps)
                        if stationary_steps
                        else 0,
                        **avg_vars,
                    }
                )

    return results, run_infos


def analyze_results(results: List[Tuple[str, pd.DataFrame]]):
    """
    Analyze and compare results from multiple experiments.
    Plots all variables over time and determines steps to stationary state.
    For each variable, all runs are merged in a single plot with different shades.
    Saves plots with experiment name (including agent implementation).
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

    # Organize results by experiment name (which now includes agent impl)
    exp_dict = {}
    for exp_name, df in results:  # Directly unpack tuple
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
            ax.set_xlim(0, 600)
            ax.legend()
        # Hide unused subplots
        for k in range(num_vars, len(axes)):
            fig.delaxes(axes[k])
        plt.tight_layout()
        plt.suptitle(f"Experiment: {prettify(exp_name)}", y=1.02)
        # Save plot with the full experiment name (including agent impl)
        plt.savefig(f"results/{exp_name}_plots.png", bbox_inches="tight")
        plt.close(fig)  # Close the figure to free memory


if __name__ == "__main__":
    import os

    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")

    # Load parameters from YAML file
    params_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "experiment_params.yaml",
    )
    with open(params_file_path, "r") as f:
        all_params = yaml.safe_load(f)

    base_params = all_params["base_params"]
    parameter_variations = all_params["parameter_variations"]

    # Define agent implementations to test
    agent_implementations_to_run = ["agents_with_comm", "agents_random_walk"]

    # Run experiments with parameter variations for both implementations
    results, run_infos = run_multiple_experiments(
        num_runs=3,
        base_params=base_params,  # Pass loaded base_params
        parameter_variations=parameter_variations,  # Pass loaded variations
        agent_implementations=agent_implementations_to_run,  # Pass implementations
    )

    # Save run_infos as CSV: one line per run x benchmark (now includes agent_implementation column)
    df_infos = pd.DataFrame(run_infos)
    df_infos.to_csv("results/experiment_stationary_steps.csv", index=False)

    # --- Grouped Bar Plot for Average Stationary Time ---
    # Filter for average rows
    avg_df = df_infos[
        df_infos["run"] == "avg"
    ].copy()  # Use .copy() to avoid SettingWithCopyWarning

    # Extract base variation name (remove the _agents or _agents_random suffix)
    avg_df["variation"] = avg_df["experiment"].str.rsplit("_", n=1).str[0]

    # Sort for consistent plotting order
    avg_df = avg_df.sort_values(by=["variation", "agent_implementation"])

    plt.figure(figsize=(12, 2 * len(avg_df["variation"].unique())))
    ax = sns.barplot(
        data=avg_df,
        y="variation",
        x="stationary_step",
        hue="agent_implementation",
        palette="viridis",
        hue_order=[
            "agents_with_comm",
            "agents_random_walk",
        ],  # Ensure consistent hue order
    )

    ax.set_title("Average Stationary Time per Experiment Variation", fontsize=16)
    ax.set_xlabel("Experiment Variation", fontsize=12)
    ax.set_ylabel("Average Stationary Time", fontsize=12)
    ax.tick_params(
        axis="x",
        rotation=45,
    )  # Rotate x-labels for better readability
    plt.legend(title="Agent Implementation")
    plt.tight_layout()
    plt.savefig("results/avg_stationary_time_grouped_barplot.png")
    plt.close()
    # --- End Grouped Bar Plot ---

    # Analyze and compare results
    print("\nAnalyzing results...")
    analyze_results(results)
    print("\nExperiment runs and analysis complete.")
