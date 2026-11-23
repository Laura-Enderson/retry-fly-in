"""
Provide graphical visualization tools for Fly-in.

This module contains utility functions and the Gui class used to
render graphs, display drone positions, and visualize simulation
progress through a Pygame interface.

It also handles user interactions, including camera navigation,
zoom adjustments, simulation speed control, and pause management.
"""

import pygame
from ..tools.elements import Graph, Hub
import copy
import time
from typing import Any


class Utils():
    """Provide utility methods for graph visualization and timing."""

    @staticmethod
    def define_scale(i_scale: float, graph: Graph) -> float:
        """
        Calculate a suitable display scale for a graph.

        Adjusts the initial scale recursively to ensure that all graph
        hubs remain within the GUI window boundaries.

        Args:
            i_scale (float): The initial scale factor.
            graph (Graph): The graph whose coordinates determine
                the required display boundaries.

        Returns:
            float: The adjusted scale factor that fits the graph
                within the GUI window.
        """
        scale = copy.copy(i_scale)
        d = 100
        min_x = graph.start_hub.coord[0]
        max_x = graph.start_hub.coord[0]
        min_y = graph.start_hub.coord[1]
        max_y = graph.start_hub.coord[1]
        for hub in graph.hubs:
            x = hub.coord[0]
            y = hub.coord[1]
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
        if (Gui.origin[0] + ((min_x * d) + 100) * scale) < 0:
            scale -= 0.1
        elif (Gui.origin[0] + ((max_x * d) + 100) * scale) > Gui.width:
            scale -= 0.1
        elif (Gui.origin[0] + ((min_y * d) + 100) * scale) < 0:
            scale -= 0.1
        elif (Gui.origin[0] + ((max_y * d) + 100) * scale) > Gui.height:
            scale -= 0.1
        if scale != i_scale:
            scale = Utils.define_scale(scale, graph)
        return scale

    @staticmethod
    def wait(duration: int) -> int:
        """
        Wait for a specified duration while processing GUI events.

        Continuously checks for user events during the waiting period.
        Stops waiting immediately if the user closes the GUI window.

        Args:
            duration (int): The waiting duration in milliseconds.

        Returns:
            int: 1 if the waiting period completes successfully,
                or 0 if the GUI is closed before completion.
        """
        pygame.init()
        end = time.perf_counter() * 1000 + duration
        now = time.perf_counter() * 1000
        while now < end:
            now = time.perf_counter() * 1000
            running = Gui.handle_events()
            if not running:
                return 0
        return 1


