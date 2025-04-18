from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from objects import Waste

MAX_CARRY_TIMEOUT = 50  # Maximum carry timeout for waste


@dataclass
class DronePercepts:
    """Represents the percepts of a drone agent."""

    neighbors_empty: List[Tuple[int, int]] = field(default_factory=list)
    neighbor_zones: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    neighbor_drones: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    neighbor_wastes: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)

    def __str__(self):
        return (
            f"Percepts(\n"
            f"\tEmpty: {len(self.neighbors_empty)},\n"
            f"\tZones: {len(self.neighbor_zones)},\n"
            f"\tDrones: {len(self.neighbor_drones)},\n"
            f"\tWastes: {len(self.neighbor_wastes)}\n"
            f")"
        )

    def __repr__(self):
        # Use default dataclass repr for detailed representation
        return self.__str__()


@dataclass
class DroneKnowledge:
    """Represents the knowledge base of a drone agent."""

    inventory: List[Waste] = field(default_factory=list)
    can_pick: bool = True
    should_move_east: bool = False
    actions: List[str] = field(default_factory=list)
    percepts: List[DronePercepts] = field(default_factory=list)
    grid_width: int = 0
    grid_height: int = 0
    zone_type: int = 0
    in_transfer_zone: bool = False
    in_drop_zone: bool = False
    collective_waste_memory: Set[Tuple[int, Tuple[int, int]]] = field(
        default_factory=set
    )
    target_pos: Optional[Tuple[int, int]] = None
    visited_positions: Dict[Tuple[int, int], int] = field(default_factory=dict)

    carry_timeout: int = MAX_CARRY_TIMEOUT
    deadlock_status: str = "idle"  # Status of the drone
    ignored_waste_positions: Set[Tuple[int, int]] = field(default_factory=set)

    def __str__(self):
        inventory_str = [
            f"Waste(id={w.unique_id}, color={w.waste_color})" for w in self.inventory
        ]
        memory_str = [
            f"Color: {color}, Position: {pos}"
            for color, pos in self.collective_waste_memory
        ]
        return (
            f"Knowledge(\n"
            f"\tZone: {self.zone_type},\n"
            f"\tInventory: {inventory_str},\n"
            f"\tTarget: {self.target_pos},\n"
            f"\tMemory: {memory_str},\n"
            f"\tCanPick: {self.can_pick},\n"
            f"\tMoveEast: {self.should_move_east},\n"
            f"\tInTransferZone: {self.in_transfer_zone},\n"
            f"\tInDropZone: {self.in_drop_zone},\n"
            f"\tActions: {self.actions},\n"
            f"\tVisitedCount: {len(self.visited_positions)}\n"  # Add visited count for brevity
            f"\tCarryTimeout: {self.carry_timeout},\n"
            f"\tStatus: {self.deadlock_status}\n"
            f"\tIgnoredWastePositions: {self.ignored_waste_positions}\n"
            f")"
        )

    def __repr__(self):
        # Use default dataclass repr or a slightly more detailed one if needed
        # For now, let's make it the same as __str__ for simplicity in logs
        return self.__str__()
