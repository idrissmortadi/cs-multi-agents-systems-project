# cs-multi-agents-systems-project

A project focused on designing, simulating, and analyzing multi-agent systems, implementing coordination, communication, and decision-making strategies.

## Running the code

### Install the required packages

```bash
conda env create -f environment.yml
conda activate SMA
```

### Run the simulation

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

### Performance Metrics

1. **Processing Efficiency**
   - Time to process waste from raw to final state
   - Number of complete waste transformations per time step
   - Average inventory utilization rate per drone

2. **Zone Performance**
   - Waste accumulation rate per zone
   - Transfer zone congestion levels
   - Zone clearance rate (waste items processed/total waste in zone)

3. **System-wide Metrics**
   - Total waste processed to completion
   - Average processing pipeline throughput
   - System bottleneck identification:

    ```python
     def calculate_bottleneck_score(zone_stats):
         return {
             'green_zone': processed_items / total_items,
             'yellow_zone': processed_items / received_items,
             'red_zone': deposited_items / received_items
         }
    ```

4. **Agent Behavior Metrics**
   - Average distance traveled per waste item processed
   - Collision/blocking incidents between drones
   - Idle time percentage per drone

These metrics can be tracked over time to optimize the system's parameters and evaluate different strategies.

### Detailed Performance Metrics Explanation

#### 1. Processing Efficiency

- **Average Processing Time:**  
  Formula:  
  $$
  \text{Average Processing Time} = \frac{\sum (\text{completed\_step} - \text{created\_step})}{\text{Total Waste Items Processed}}
  $$  
  Pseudo-code:
  
```python
  processing_times = [
      waste["completed_step"] - waste["created_step"]
      for waste in waste_tracking.values()
      if "completed_step" in waste
  ]
  avg_processing_time = sum(processing_times) / len(processing_times)
  ```

- **Transformations Per Step:**  
  Formula:  
  $$
  \text{Transformations Per Step} = \frac{\text{Total Transformations}}{\text{Total Simulation Steps}}
  $$  
  Pseudo-code:
  
```python
  transformations_per_step = sum(transformations.values()) / total_steps
  ```

- **Average Inventory Utilization:**  
  Formula:  
  $$
  \text{Average Inventory Utilization} = \frac{\sum (\text{Inventory Size})}{\text{Total Actions} \times \text{Max Inventory Capacity}}
  $$  
  Pseudo-code:
  
```python
  avg_inventory_utilization = sum(inventory_sizes) / (len(inventory_sizes) * 2)
  ```

#### 2. Zone Performance

- **Waste Accumulation Rate:**  
  Formula:  
  $$
  \text{Accumulation Rate} = \frac{\text{Waste Items in Zone}}{\text{Simulation Steps}}
  $$  
  Pseudo-code:
  
```python
  accumulation_rate = sum(zone_accumulation) / len(zone_accumulation)
  ```

- **Zone Clearance Rate:**  
  Formula:  
  $$
  \text{Clearance Rate} = \frac{\sum (\text{Negative Changes in Waste Count})}{\text{Total Changes}}
  $$  
  Pseudo-code:
  
```python
  clearance_rate = sum(change for change in changes if change < 0) / len(changes)
  ```

- **Transfer Zone Congestion Level:**  
  Formula:  
  $$
  \text{Congestion Level} = \frac{\text{Max Waste in Transfer Zone}}{\text{Scaling Factor}}
  $$  
  Pseudo-code:
  
```python
  congestion_level = max(zone_accumulation) / 10
  ```

#### 3. System-wide Metrics

- **Total Waste Processed:**  
  Formula:  
  $$
  \text{Total Waste Processed} = \text{Count of Waste Items with Completed Status}
  $$  
  Pseudo-code:
  
```python
  total_processed = sum(1 for waste in waste_tracking.values() if "completed_step" in waste)
  ```

- **Average Throughput:**  
  Formula:  
  $$
  \text{Average Throughput} = \frac{\text{Total Waste Processed}}{\text{Total Simulation Steps}}
  $$  
  Pseudo-code:
  
```python
  avg_throughput = total_processed / total_steps
  ```

- **Bottleneck Score:**  
  Formula:  
  $$
  \text{Bottleneck Score (Zone)} = \frac{\text{Processed Items in Zone}}{\text{Total Items Entering Zone}}
  $$  
  Pseudo-code:
  
```python
  bottleneck_score = {
      "green_zone": green_processed / max(1, green_total),
      "yellow_zone": yellow_processed / max(1, yellow_received),
      "red_zone": red_deposited / max(1, red_received),
  }
  ```

#### 4. Agent Behavior Metrics

- **Average Distance Traveled Per Agent:**  
  Formula:  
  $$
  \text{Average Distance} = \frac{\sum (\text{Manhattan Distance Between Consecutive Positions})}{\text{Total Agents}}
  $$  
  Pseudo-code:
  
```python
  distance = sum(
      abs(pos[i][0] - pos[i-1][0]) + abs(pos[i][1] - pos[i-1][1])
      for i in range(1, len(positions))
  )
  avg_distance = distance / total_agents
  ```

- **Collision/Blocking Incidents:**  
  Formula:  
  $$
  \text{Collisions} = \text{Count of Overlapping Positions Between Agents}
  $$  
  Pseudo-code:
  
```python
  collisions = sum(1 for pos in positions if pos in occupied_positions)
  ```

- **Idle Time Percentage:**  
  Formula:  
  $$
  \text{Idle Time Percentage} = \frac{\text{Idle Steps}}{\text{Total Steps}}
  $$  
  Pseudo-code:
  
```python
  idle_percentage = idle_steps / total_steps
  ```

These metrics can be tracked over time to optimize the system's parameters and evaluate different strategies.
