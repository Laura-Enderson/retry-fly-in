"""
Define graph elements and drone simulation orchestration.

Provides graph models, validation, pathfinding, and drone movement
scheduling.
"""

from pydantic import BaseModel, Field, model_validator, ValidationError
from enum import StrEnum
from pydantic_extra_types.color import Color
from typing import Any


class InitError(Exception):
    """Represent an error occurring during graph initialization."""

    def __init__(self, mess: str = "Init error."):
        """
        Initialize the exception.

        Args:
            mess (str): The error message.

        Returns:
            None
        """
        self.message = mess
        super().__init__(self.message)


class ZoneType(StrEnum):
    """Define the available types of graph zones."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Hub(BaseModel):
    """Represent a graph hub and its drone capacity."""

    name: str
    coord: tuple[int, int]
    zone: ZoneType = ZoneType.NORMAL
    color: Color = Color("white")
    max_drones: float = 1
    list_of_drones_in: list["Drone"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_name(self) -> "Hub":
        """
        Validate the hub name.

        Returns:
            Hub: The validated hub instance.

        Raises:
            ValueError: If the name contains spaces or dashes.
        """
        if " " in self.name or "-" in self.name:
            raise ValueError("Invalid name: no dash/space in zone names")
        return self


class StartHub(Hub):
    """Represent the starting hub with unlimited drone capacity."""

    max_drones: float = float("inf")


class EndHub(Hub):
    """Represent the destination hub with unlimited drone capacity."""

    max_drones: float = float("inf")


class Link(BaseModel):
    """Represent a connection between two hubs."""

    name: str
    linked_zones: tuple[Hub, Hub]
    max_link_capacity: float
    list_of_drones_in: list["Drone"] = Field(default_factory=list)


class Drone(BaseModel):
    """Represent a drone and its current and previous locations."""

    id: int
    previous_loc: Hub | Link | None = None
    loc: Hub | Link
    next_loc: Hub | Link | None = None


class Graph():
    """Store the graph structure, including hubs, links, and drones."""

    def __init__(self, drones: list[Drone], start_hub: StartHub,
                 hubs: list[Hub], end_hub: Hub, links: list[Link]):
        """
        Initialize the graph components.

        Args:
            drones (list[Drone]): Drones in the graph.
            start_hub (StartHub): Starting hub.
            hubs (list[Hub]): Graph hubs.
            end_hub (Hub): Destination hub.
            links (list[Link]): Connections between hubs.

        Returns:
            None
        """
        self.drones: list[Drone] = drones
        self.start_hub = start_hub
        self.hubs: list[Hub] = hubs
        self.end_hub = end_hub
        self.links: list[Link] = links

    @staticmethod
    def parse_color(color: str) -> Color:
        """
        Convert a string into a Color object.

        Args:
            color (str): Color name or value.

        Returns:
            Color: Parsed color, or white if invalid.
        """
        try:
            result = Color(color)
        except ValueError:
            result = Color("white")
        return result

    @classmethod
    def init_graph(cls, graph: Any) -> "Graph":
        """
        Initialize a graph from input data.

        Args:
            graph (Any): Dictionary containing graph configuration.

        Returns:
            Graph: The initialized graph.

        Raises:
            InitError: If graph components cannot be initialized.
        """
        try:
            start_hub = StartHub(
                name=graph["start_hub"]["name"],
                coord=tuple(graph["start_hub"]["coord"]),
                zone=ZoneType.NORMAL if not graph[
                    "start_hub"]["zone"] else ZoneType(
                    graph["start_hub"]["zone"]),
                color=Graph.parse_color(graph["start_hub"]["color"])
            )
            end_hub = EndHub(
                name=graph["end_hub"]["name"],
                coord=tuple(graph["end_hub"]["coord"]),
                zone=ZoneType.NORMAL if not graph[
                    "end_hub"]["zone"] else ZoneType(
                    graph["end_hub"]["zone"]),
                color=Graph.parse_color(graph["end_hub"]["color"])
            )
        except ValueError as error:
            raise InitError(f"Failed initiating endpoints: {error}")
        except ValidationError as e:
            raise InitError(f"Failed initiating endpoints: {e.errors()}")
        drones: list[Drone] = []
        try:
            for i in range(graph["nb_drones"]):
                drone = Drone(
                    id=(i + 1),
                    loc=start_hub,
                    previous_loc=None
                )
                drones.append(drone)
        except ValidationError as e:
            raise InitError(f"Failed initiating drones: {e.errors()}")
        start_hub.list_of_drones_in.extend(drones)
        hubs: list[Hub] = []
        try:
            hubs.append(start_hub)
            hubs.append(end_hub)
            for hub in graph["hubs"]:
                hubs.append(
                    Hub(
                        name=hub["name"],
                        coord=tuple(hub["coord"]),
                        zone=ZoneType.NORMAL if not hub["zone"] else ZoneType(
                            hub["zone"]),
                        color=Graph.parse_color(hub["color"]),
                        max_drones=hub["max_drones"]
                    )
                )
        except ValueError as error:
            raise InitError(f"Failed initiating hubs: {error}")
        except ValidationError as e:
            raise InitError(f"Failed initiating hubs: {e.errors()}")
        links: list[Link] = []
        try:
            for link in graph["links"]:
                all_hubs = hubs + [start_hub] + [end_hub]
                zone_a = next(
                    hub for hub in all_hubs
                    if hub.name == tuple(link["linked_zones"])[0]
                )
                zone_b = next(
                    hub for hub in all_hubs
                    if hub.name == tuple(link["linked_zones"])[1]
                )
                links.append(
                    Link(
                        name=f"{zone_a.name}-{zone_b.name}",
                        linked_zones=(zone_a, zone_b),
                        max_link_capacity=link["max_link_capacity"]
                    )
                )
        except ValueError as error:
            raise InitError(f"Failed initiating links: {error}")
        except ValidationError as e:
            raise InitError(f"Failed initiating links: {e.errors()}")
        return cls(
            drones=drones,
            start_hub=start_hub,
            hubs=hubs,
            end_hub=end_hub,
            links=links
        )


class Orchestrator():
    """Manage graph initialization and drone movement scheduling."""

    real_graph: Graph
    graph = {
        "nb_drones": 0,
        "start_hub": {
            "name": "",
            "coord": [0, 0],
            "zone": "",
            "color": "",
            "max_drones": 0
        },
        "hubs": [],
        "end_hub": {
            "name": "",
            "coord": [0, 0],
            "zone": "",
            "color": "",
            "max_drones": 0
        },
        "links": []
    }
    paths: list[list[Hub]] = []

    @staticmethod
    def check_if_linked(
            current_loc: Hub, links: list[Link], processed_loc: list[Hub]
    ) -> list[Link]:
        """
        Find unprocessed links connected to a hub.

        Args:
            current_loc (Hub): Hub to check.
            links (list[Link]): Available graph links.
            processed_loc (list[Hub]): Already visited hubs.

        Returns:
            list[Link]: Available connected links.
        """
        connected_links = []
        for link in links:
            if current_loc in link.linked_zones:
                if link.linked_zones[0] == current_loc:
                    loc = link.linked_zones[1]
                else:
                    loc = link.linked_zones[0]
                if loc not in processed_loc:
                    connected_links.append(link)
        return connected_links

    @staticmethod
    def get_other_extremity_of(current_loc: Hub | Link | None, link: Link
                               ) -> Hub:
        """
        Get the opposite hub of a link.

        Args:
            current_loc (Hub | Link | None): Current location.
            link (Link): Link to inspect.

        Returns:
            Hub: The opposite hub.
        """
        if link.linked_zones[0] == current_loc:
            loc = link.linked_zones[1]
        else:
            loc = link.linked_zones[0]
        return loc

    @staticmethod
    def dig_in(path: list[Hub], last_loc: Hub,
               graph: Graph, paths: dict[str, list[list[Hub]]]) -> None:
        """
        Recursively explore the graph to find valid paths.

        Args:
            path (list[Hub]): Current exploration path.
            last_loc (Hub): Last visited hub.
            graph (Graph): Graph being explored.
            paths (dict[str, list[list[Hub]]]): Storage for valid paths.

        Returns:
            None
        """
        connected_links = Orchestrator.check_if_linked(
            path[len(path) - 1], graph.links, path)
        for link in connected_links:
            path_second = path.copy()
            loc = Orchestrator.get_other_extremity_of(
                path[len(path) - 1], link)
            path_second.append(loc)
            if loc.zone == "blocked":
                continue
            if isinstance(loc, EndHub):
                paths["valid_paths"].append(path_second)
                continue
            Orchestrator.dig_in(
                path_second, path_second[len(path_second) - 1], graph, paths)

    @staticmethod
    def find_paths(graph: Graph) -> list[list[Hub]]:
        """
        Find valid paths from the starting hub to the destination.

        Args:
            graph (Graph): Graph to explore.

        Returns:
            list[list[Hub]]: Up to eight shortest valid paths.

        Raises:
            RuntimeError: If the starting hub is blocked or no path exists.
        """
        paths: dict[str, list[Any]] = {
            "valid_paths": []
        }
        if graph.start_hub.zone == ZoneType.BLOCKED:
            raise RuntimeError(
                "The start hub is inaccessible(cannot be entered)."
            )
        Orchestrator.dig_in(
            path=[graph.start_hub],
            last_loc=graph.start_hub,
            graph=graph,
            paths=paths
        )
        if len(paths["valid_paths"]) == 0:
            raise RuntimeError(
                "No valid path found in the given graph"
            )
        sorted_paths = sorted(paths["valid_paths"], key=lambda x: len(x))
        result = sorted_paths
        if len(result) > 8:
            result = sorted_paths[:8]
        return result

    @staticmethod
    def corresponding_paths_to_loc(
            loc: Hub, paths: list[list[Hub]]) -> list[list[Hub]]:
        """
        Extract paths starting after a specified hub.

        Args:
            loc (Hub): Hub from which to continue.
            paths (list[list[Hub]]): Available paths.

        Returns:
            list[list[Hub]]: Remaining path segments.
        """
        corresponding_paths = []
        for path in paths:
            if loc in path:
                corresponding_paths.append(path[(path.index(loc) + 1):])
        return corresponding_paths

    @staticmethod
    def choose_drone_next_move(
            drone: Drone, paths: list[list[Hub]], graph: Graph) -> None:
        """
        Select the drone's next destination based on path costs and capacities.

        Args:
            drone (Drone): Drone to update.
            paths (list[list[Hub]]): Available valid paths.
            graph (Graph): Graph containing the drone.

        Returns:
            None
        """
        the_least_moves = 1000000000
        next_loc_to_go: Any = None
        if isinstance(drone.loc, Link):
            next_loc_to_go = Orchestrator.get_other_extremity_of(
                drone.previous_loc, drone.loc)
            drone.next_loc = next_loc_to_go
            return
        paths = Orchestrator.corresponding_paths_to_loc(drone.loc, paths)
        for path in paths:
            total_move_cost = 0
            for hub in path:
                if hub.zone == ZoneType.RESTRICTED:
                    total_move_cost += 2
                else:
                    total_move_cost += 1
                if hub.max_drones <= len(
                        graph.hubs[graph.hubs.index(hub)].list_of_drones_in):
                    total_move_cost += 1
            if total_move_cost < the_least_moves:
                the_least_moves = total_move_cost
                next_loc_to_go = path[0]
            elif total_move_cost == the_least_moves:
                if next_loc_to_go is not None:
                    if (path[0].zone == ZoneType.PRIORITY
                            and next_loc_to_go.zone != ZoneType.PRIORITY):
                        next_loc_to_go = path[0]
        if next_loc_to_go is None:
            return
        if next_loc_to_go.zone == ZoneType.RESTRICTED:
            next_loc_cap = 0
            connected_links_to_next = [
                li for li in graph.links if next_loc_to_go in li.linked_zones
                ]
            for connected_link in connected_links_to_next:
                for dr in connected_link.list_of_drones_in:
                    if dr.previous_loc != next_loc_to_go:
                        next_loc_cap += 1
            if next_loc_cap < next_loc_to_go.max_drones:
                next_loc_to_go = next(
                    (link for link in graph.links
                        if (drone.loc in link.linked_zones
                            and next_loc_to_go in link.linked_zones)),
                    None)
            else:
                next_loc_to_go = None
        drone.next_loc = next_loc_to_go

    @staticmethod
    def make_drone_move(drone: Drone, graph: Graph) -> str | None:
        """
        Move a drone to its next location if capacity allows.

        Args:
            drone (Drone): Drone to move.
            graph (Graph): Graph containing the drone.

        Returns:
            str | None: Movement log, or None if the move fails.
        """
        drone.previous_loc = drone.loc
        if drone.next_loc is None:
            return None
        if isinstance(drone.next_loc, Link):
            link = graph.links[graph.links.index(drone.next_loc)]
            if len(link.list_of_drones_in) < link.max_link_capacity:
                if not isinstance(drone.loc, Hub):
                    return None
                next_loc = Orchestrator.get_other_extremity_of(drone.loc, link)
                if len(link.list_of_drones_in) >= next_loc.max_drones:
                    return None
                graph.hubs[graph.hubs.index(
                    drone.loc)].list_of_drones_in.remove(drone)
                link.list_of_drones_in.append(drone)
                drone.loc = link
                return f"D{drone.id}-{link.name}"
            else:
                return None
        next_loc = graph.hubs[graph.hubs.index(drone.next_loc)]
        if next_loc == drone.loc:
            return None
        if len(next_loc.list_of_drones_in) < next_loc.max_drones:
            if isinstance(drone.loc, Link):
                link = graph.links[graph.links.index(drone.loc)]
                link.list_of_drones_in.remove(drone)
            else:
                graph.hubs[graph.hubs.index(
                    drone.loc)].list_of_drones_in.remove(drone)
            next_loc.list_of_drones_in.append(drone)
            drone.loc = next_loc
            return f"D{drone.id}-{next_loc.name}"
        else:
            return None

    def schedule(self) -> list[list[str]]:
        """
        Schedule drone movements until all drones reach the destination.

        Returns:
            list[list[str]]: Movement logs grouped by simulation turn.
        """
        for drone in self.real_graph.drones:
            self.real_graph.start_hub.list_of_drones_in.append(drone)
        self.paths = Orchestrator.find_paths(self.real_graph)
        all_logs = []
        while (True):
            logs = []
            i = 0
            all_links: list[dict[str, Any]] = []
            while (i < len(self.real_graph.drones)):
                self.choose_drone_next_move(
                    self.real_graph.drones[i], self.paths, self.real_graph)
                link_cnc = None
                if isinstance(self.real_graph.drones[i].next_loc, Link):
                    link_cnc = self.real_graph.drones[i].next_loc
                else:
                    for g_link in self.real_graph.links:
                        if isinstance(self.real_graph.drones[i].loc, Link):
                            link_cnc = self.real_graph.drones[i].loc
                            break
                        else:
                            drone = self.real_graph.drones[i]
                            if (isinstance(drone.loc, Hub)
                                    and isinstance(drone.next_loc, Hub)):
                                link_name = [
                                    f"{
                                        drone.loc.name
                                    }-{
                                        drone.next_loc.name
                                    }",
                                    f"{
                                        drone.next_loc.name
                                    }-{
                                        drone.loc.name
                                    }"]
                                if g_link.name in link_name:
                                    link_cnc = g_link
                                    break
                if not isinstance(link_cnc, Link):
                    i += 1
                    continue
                link = {
                    "linked_zones": link_cnc.linked_zones,
                    "capacity": link_cnc.max_link_capacity
                }
                all_links_cncd_zn = [cnc["linked_zones"] for cnc in all_links]
                if not isinstance(self.real_graph.drones[i].loc, Link):
                    if link["linked_zones"] in all_links_cncd_zn:
                        loc = all_links_cncd_zn.index(link["linked_zones"])
                        all_links[loc]["capacity"] -= 1
                    else:
                        all_links.append(link)
                        all_links[len(all_links) -
                                  1]["capacity"] -= len(
                                      link_cnc.list_of_drones_in)
                        all_links[len(all_links) - 1]["capacity"] -= 1
                for t_link in all_links:
                    if t_link["linked_zones"] == link["linked_zones"]:
                        if t_link["capacity"] < 0:
                            self.real_graph.drones[
                                i].next_loc = self.real_graph.drones[i].loc
                move_log = self.make_drone_move(
                    self.real_graph.drones[i],
                    self.real_graph
                )
                if move_log is not None:
                    logs.append(move_log)
                if isinstance(self.real_graph.drones[i].loc, EndHub):
                    self.real_graph.drones.pop(i)
                    continue
                i += 1
            all_logs.append(logs)
            for log in logs:
                print(f"{log} ", end="")
            print()
            if len(self.real_graph.drones) <= 0:
                break
        return all_logs