class Gui():
    """
    Manage the graphical visualization of a drone simulation.

    Provides methods to initialize the Pygame window, render
    graph elements and drones, process logs, and display
    simulation progress.

    The class also manages visualization settings such as
    zoom level, display scale, simulation speed, and pause state.

    Attributes:
        size (tuple[int, int]): Dimensions of the Pygame window.
        width (int): Width of the visualization window.
        height (int): Height of the visualization window.
        black (tuple[int, int, int, int]): Background color.
        origin (tuple[int, int]): Origin coordinates used
            to position graph elements.
        zoom (float): Current zoom factor.
        pause (bool): Indicates whether the simulation is paused.
        graph_data (dict[str, Any]): Stores graph information,
            display surfaces, scaling factors, and simulation
            settings.
    """

    size = width, height = 1700, 800
    black = 0, 0, 0, 0
    origin = 200, 400
    graph_data: dict[str, Any] = {}

    @staticmethod
    def display_graph(graph: Graph, logs: list[list[str]]) -> None:
        """
        Initialize and display the graph visualization window.

        Creates the Pygame window, initializes the graph representation,
        draws the drones and graph elements,
        and displays the simulation instructions.

        The user can navigate the visualization,
        and launch the simulation using the keyboard.

        Args:
            graph (Graph): The graph to visualize.
            logs (list[list[str]]): Simulation logs describing the
                successive movements of drones.

        Returns:
            None
        """
        pygame.init()
        Gui.graph_data["graph"] = copy.deepcopy(graph)
        Gui.graph_data["scale"] = Utils.define_scale(
            10, Gui.graph_data["graph"])
        Gui.graph_data["duration"] = 600
        window = pygame.display.set_mode(Gui.size)
        pygame.display.set_caption("Fly-in")
        Gui.graph_data["all"] = pygame.Surface(
            (Gui.width, Gui.height), pygame.SRCALPHA)
        graph_rep = Gui.draw_graph()
        graph_rect = graph_rep.get_rect()
        drones_surf = pygame.Surface((Gui.width, Gui.height), pygame.SRCALPHA)
        Gui.graph_data["all"].blit(graph_rep, graph_rect)
        Gui.draw_drones(drones_surf)
        Gui.graph_data["all"].blit(drones_surf, (0, 0))
        window.blit(Gui.graph_data["all"], (0, 0))
        loc = -1
        Gui.display_instructions(window, logs, loc)
        pygame.display.flip()
        running = True
        Gui.graph_data["all_rect"] = Gui.graph_data["all"].get_rect()
        while running:
            Gui.graph_data["all_rect"].center = Gui.catch_input()
            running = Gui.handle_events()
            window.fill(Gui.black)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                result = Gui.play(graph, window, drones_surf, graph_rep, logs)
                loc = len(logs) - 1
                if result == 0:
                    running = False
            window.blit(Gui.graph_data["all"], Gui.graph_data["all_rect"])
            Gui.display_instructions(window, logs, loc)
            pygame.display.flip()
        pygame.quit()

    @staticmethod
    def fluid_transition(
        window: pygame.Surface, graph_rep: pygame.Surface,
        drone_surf: pygame.Surface, graph_now: Graph,
        graph_next: Graph, logs: list[list[str]],
            loc: int) -> int:
        """
        Create a smooth vizualisation of the transition.

        Args:
            window (pygame.Surface): The main Pygame display surface.
            graph_rep (pygame.Surface): The surface containing
                the graph representation.
            drones_surf (pygame.Surface): The surface containing
                the drone representations.
            graph_now: the graph before the transition.
            graph_next: the graph after the transition.

        Returns:
            int: 1 if the transition reaches its end,
                or 0 if the transition is interrupted.
        """
        moving_drones: list[dict[str, Any]] = []
        for drone in graph_now.drones:
            if drone.loc == graph_next.drones[drone.id - 1].loc:
                continue
            if isinstance(drone.loc, Hub):
                start_loc: tuple[float, float] = drone.loc.coord
            else:
                start_loc = (
                    (drone.loc.linked_zones[
                        0].coord[
                            0] + drone.loc.linked_zones[
                                1].coord[
                                    0]) / 2,
                    (
                        drone.loc.linked_zones[
                            0].coord[
                                1] + drone.loc.linked_zones[
                                    1].coord[1]) / 2)
            drone_loc = graph_next.drones[drone.id - 1].loc
            if isinstance(drone_loc, Hub):
                end_loc: tuple[float, float] = drone_loc.coord
            else:
                end_loc = (
                    (drone_loc.linked_zones[
                            0].coord[
                                0] + drone_loc.linked_zones[
                                        1].coord[
                                            0]) / 2,
                    (drone_loc.linked_zones[
                            0].coord[
                                1] + drone_loc.linked_zones[
                                        1].coord[1]) / 2)
            moving_drones.append(
                {
                    "drone": drone,
                    "start": start_loc,
                    "end": end_loc,
                    "progress": 0.0
                }
            )
        if not moving_drones:
            return 1
        running = True
        while running:
            Gui.graph_data["all_rect"].center = Gui.catch_input()
            running = Gui.handle_events()
            if not running:
                return 0
            window.fill(Gui.black)
            Gui.graph_data["all"].fill(Gui.black)
            drone_surf.fill(Gui.black)
            graph_rep.fill(Gui.black)
            graph_rep = Gui.draw_graph()
            for moving_drone in moving_drones:
                moving_drone["progress"] += 0.01
                if moving_drone["progress"] > 1.0:
                    moving_drone["progress"] = 1.0
                new_x = moving_drone[
                    "start"][
                        0] + (
                            moving_drone[
                                "end"][
                                    0] - moving_drone[
                                        "start"][
                                            0]) * moving_drone[
                                                "progress"]
                new_y = moving_drone[
                    "start"][
                        1] + (
                            moving_drone[
                                "end"][
                                    1] - moving_drone[
                                        "start"][
                                            1]) * moving_drone[
                                                "progress"]
                Gui.draw_drone(
                    drone_surf, moving_drone[
                        "drone"].id, Gui.graph_data[
                            "scale"], (new_x, new_y))
            Gui.graph_data["all"].blit(graph_rep, (0, 0))
            Gui.graph_data["all"].blit(drone_surf, (0, 0))
            window.blit(Gui.graph_data["all"], (Gui.graph_data["all_rect"]))
            Gui.display_instructions(window, logs, loc)
            pygame.display.flip()
            if all(
                moving_drone[
                    "progress"] >= 1.0 for moving_drone in moving_drones):
                break
        return 1

    @staticmethod
    def play(graph: Graph, window: pygame.Surface, drones_surf: pygame.Surface,
             graph_rep: pygame.Surface, logs: list[list[str]]) -> int:
        """
        Execute and display the drone movement simulation.

        Reconstructs the graph state, processes simulation logs,
        updates drone positions, and refreshes the visualization
        at each simulation step.

        Args:
            graph (Graph): The initial graph used for the simulation.
            window (pygame.Surface): The main Pygame display surface.
            drones_surf (pygame.Surface): The surface containing
                the drone representations.
            graph_rep (pygame.Surface): The surface containing
                the graph representation.
            logs (list[list[str]]): Simulation logs containing
                the successive drone movements.

        Returns:
            int: 1 if the simulation reaches its end,
                or 0 if the simulation is interrupted.
        """
        all_rect = Gui.graph_data["all_rect"]
        window.fill(Gui.black)
        Gui.graph_data["all"].fill(Gui.black)
        Gui.graph_data["graph"] = copy.deepcopy(graph)
        drones_surf.fill(Gui.black)
        Gui.graph_data["all"].blit(graph_rep, (0, 0))
        Gui.draw_drones(drones_surf)
        Gui.graph_data["all"].blit(drones_surf, (0, 0))
        window.blit(Gui.graph_data["all"], all_rect)
        Gui.display_instructions(window, logs, -1)
        pygame.display.flip()
        running = True
        loc = 0
        while running:
            Gui.graph_data["all_rect"].center = Gui.catch_input()
            window.fill(Gui.black)
            Gui.graph_data["all"].fill(Gui.black)
            drones_surf.fill(Gui.black)
            graph_rep.fill(Gui.black)
            graph_now = copy.deepcopy(Gui.graph_data["graph"])
            Gui.update_graph(logs[loc])
            graph_next = copy.deepcopy(Gui.graph_data["graph"])
            running = Gui.handle_events()
            if not running:
                break
            result = Gui.fluid_transition(
                window, graph_rep, drones_surf, graph_now,
                graph_next, logs, loc)
            if result == 0:
                break
            loc += 1
            if loc >= len(logs):
                return 1
            end = time.perf_counter() * 1000 + Gui.graph_data["duration"]
            now = time.perf_counter() * 1000
            while now < end:
                now = time.perf_counter() * 1000
                running = Gui.handle_events()
                Gui.graph_data["all_rect"].center = Gui.catch_input()
                if not running:
                    break
        return 0

    @staticmethod
    def display_instructions(window: pygame.Surface,
                             logs: list[list[str]], loc: int) -> None:
        """
        Display simulation instructions and progress information.

        Renders keyboard controls, the current simulation speed,
        and the number of movements already processed.

        Args:
            window (pygame.Surface): The Pygame surface on which
                the instructions are displayed.
            logs (list[list[str]]): The complete simulation logs.
            loc (int): The index of the current simulation step.
                A negative value indicates that the simulation
                has not started.

        Returns:
            None
        """
        font = pygame.font.Font(None, 20)
        color = (0, 255, 0)

        play = font.render(
            "Press 'SPACE' to launch the simulation.",
            True,
            color)
        directions = font.render("Use arrow keys to navigate.", True, color)
        if loc < 0:
            nb_moves = 0
        else:
            nb_moves = loc + 1
        nb_of_turns = font.render(
            f"number of moves: {nb_moves}/{len(logs)}.", True, color)

        window.blit(nb_of_turns, (1500, 20))
        window.blit(play, (20, 720))
        window.blit(directions, (20, 740))

    @staticmethod
    def draw_drones(surf: pygame.Surface) -> None:
        """
        Draw all drones at their current graph locations.

        Determines each drone's position based on whether it is
        located in a hub or on a link. For drones on links,
        the position is calculated using the midpoint between
        the two connected hubs.

        Args:
            surf (pygame.Surface): The surface on which the drones
                are drawn.

        Returns:
            None
        """
        scale = Gui.graph_data["scale"]
        graph = Gui.graph_data["graph"]
        for drone in graph.drones:
            if isinstance(drone.loc, Hub):
                loc = drone.loc.coord
            else:
                a = drone.loc.linked_zones[0].coord
                b = drone.loc.linked_zones[1].coord
                loc = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            Gui.draw_drone(surf, drone.id, scale, loc)

    @staticmethod
    def draw_drone(surf: pygame.Surface, id: int,
                   scale: float, loc: tuple[int, int]) -> None:
        """
        Draw an individual drone and its identifier.

        Loads the drone image, resizes it according to the display
        scale, and renders its identifier at the specified position.

        Args:
            surf (pygame.Surface): The surface on which the drone
                is drawn.
            id (int): The unique identifier of the drone.
            scale (float): The scaling factor applied to the drone
                image and its identifier.
            loc (tuple[int, int]): The drone's graph coordinates.

        Returns:
            None
        """
        d = 100
        r_loc = (Gui.origin[0] + (loc[0] * d * scale),
                 Gui.origin[1] + ((-loc[1]) * d * scale))
        drone = pygame.image.load("src/GUI/assets/drone.png").convert_alpha()
        drone = pygame.transform.scale(drone, (30 * scale, 30 * scale))
        font = pygame.font.Font(None, int(10 * scale))
        number = font.render(str(id), False, (225, 0, 0))
        drone_rect = drone.get_rect(center=r_loc)
        surf.blit(drone, drone_rect)
        number_rect = number.get_rect(center=(r_loc[0], r_loc[1]))
        surf.blit(number, number_rect)

    @staticmethod
    def draw_graph() -> pygame.Surface:
        """
        Render the graph, including hubs, links, and their capacities.

        Draws links between connected hubs, displays their current
        drone occupancy and maximum capacity, and renders hubs
        according to their respective zones and colors.

        Returns:
            pygame.Surface: A Pygame surface containing the complete
                graph visualization.
        """
        background = pygame.Surface((Gui.width, Gui.height))
        d = 100
        inf = float("inf")
        scale = Gui.graph_data["scale"]
        graph = Gui.graph_data["graph"]
        line_surf = pygame.Surface((Gui.width, Gui.height), pygame.SRCALPHA)
        font = pygame.font.Font(None, int(10 * scale))
        for link in graph.links:
            max = link.max_link_capacity
            if max != inf:
                max = int(max)
            capacity = font.render(
                f"{len(link.list_of_drones_in)}/{max}", False, (220, 220, 220))
            hub1 = link.linked_zones[0]
            hub2 = link.linked_zones[1]
            loc1 = (Gui.origin[0] + ((hub1.coord[0]) * d * scale),
                    Gui.origin[1] + ((-hub1.coord[1]) * d * scale))
            loc2 = (Gui.origin[0] + ((hub2.coord[0]) * d * scale),
                    Gui.origin[1] + ((-hub2.coord[1]) * d * scale))
            pygame.draw.line(line_surf, (255, 255, 255, 15),
                             loc1, loc2, int(5 * scale))
            center = (((loc1[0] + loc2[0]) / 2) -
                      (20 * scale), (loc1[1] + loc2[1]) / 2)
            capacity_rect = capacity.get_rect(center=center)
            background.blit(capacity, capacity_rect)
        background.blit(line_surf, (0, 0))

        for hub in graph.hubs:
            max = hub.max_drones
            if max != inf:
                max = int(max)
            hub_name = font.render(
                f"{hub.name}[drones:{len(hub.list_of_drones_in)}/{max}]",
                False,
                hub.color.as_rgb_tuple()
            )
            if hub.zone == "priority":
                hub_represent = pygame.image.load(
                    "src/GUI/assets/priority_zone.png").convert_alpha()
            elif hub.zone == "normal":
                hub_represent = pygame.image.load(
                    "src/GUI/assets/normal_zone.png").convert_alpha()
            elif hub.zone == "restricted":
                hub_represent = pygame.image.load(
                    "src/GUI/assets/restricted_zone.png").convert_alpha()
            elif hub.zone == "blocked":
                hub_represent = pygame.image.load(
                    "src/GUI/assets/blocked_zone.png").convert_alpha()
            hub_represent = Gui.recolor(
                hub_represent, hub.color.as_rgb_tuple())
            hub_represent = pygame.transform.scale(
                hub_represent, (40 * scale, 40 * scale))
            loc = (Gui.origin[0] + (hub.coord[0] * d * scale),
                   Gui.origin[1] + ((-hub.coord[1]) * d * scale))
            hub_rect = hub_represent.get_rect(center=loc)
            name_rect = hub_name.get_rect(
                center=(loc[0], loc[1] + (20 * scale)))
            background.blit(hub_represent, hub_rect)
            background.blit(hub_name, name_rect)
        return background

    @staticmethod
    def handle_events() -> bool:
        """
        Process pending Pygame events.

        Checks the event queue for window closure events and
        determines whether the GUI should continue running.

        Returns:
            bool: True if the GUI should continue running,
                or False if a window closure event is detected.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    @staticmethod
    def catch_input() -> tuple[int, int]:
        """
        Process keyboard inputs and update visualization settings.

        Handles camera movement, zoom adjustments, simulation speed
        changes, and pause toggling based on keyboard inputs.

        Returns:
            tuple[int, int]: The updated center coordinates of
                the visualization rectangle.
        """
        rect = Gui.graph_data["all_rect"]
        loc = list(rect.center)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            loc[0] += (10 * Gui.graph_data["scale"])
        if keys[pygame.K_LEFT]:
            loc[0] -= (10 * Gui.graph_data["scale"])
        if keys[pygame.K_UP]:
            loc[1] -= (10 * Gui.graph_data["scale"])
        if keys[pygame.K_DOWN]:
            loc[1] += (10 * Gui.graph_data["scale"])
        return tuple(loc)

    @staticmethod
    def update_graph(logs: list[str]) -> None:
        """
        Update drone positions according to simulation log entries.

        Parses each log entry to identify the drone and its next
        destination, removes the drone from its current location,
        and adds it to the destination hub or link.

        Args:
            logs (list[str]): A list of movement instructions.
                Each entry identifies a drone and its next location.

        Returns:
            None
        """
        graph_data = Gui.graph_data
        for log in logs:
            if not log:
                continue
            drone_id_str, drone_next_loc = log.split("-", 1)
            drone_id = int(drone_id_str[1:])
            if "-" in drone_next_loc:
                next_loc = [
                    link for link in graph_data["graph"].links
                    if link.name == drone_next_loc.strip()
                ][0]
            else:
                next_loc = [
                    hub for hub in graph_data["graph"].hubs
                    if hub.name == drone_next_loc.strip()
                ][0]
            drone = [
                dr for dr in graph_data["graph"].drones if dr.id == drone_id
            ][0]
            l_drone_loc = [
                loc for loc in graph_data["graph"].hubs
                if drone in loc.list_of_drones_in
            ]
            if not l_drone_loc:
                l_drone_loc = [
                    loc for loc in graph_data["graph"].links
                    if drone in loc.list_of_drones_in
                ]
            drone_loc = l_drone_loc[0]
            drone_loc.list_of_drones_in.remove(drone)
            next_loc.list_of_drones_in.append(drone)
            drone.loc = next_loc

    @staticmethod
    def recolor(image: Any, color: tuple[int]) -> Any:
        """
        Apply a color tint to an image using multiplicative blending.

        Creates a copy of the original image and applies the specified
        color while preserving the image's transparency.

        Args:
            image (Any): The original image to recolor.
            color (tuple[int]): The RGB color used to tint the image.

        Returns:
            Any: A new image containing the recolored result.
        """
        result = image.copy()
        overlay = pygame.Surface(image.get_size())
        overlay.fill(color)
        result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        return result
