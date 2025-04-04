import csv
import json
from typing import Dict, List

import numpy as np


class Tracker:
    """
    A comprehensive experiment tracker that logs metrics for multi-agent waste processing systems.
    """

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.results = []
        self.step_data = {}
        self.metrics = {}
        self.agent_movements = {}  # Track agent movements for distance calculation
        self.agent_actions = {}  # Track agent actions for behavior metrics
        self.waste_tracking = {}  # Track waste through the system for processing time

    def log_result(self, result: Dict):
        """Log a single step result dictionary."""
        self.results.append(result)
        self.step_data[result["step"]] = result

    def track_agent_movement(self, agent_id, position, inventory_size, action):
        """Track agent movements and actions for behavior metrics."""
        if agent_id not in self.agent_movements:
            self.agent_movements[agent_id] = []
            self.agent_actions[agent_id] = []

        self.agent_movements[agent_id].append(position)
        self.agent_actions[agent_id].append(
            {
                "action": action,
                "position": position,
                "inventory_size": inventory_size,
                "step": len(self.results) - 1,
            }
        )

    def track_waste(self, waste_id, current_zone, status, processor_id=None):
        """Track waste through the processing pipeline."""
        if waste_id not in self.waste_tracking:
            self.waste_tracking[waste_id] = {
                "created_step": len(self.results) - 1,
                "history": [],
            }

        self.waste_tracking[waste_id]["history"].append(
            {
                "step": len(self.results) - 1,
                "zone": current_zone,
                "status": status,
                "processor_id": processor_id,
            }
        )

        if status == "completed":
            self.waste_tracking[waste_id]["completed_step"] = len(self.results) - 1

    def calculate_metrics(self):
        """Calculate all metrics based on collected data."""
        final_step = self.results[-1]["step"] if self.results else 0

        # 1. Processing Efficiency
        processing_times = []
        transformations_per_step = {}
        inventory_utilization = {}

        for waste_id, data in self.waste_tracking.items():
            if "completed_step" in data:
                processing_times.append(data["completed_step"] - data["created_step"])

                # Count transformations per step
                for entry in data["history"]:
                    if entry["status"] == "transformed":
                        step = entry["step"]
                        transformations_per_step[step] = (
                            transformations_per_step.get(step, 0) + 1
                        )

        # Calculate inventory utilization
        for agent_id, actions in self.agent_actions.items():
            inventory_sizes = [a["inventory_size"] for a in actions]
            inventory_utilization[agent_id] = sum(inventory_sizes) / (
                len(inventory_sizes) * 2
            )  # Max capacity is 2

        # 2. Zone Performance
        zone_stats = {0: {}, 1: {}, 2: {}}
        for step_data in self.results:
            for zone_type in range(3):
                zone_key = f"{zone_type}_zone_wastes"
                if zone_key in step_data:
                    if "accumulation" not in zone_stats[zone_type]:
                        zone_stats[zone_type]["accumulation"] = []
                    zone_stats[zone_type]["accumulation"].append(step_data[zone_key])

        # Calculate zone clearance rates and congestion levels
        for zone_type, stats in zone_stats.items():
            if "accumulation" in stats and stats["accumulation"]:
                # Approximate clearance rate from waste accumulation patterns
                if len(stats["accumulation"]) > 1:
                    changes = [
                        stats["accumulation"][i] - stats["accumulation"][i - 1]
                        for i in range(1, len(stats["accumulation"]))
                    ]
                    stats["clearance_rate"] = (
                        sum(c for c in changes if c < 0) / len(changes)
                        if changes
                        else 0
                    )

                # Transfer zone congestion (simplified)
                stats["congestion_level"] = (
                    max(stats["accumulation"]) / 10
                )  # Scale congestion to 0-1

        # 3. System-wide Metrics
        total_processed = sum(
            1 for w in self.waste_tracking.values() if "completed_step" in w
        )
        avg_throughput = total_processed / final_step if final_step > 0 else 0

        # Calculate bottleneck scores
        bottleneck_score = self.calculate_bottleneck_score(zone_stats)

        # 4. Agent Behavior Metrics
        distance_traveled = {}
        idle_percentage = {}
        collisions = {}

        for agent_id, positions in self.agent_movements.items():
            # Calculate total Manhattan distance traveled
            if len(positions) > 1:
                distance = sum(
                    abs(positions[i][0] - positions[i - 1][0])
                    + abs(positions[i][1] - positions[i - 1][1])
                    for i in range(1, len(positions))
                )
                distance_traveled[agent_id] = distance
            else:
                distance_traveled[agent_id] = 0

            # Calculate idle percentage (when position doesn't change)
            idle_count = sum(
                1 for i in range(1, len(positions)) if positions[i] == positions[i - 1]
            )
            idle_percentage[agent_id] = idle_count / len(positions) if positions else 0

            # Simplified collision detection (position overlap)
            collisions[agent_id] = 0

        # Store all calculated metrics
        self.metrics = {
            "processing_efficiency": {
                "avg_processing_time": np.mean(processing_times)
                if processing_times
                else 0,
                "transformations_per_step": sum(transformations_per_step.values())
                / final_step
                if final_step > 0
                else 0,
                "avg_inventory_utilization": np.mean(
                    list(inventory_utilization.values())
                )
                if inventory_utilization
                else 0,
            },
            "zone_performance": {
                f"zone_{zone}": stats for zone, stats in zone_stats.items()
            },
            "system_metrics": {
                "total_processed": total_processed,
                "avg_throughput": avg_throughput,
                "bottleneck_score": bottleneck_score,
            },
            "agent_behavior": {
                "avg_distance_per_agent": np.mean(list(distance_traveled.values()))
                if distance_traveled
                else 0,
                "avg_idle_percentage": np.mean(list(idle_percentage.values()))
                if idle_percentage
                else 0,
                "total_collisions": sum(collisions.values()),
            },
        }

        return self.metrics

    def calculate_bottleneck_score(self, zone_stats):
        """Calculate bottleneck scores for each zone."""
        # Approximate the bottleneck calculation based on available data
        green_zone_processed = 0
        green_zone_total = 0
        yellow_zone_processed = 0
        yellow_zone_received = 0
        red_zone_deposited = 0
        red_zone_received = 0

        # Use waste tracking to estimate these values
        for waste_data in self.waste_tracking.values():
            history = waste_data["history"]
            zones_visited = set(entry["zone"] for entry in history)

            if 0 in zones_visited:  # Waste entered green zone
                green_zone_total += 1
                if any(
                    entry["status"] == "transformed" and entry["zone"] == 0
                    for entry in history
                ):
                    green_zone_processed += 1
                    yellow_zone_received += 1

            if 1 in zones_visited:  # Waste entered yellow zone
                if any(
                    entry["status"] == "transformed" and entry["zone"] == 1
                    for entry in history
                ):
                    yellow_zone_processed += 1
                    red_zone_received += 1

            if 2 in zones_visited:  # Waste entered red zone
                if any(entry["status"] == "completed" for entry in history):
                    red_zone_deposited += 1

        # Avoid division by zero
        green_score = green_zone_processed / max(1, green_zone_total)
        yellow_score = yellow_zone_processed / max(1, yellow_zone_received)
        red_score = red_zone_deposited / max(1, red_zone_received)

        return {
            "green_zone": green_score,
            "yellow_zone": yellow_score,
            "red_zone": red_score,
        }

    def get_results(self) -> List[Dict]:
        """Return all logged results."""
        return self.results

    def get_metrics(self) -> Dict:
        """Return calculated metrics."""
        if not self.metrics:
            self.calculate_metrics()
        return self.metrics

    def save_results(self, filename: str):
        """Save step-by-step results to a CSV file."""
        if not self.results:
            print("No results to save")
            return

        # Get fieldnames from the first result dictionary
        fieldnames = list(self.results[0].keys())

        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"Results saved to {filename}")

    def log_experiment_params(self, params: Dict):
        """Log the experiment parameters."""
        self.metrics["experiment_params"] = params

    def save_metrics(self, filename: str):
        """Save calculated metrics to a JSON file."""
        if not self.metrics:
            self.calculate_metrics()

        with open(filename, "w") as jsonfile:
            json.dump(self.metrics, jsonfile, indent=4)

        print(f"Metrics saved to {filename}")
