import csv
from typing import Dict, List


class Tracker:
    """
    A simple experiment tracker that logs results and saves them as CSV files.
    """

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.results: List[Dict] = []

    def log_result(self, result: Dict):
        """Log a single result dictionary."""
        self.results.append(result)
        print(f"Logged result: {result}")

    def get_results(self) -> List[Dict]:
        """Return all logged results."""
        return self.results

    def save_results(self, filename: str):
        """
        Save results to a CSV file.

        Args:
            filename: Path to save the CSV file
        """
        if not self.results:
            print("No results to save")
            return

        # Get fieldnames from the first result dictionary
        fieldnames = list(self.results[0].keys())

        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            writer.writerows(self.results)

        print(f"Results saved to {filename}")
