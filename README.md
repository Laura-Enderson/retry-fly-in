*This project was created as part of the 42 curriculum by tsiarran.*

# FLY-IN
## Description

This project aims to route drones through a given network while minimizing the number of simulation turns and respecting movement constraints.

A network consists of:

- Hubs: Locations that drones can access depending on their capacity and zone type.<br> There are 4 types of zones:
  - normal: A standard zone with a movement cost of 1 turn (default).
  - blocked: An inaccessible zone. Drones must not enter or pass through it. Any path containing this zone is considered invalid.
  - restricted: A sensitive or dangerous zone. Moving to this zone costs 2 turns.
  - priority: A preferred zone. Moving to this zone costs 1 turn, but it should be prioritized during pathfinding.
- Links: Connections between two hubs. Each link has a limited capacity (1 drone by default).
## Instructions

Run make commands in the terminal:

- `install`: Install the project dependencies using uv.
- `run`: Execute the main script of the project using:
```
uv run python -m src
```
- `debug`: Run the main script in debug mode using Python's built-in debugger (pdb).
- `clean`: Remove temporary files and caches (e.g., __pycache__, .mypy_cache) to keep the project environment clean.
- `fclean`: Remove temporary files and the .venv directory created by uv.
- `lint`: Execute the following commands:
```
flake8 ./src and mypy ./src --warn-return-any
--warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs
--check-untyped-defs
```
- `lint-strict`: Execute the following commands:
```
flake8 ./src and mypy ./src --strict
```

**How does it work (make run)?**

The program automatically scans for all available map files and asks the user to choose one.

## Resources
- `pygame.org > docs`: Contains a lot of information and tutorials to help beginners get started with Pygame.
- `AI Usage`:
   - Work faster: AI makes it faster to find and understand documentation about specific topics. Its examples also help explain unfamiliar concepts.
   - Help with English: AI was used to improve English writing and correct grammatical mistakes.

## Additional Sections
### Algorithm

- **First, all possible paths are discovered using `Orchestrator.find_paths()`:**
```
How?

Starting from the start_hub, the algorithm explores all possible connections in the network until it encounters either a blocked zone or the end_hub.

- If it encounters a blocked zone, the path is considered invalid and discarded.

- If it reaches the end_hub, the path is considered valid and added to the list of valid_paths.
```

- **Then, the actual simulation begins:**
During each turn, every drone in the network:
```
- Looks for its next destination:

The algorithm checks all hubs connected to the drone's current location (hub/link).
It calculates the possible paths through those hubs and selects the next hub based on the path with the lowest movement cost.


- Try to move to the next destination:

The drone checks whether it can access the selected hub. It can move to the next hub only if:

    - The link connecting the drone's current hub to the next hub has not reached its maximum capacity.
    - The next hub still has an available slot for the drone.

If the drone cannot move to its next destination, it waits at its current location until the next turn.
```
### Visual Representation

A simple visual representation is presented to the user once the simulation is complete.

It displays:

- `All hubs in the network`: Each hub zone type has its own visual representation, allowing users to identify them easily.
- `All links in the network`: Lines illustrate which hubs are connected to one another.
- `Drones`: Once the animation is launched, it displays the drones' positions throughout the simulation (press `space` to launch).
- `Hub names` and `the number of drones occupying each hub` are also displayed around the hubs to avoid confusion when drones overlap.
- The following control is available to the user:
        - Use the `arrow keys` to navigate.

### Examples:
- **[#] Example of a valid map file:**
```
nb_drones: 3

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```
- The first line defines the number of drones using the following syntax: 
   - nb_drones: `<number>`. <br><br>
- Each zone is defined on a separate line using one of the following prefixes:
   - start_hub: `<name> <x> <y> [metadata]` marks the starting zone.
   - end_hub: `<name> <x> <y> [metadata]` marks the destination zone.
   - hub: `<name> <x> <y> [metadata]` defines a regular zone.
   - The connection syntax does not allow dashes in zone names (see below).
   - All metadata is optional and enclosed in brackets [...], with the following default values:
      - zone=`<type>` (default: normal)
      - color=`<value>` (default: none)
      - max_drones=`<number>` (default: 1) - Maximum number of drones that can occupy this
   zone simultaneously.
      - Tags inside brackets can appear in any order. <br><br>

- Zone types:
   - `normal` – A standard zone with a movement cost of 1 turn (default).
   - `blocked` – An inaccessible zone. Drones must not enter or pass through this zone.Any path containing it is considered invalid.
   - `restricted` – A sensitive or dangerous zone. Moving to this zone costs 2 turns.
   - `priority` – A preferred zone. Moving to this zone costs 1 turn, but it should be prioritized during pathfinding. <br><br>
- Colors:
  - Colors are optional and can be used for visual representation (in terminal output
or graphical displays). 
  - Accepted color values can be any valid single-word strings (e.g., red, blue, gray). There is no predefined list of allowed colors.

  - When colors are specified, the implementation should provide visual feedback through colored terminal output or a graphical representation. <br><br>
- Connections are defined using the following syntax: connection: <name1>-<name2> [metadata]:
   - Defines a bidirectional connection between two zones.
   - The connection syntax does not allow dashes in zone names.
   - Optional metadata can be specified in brackets [...]:
       - max_link_capacity=`<number>` (default: 1) - Maximum number of drones that can
traverse this connection simultaneously.
<br><br>
- Comments start with `#` and are ignored.

**[#] Example of the expected output for the map above:**
```
D1-waypoint1 
D1-waypoint2 D2-waypoint1 
D1-goal D2-waypoint2 
D2-goal
```
- The simulation must output the step-by-step movements of drones from the starting zone to the destination zone.
- Each simulation turn is represented by a separate line.
- Each line must list all drone movements that occur during that turn, separated by spaces. Each movement must follow one of these formats: `D<ID>-<zone>`, or `D<ID>-<connection>` when a drone is still in transit toward a restricted zone.
- `D<ID>` refers to the unique drone identifier (e.g., D1, D2).
`<zone>` is the name of the destination zone.
`<connection>` is the name of the connection leading to a restricted zone.
- Drones that do not move during a given turn are omitted from that line.
- Drones that reach the destination zone are considered delivered and are no longer tracked.
- The simulation ends when all drones have reached the destination zone.