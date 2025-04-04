# cs-multi-agents-systems-project

A project focused on designing, simulating, and analyzing multi-agent systems, implementing coordination, communication, and decision-making strategies.

## Running the code

```bash
solara run src/server.py
```

## Multi-Agent Waste Processing System

### Agent Overview

The system consists of drone agents assigned to specific zones, each responsible for collecting, processing, and transferring waste materials through a pipeline of increasing refinement.

### Agent Types

The drones are specialized by zone type (0, 1, 2), which corresponds to different processing capabilities:

- **Green Zone Drones (zone_type=0)**: First-stage processors
- **Yellow Zone Drones (zone_type=1)**: Second-stage processors
- **Red Zone Drones (zone_type=2)**: Final-stage processors

### Agent Architecture

Each drone maintains:

- **Percepts**: Current environmental observations
  - Empty neighboring cells
  - Nearby zones, drones, and waste objects
- **Knowledge**: Internal state and memory
  - Inventory (max capacity: 2 waste items)
  - Processing flags and action history
  - Zone and position awareness

### Decision Making Process

Drones follow a deliberation cycle with priority-based decision making:

1. **Update knowledge** based on current percepts
2. **Deliberate** to select the next action
3. **Execute** the chosen action

#### Action Priority Hierarchy

1. **Transform waste** when inventory is full (2 items) for green/yellow drones
2. **Drop waste** when:
   - At a transfer zone with processed waste (zone boundaries)
   - At the final drop zone for red drones
3. **Move eastward** after transforming waste or when carrying processed waste
4. **Pick up waste** when:
   - Compatible waste is present
   - Inventory has capacity
   - Drone is allowed to pick (compatibility rules)
5. **Default**: Random movement to explore the environment

### Zone-Based Strategy

- **Spatial Organization**: The grid is divided into three zones (left to right)
- **Transfer Zones**: Special boundary regions where drones transfer waste to the next zone
- **Drop Zone**: Eastmost column where final processed waste is deposited

### Waste Processing Pipeline

1. **Collection**: Drones gather waste matching their zone type
2. **Transformation**: When inventory is full, waste is transformed into a higher-level type
3. **Transportation**: Processed waste is moved eastward to transfer/drop zones
4. **Transfer/Deposit**: Waste is dropped for the next processing stage or final deposit

### Agent Collaboration

The system demonstrates emergence through specialized roles and implicit coordination:

- First-stage drones process raw materials
- Second-stage drones process intermediate materials
- Final-stage drones complete the processing pipeline

This creates an efficient waste management system without explicit communication between agents.
