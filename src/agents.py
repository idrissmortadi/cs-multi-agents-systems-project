import random

from mesa import Agent

from objects import Waste


class Drone(Agent):
    """
    A drone agent that can move around the grid, pick up, transform, and drop waste.
    Each drone is assigned to a specific zone type.
    """

    def __init__(self, model, zone_type):
        """
        Initialize a drone agent.

        Args:
            model: The model instance the drone is part of
            zone_type: The type of zone the drone is assigned to
        """
        super().__init__(model)
        self.percepts = {
            "neighbors_empty": [],  # [(x, y), ...] in correponding zone color
            "neighbor_zones": [],  # [(zone_type, zone_pos), ...]
            "neighbor_drones": [],  # [(drone_id, drone_pos), ...]
            "neighbor_wastes": [],  # [(waste_id, waste_pos), ...]
        }
        self.knowledge = {
            "carried_waste_type": None,
            "carried_waste_amount": 0,
            "can_pick": True,
            "actions": [],
            "percepts": [],
            "grid_width": self.model.grid.width,
            "grid_height": self.model.grid.height,
            "zone_type": zone_type,
            "in_drop_zone": False,  # Whether drone is in a drop zone
        }

    def move(self):
        """
        Move the drone to a new position chosen randomly from available empty neighbors.
        If no empty neighbors are available, the drone stays in place.
        Updates the drone's knowledge after moving.
        """
        # Choose a new position from available empty neighbors or stay in place
        new_position = random.choice(
            (
                self.percepts["neighbors_empty"]
                if len(self.percepts["neighbors_empty"]) > 0
                else [self.pos]
            )
        )
        # Move the agent to the new position
        self.model.grid.move_agent(self, new_position)

        # Update knowledge about position
        self.knowledge["actions"].append(f"moved to {new_position}")

        # Update knowledge about whether position is in drop zone
        is_drop_zone = new_position[0] == (self.knowledge["zone_type"] * 3 + 2)
        self.knowledge["in_drop_zone"] = is_drop_zone

    def pick_waste(self):
        """
        Pick up waste at the drone's current position if:
        1. There is waste at the position
        2. The drone can carry more waste (less than 2 units)
        3. The waste color matches the drone's zone type
        4. The waste color matches the already carried waste type (if any)

        Returns:
            bool: True if waste was picked up, False otherwise
        """
        # Find wastes at current position
        wastes_at_position = [
            (waste_id, waste_pos)
            for waste_id, waste_pos in self.percepts["neighbor_wastes"]
        ]

        # Check if there are wastes at the current position and the drone can carry more waste
        if wastes_at_position and self.knowledge["carried_waste_amount"] < 2:
            waste_id, _ = wastes_at_position[0]  # Get the first waste
            waste = self.model.get_agent_by_id(waste_id)
            print(f"Drone {self.unique_id} found waste {waste_id}")

            # Check if the waste color matches the carried waste type or if the drone is not carrying any waste
            if (
                waste.waste_color == self.knowledge["carried_waste_type"]
                or self.knowledge["carried_waste_type"] is None
            ) and waste.waste_color == self.knowledge["zone_type"]:
                # Update the drone's carried waste amount and type
                self.knowledge["carried_waste_amount"] += waste.weight
                self.knowledge["carried_waste_type"] = waste.waste_color

                # Remove the waste from the grid
                if waste.pos is None:
                    return False
                self.model.grid.remove_agent(waste)

                # Log the action
                self.knowledge["actions"].append(f"picked waste {waste_id}")
                print(f"Drone {self.unique_id} picked waste {waste.unique_id}")
                print(
                    f"Drone {self.unique_id} is carrying {self.knowledge['carried_waste_amount']} waste"
                )
                return True
            else:
                self.knowledge["can_pick"] = False

        # Return False if no waste was picked
        print(f"Drone {self.unique_id} did not pick any waste")
        return False

    def drop_waste(self):
        """
        Drop the waste the drone is carrying at its current position.
        This method is only executed if the drone is carrying waste.

        Returns:
            bool: True if waste was dropped, False otherwise
        """
        # Check if the drone is carrying any waste
        if self.knowledge["carried_waste_amount"] > 0:
            # Decrease the carried waste amount
            self.knowledge["carried_waste_amount"] -= 1

            # Reset the carried waste type if no more waste is carried
            if self.knowledge["carried_waste_amount"] == 0:
                self.knowledge["carried_waste_type"] = None

            # Create a new waste agent at the current position
            new_waste = Waste(self.model, self.knowledge["zone_type"] + 1)
            self.model.add_agent(new_waste, self.pos)

            # Log the action
            self.knowledge["actions"].append("dropped waste")
            print(f"Drone {self.unique_id} dropped waste at {self.pos}")

            return True

        # Return False if no waste was dropped
        return False

    def update(self):
        """
        Update the drone's knowledge based on its current percepts and state.
        This method is called at the beginning of each step.
        """
        # Store current percepts in knowledge history
        self.knowledge["percepts"].append(self.percepts)
        # Reset actions for the new step
        self.knowledge["actions"] = []

        # Update drop zone status based on current position
        # Check if the drone is in a drop zone (x-coordinate equals zone_type * 3 + 2)
        is_drop_zone = self.pos[0] == (self.knowledge["zone_type"] * 3 + 2)
        self.knowledge["in_drop_zone"] = is_drop_zone

    def transform_waste(self):
        """
        Transform carried waste into processed waste.
        Sets the carried waste amount to 1 and updates the waste type.
        """
        self.knowledge["carried_waste_amount"] = 1
        self.knowledge["carried_waste_type"] = self.knowledge["zone_type"] + 1
        self.knowledge["actions"].append("transformed waste")

    def deliberate(self):
        """
        Decide which action to take based on the drone's current knowledge and state.

        Returns:
            str: The action to take ("transform_waste", "drop_waste", "pick_waste", or "move")
        """
        # Priority 0: Transform waste if carrying maximum capacity
        if self.knowledge["carried_waste_amount"] == 2:
            print("Transforming waste")
            return "transform_waste"

        # Priority 1: Drop waste if in drop zone and carrying waste of the correct type
        if (
            self.knowledge["in_drop_zone"]
            and self.knowledge["carried_waste_amount"] > 0
        ):
            print("Reached drop zone")
            if self.knowledge["carried_waste_type"] == (
                self.knowledge["zone_type"] + 1
            ):
                print("Dropping waste")
                return "drop_waste"

        # Priority 2: Pick waste if at same position as compatible waste and has capacity
        filtered_wastes = []
        for waste_id, waste_pos in self.percepts["neighbor_wastes"]:
            waste = self.model.get_agent_by_id(waste_id)
            if (
                waste.waste_color == self.knowledge["carried_waste_type"]
                or self.knowledge["carried_waste_type"] is None
            ) and waste.waste_color == self.knowledge["zone_type"]:
                filtered_wastes.append(waste_id)
        if (
            filtered_wastes
            and self.knowledge["carried_waste_amount"] < 2
            and self.knowledge["can_pick"]
        ):
            return "pick_waste"

        # Default action: Move randomly
        return "move"

    def step_agent(self):
        """
        Execute one step of the agent's behavior:
        1. Update knowledge
        2. Decide on an action
        3. Execute the action and update percepts
        """
        self.update()
        action = self.deliberate()
        self.percepts = self.model.do(self, action)
