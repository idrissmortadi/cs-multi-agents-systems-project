import os
from glob import glob

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def load_and_combine_experiments(results_dir: str) -> pd.DataFrame:
    """Load all CSV files and combine them into a single DataFrame with experiment ID."""
    all_data = []

    for file_path in glob(os.path.join(results_dir, "experiment_*.csv")):
        exp_id = os.path.basename(file_path).split("_")[1].split(".")[0]
        df = pd.read_csv(file_path)
        df["experiment"] = f"Experiment {exp_id}"
        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


def create_plots(data: pd.DataFrame, output_dir: str):
    """Create a separate plot for each metric over time."""
    # Set the style for all plots
    sns.set_style("whitegrid")
    sns.set_palette("husl")

    # Create plots directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get all columns except 'experiment' and 'step'
    metrics = [col for col in data.columns if col not in ["experiment", "step"]]

    # Create a plot for each metric
    for metric in metrics:
        plt.figure(figsize=(12, 6))

        # Create the line plot
        sns.lineplot(
            data=data,
            x="step",
            y=metric,
            hue="experiment",
            linewidth=2,
            marker="o",
            markersize=4,
        )

        # Customize the plot
        plt.title(f"{metric.replace('_', ' ').title()} over Time", pad=20)
        plt.xlabel("Simulation Steps")
        plt.ylabel(metric.replace("_", " ").title())

        # Add legend with better positioning
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        # Tight layout to prevent label cutoff
        plt.tight_layout()

        # Save the plot
        plt.savefig(
            os.path.join(output_dir, f"{metric}_over_time.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()


def main():
    # Define directories
    results_dir = "results"
    plots_dir = "plots"

    # Load and combine all experiment data
    data = load_and_combine_experiments(results_dir)

    # Create regular plots
    create_plots(data, plots_dir)

    print(f"Plots have been saved to the '{plots_dir}' directory")


if __name__ == "__main__":
    main()
