"""
Parse and validate graph configuration files.

Provides parsing utilities for drone, hub, and connection definitions.
"""

import re
from typing import Any, cast


class ParseError(Exception):
    """Represent an error occurring during input parsing."""

    def __init__(
            self,
            message: str = "Something went wrong with the parsing."):
        """
        Initialize the parsing exception.

        Args:
            message (str): Description of the parsing error.

        Returns:
            None
        """
        self.message = message
        super().__init__(self.message)


class Checker():
    """Validate and extract graph components from input lines."""

    raw_lines: list[str] = []

    @staticmethod
    def check_and_take_drones_nb(
            lines: list[str], graph: dict[str, int | str | list[Any]]
    ) -> list[str]:
        """
        Extract and validate the number of drones.

        Args:
            lines (list[str]): Input lines to process.
            graph (dict): Graph configuration to update.

        Returns:
            list[str]: Remaining unprocessed lines.

        Raises:
            ParseError: If the drone count is missing or invalid.
        """
        if not lines:
            raise ParseError(
                "The first line must define the number"
                " of drones using nb_drones: <positive_integer>"
            )
        result = re.fullmatch(r"\s*nb_drones\s*:\s*(\d+)\s*", lines[0])
        if not result or int(result.group(1)) <= 0:
            raise ParseError(
                "The first line must define the number"
                " of drones using nb_drones: <positive_integer>"
            )
        graph["nb_drones"] = int(result.group(1))
        lines.pop(0)
        return lines

    @staticmethod
    def check_hub_metadata(
        full_line: str, line: str, hub: dict[str, str | int]
        ) -> None:
        """
        Extract and validate hub metadata.

        Args:
            line (str): Metadata string to parse.
            hub (dict): Hub configuration to update.

        Returns:
            None

        Raises:
            ParseError: If metadata is invalid or duplicated.
        """
        result = re.fullmatch(r"\[([^\]]*)\]", line.strip())
        n = Checker.raw_lines.index(full_line) + 1
        if not result:
            raise ParseError(f"Invalid hub metadata format [line:{n}]")
        content = result.group(1)
        patterns = {
            "zone": r"zone=(\w+)",
            "color": r"color=(\w+)",
            "max_drones": r"max_drones=(\d+)"
        }
        data = {}
        for token in content.split():
            matched = False
            for name, regex in patterns.items():
                match = re.fullmatch(regex, token)
                if match:
                    if name in data:
                        raise ParseError(
                            f"Duplicate parameter in metadata:{name} [line:{n}]"
                        )
                    matched = True
                    data[name] = (int(match.group(1)) if name ==
                                  "max_drones" else match.group(1))
                    break
            if not matched:
                raise ParseError(
                    f"invalid parameter in metadata: {token} [line:{n}]"
                )
        if "max_drones" in data.keys():
            if int(data["max_drones"]) <= 0:
                err1 = "Invalid hub metadata format: the"
                raise ParseError(
                    f"{err1} max_drones should be greater than 0 [line:{n}]"
                )
        if "zone" in data.keys():
            zone = data["zone"]
            if zone not in ["priority", "restricted", "blocked", "normal"]:
                raise ParseError(
                    f" '{zone}' is not a valid type of zone [line:{n}]"
                    )
        if not data:
            raise ParseError(f"Hub metadata cannot be empty [line:{n}]")
        hub.update(data)

    @staticmethod
    def check_and_take_startpoint(
            lines: list[str], graph: dict[str, Any]
    ) -> list[str]:
        """
        Extract and validate the starting hub.

        Args:
            lines (list[str]): Input lines to process.
            graph (dict): Graph configuration to update.

        Returns:
            list[str]: Remaining unprocessed lines.

        Raises:
            ParseError: If the starting hub is missing or duplicated.
        """
        start = []
        for i in range(len(lines)):
            result = re.match(
                r"\s*start_hub\s*:\s*(\w+)\s+(-?\d+)\s+(-?\d+)\s*", lines[i])
            if result:
                start.append({"match": result, "loc": i})
        if len(start) == 0:
            err = " - A start_hub should have the format: "
            form = "start_hub: <name> <x> <y> [metadata]"
            raise ParseError(f"No start_hub found{err}{form}")
        if len(start) != 1:
            numbers = []
            for el in start:
                numbers.append(Checker.raw_lines.index(lines[el["loc"]]) + 1)
            if len(set(numbers)) == 1:
                raise ParseError("There must be exactly one start_hub")
            raise ParseError(
                "There must be exactly one start_hub"
                f"; Found start_hub lines on lines: {numbers}"
                )
        else:
            first = start[0]
            start_loc = cast(int, first["loc"])
            start_line = lines[start_loc]
            lines.pop(start_loc)
            start_hub: dict[str, Any] = graph["start_hub"]
            match = cast(re.Match[str], first["match"])
            start_hub["name"] = match.group(1)
            start_hub["coord"][0] = match.group(2)
            if int(start_hub["coord"][0]) >= 1000:
                start_hub["coord"][0] = 1000
            if int(start_hub["coord"][0]) <= -1000:
                start_hub["coord"][0] = -1000
            start_hub["coord"][1] = match.group(3)
            if int(start_hub["coord"][1]) >= 1000:
                start_hub["coord"][1] = 1000
            if int(start_hub["coord"][1]) <= -1000:
                start_hub["coord"][1] = -1000
            start_hub["line"] = Checker.raw_lines.index(start_line) + 1
            if len(start_line) > len(match.group(0)):
                Checker.check_hub_metadata(
                    start_line,
                    start_line[len(match.group(0)):],
                    graph["start_hub"]
                )
        return (lines)

    @staticmethod
    def check_and_take_endpoint(
            lines: list[str], graph: dict[str, int | str | list[Any]]
    ) -> list[str]:
        """
        Extract and validate the destination hub.

        Args:
            lines (list[str]): Input lines to process.
            graph (dict): Graph configuration to update.

        Returns:
            list[str]: Remaining unprocessed lines.

        Raises:
            ParseError: If the destination hub is missing or duplicated.
        """
        end: list[dict[str, Any]] = []
        for i in range(len(lines)):
            result = re.match(
                r"\s*end_hub\s*:\s*(\w+)\s+(-?\d+)\s+(-?\d+)\s*", lines[i])
            if result:
                end.append({"match": result, "loc": i})
        if len(end) == 0:
            err = " - A end_hub should have the format: "
            form = "end_hub: <name> <x> <y> [metadata]"
            raise ParseError(f"No end_hub found{err}{form}")
        if len(end) != 1:
            numbers = []
            for el in end:
                numbers.append(Checker.raw_lines.index(lines[el["loc"]]) + 1)
            if len(set(numbers)) == 1:
                raise ParseError("There must be exactly one end_hub")
            raise ParseError(
                "There must be exactly one end_hub"
                f"; Found end_hub lines on lines: {numbers}"
                )
        else:
            endpoint = end[0]
            loc = cast(int, endpoint["loc"])
            match = cast(re.Match[str], endpoint["match"])
            end_line = lines[loc]
            lines.pop(loc)
            end_hub = cast(dict[str, Any], graph["end_hub"])
            end_hub["name"] = match.group(1)
            end_hub["coord"][0] = match.group(2)
            if int(end_hub["coord"][0]) >= 1000:
                end_hub["coord"][0] = 1000
            if int(end_hub["coord"][0]) <= -1000:
                end_hub["coord"][0] = -1000
            end_hub["coord"][1] = match.group(3)
            if int(end_hub["coord"][1]) >= 1000:
                end_hub["coord"][1] = 1000
            if int(end_hub["coord"][1]) <= -1000:
                end_hub["coord"][1] = -1000
            end_hub["line"] = Checker.raw_lines.index(end_line) + 1
            if len(end_line) > len(match.group(0)):
                Checker.check_hub_metadata(
                    end_line,
                    end_line[len(match.group(0)):],
                    end_hub
                )
        return (lines)

    @staticmethod
    def check_and_take_hubs(
        lines: list[str], graph: dict[str, Any]
    ) -> list[str]:
        """
        Extract and validate intermediate hubs.

        Args:
            lines (list[str]): Input lines to process.
            graph (dict): Graph configuration to update.

        Returns:
            list[str]: Remaining unprocessed lines.

        Raises:
            ParseError: If a hub definition is invalid or duplicated.
        """
        hubs: list[dict[str, Any]] = []
        to_remove: list[int] = []
        for i in range(len(lines)):
            n = Checker.raw_lines.index(lines[i]) + 1
            hub: dict[str, Any] = {
                "name": "",
                "coord": [0, 0],
                "zone": "normal",
                "color": "white",
                "max_drones": 1,
                "line": Checker.raw_lines.index(lines[i]) + 1
            }
            result = re.match(
                r"\s*hub\s*:\s*(\w+)\s+(-?\d+)\s+(-?\d+)\s*", lines[i]
                )
            if result:
                hub["name"] = result.group(1)
                hub["coord"][0] = result.group(2)
                if int(hub["coord"][0]) >= 1000:
                    hub["coord"][0] = 1000
                if int(hub["coord"][0]) <= -1000:
                    hub["coord"][0] = -1000
                hub["coord"][1] = result.group(3)
                if int(hub["coord"][1]) >= 1000:
                    hub["coord"][1] = 1000
                if int(hub["coord"][1]) <= -1000:
                    hub["coord"][1] = -1000
                if len(lines[i]) > len(result.group(0)):
                    Checker.check_hub_metadata(
                        lines[i],
                        lines[i][len(result.group(0)):],
                        hub
                    )
                to_remove.append(i)
                if any(hub["name"] == hub_already_in["name"]
                       for hub_already_in in hubs):
                    raise ParseError(
                        f"Duplicate zone name: {hub["name"]} [line:{n}]"
                    )
                hubs.append(hub)
        for i in range(len(to_remove) - 1, -1, -1):
            lines.pop(to_remove[i])
        graph["hubs"].extend(hubs)
        return (lines)

    @staticmethod
    def check_link_metadata(full_line: str, line: str, link: dict[str, Any]) -> None:
        """
        Extract and validate link capacity metadata.

        Args:
            line (str): Link metadata string.
            link (dict): Link configuration to update.

        Returns:
            None

        Raises:
            ParseError: If the capacity is missing or invalid.
        """
        n = Checker.raw_lines.index(full_line) + 1
        result = re.fullmatch(
            r"\[\s*max_link_capacity=(\d+)\s*\]", line.strip())
        if not result or int(result.group(1)) <= 0:
            err2 = "Invalid link metadata format, max_link_capacity metadata"
            err3 = f"where max is a number greater than 0 [line:{n}]"
            raise ParseError(
                f"{err2} should look like: [max_link_capacity=<max>] {err3}"
            )
        link["max_link_capacity"] = int(result.group(1))

    @staticmethod
    def check_and_take_links(
            lines: list[str], graph: dict[str, Any]) -> list[str]:
        """
        Extract and validate connections between hubs.

        Args:
            lines (list[str]): Input lines to process.
            graph (dict): Graph configuration containing defined hubs.

        Returns:
            list[str]: Remaining unprocessed lines.

        Raises:
            ParseError: If a connection is invalid, duplicated,
                self-referencing, or references an undefined hub.
        """
        links: list[dict[str, Any]] = []
        to_remove: list[int] = []
        for i in range(len(lines)):
            n = Checker.raw_lines.index(lines[i]) + 1
            link: dict[str, Any] = {
                "linked_zones": set(),
                "max_link_capacity": 1
            }
            result = re.match(r"\s*connection\s*:\s*(\w+)-(\w+)\s*", lines[i])
            if result:
                link["linked_zones"] = {result.group(1), result.group(2)}
                if len(link["linked_zones"]) == 1:
                    raise ParseError(
                        f"the zone '{result.group(1)}' is linked to itself [line: {n}]"
                    )
                for zone in link["linked_zones"]:
                    all_hubs = [{g_hub["name"]: g_hub["line"]} for g_hub in graph["hubs"]]
                    all_hubs.append({graph["start_hub"]["name"] : graph["start_hub"]["line"]})
                    all_hubs.append({graph["end_hub"]["name"] : graph["end_hub"]["line"]})
                    all_names = [next(iter(hub)) for hub in all_hubs]
                    if zone not in all_names:
                        raise ParseError(f"{zone} is an undefined zone [line: {n}]")
                    else:
                        for hub in all_hubs:
                            if next(iter(hub)) == zone:
                                loc = hub[zone]
                        if loc > n:
                            raise ParseError(f"{zone} is only defined later [line: {n}]")
                if len(lines[i]) > len(result.group(0)):
                    Checker.check_link_metadata(
                        lines[i],
                        lines[i][len(result.group(0)):],
                        link
                    )
                to_remove.append(i)
                if any(link["linked_zones"] == link_already_in["linked_zones"]
                       for link_already_in in links):
                    raise ParseError(
                        f"Duplicate connection: {
                            result.group(1)}-{
                            result.group(2)} [line: {n}]"
                    )
                links.append(link)
        for i in range(len(to_remove) - 1, -1, -1):
            lines.pop(to_remove[i])
        graph["links"].extend(links)
        return (lines)


class Parser():
    """Read and parse graph configuration files."""

    @staticmethod
    def parse(
            path: str, graph: dict[str, Any]) -> None:
        """
        Parse a configuration file and populate the graph data.

        Args:
            path (str): Path to the configuration file.
            graph (dict[str, Any]): Graph configuration to populate.

        Returns:
            None

        Raises:
            ParseError: If the file cannot be read or contains
                invalid configuration data.
        """
        try:
            with open(path, "r") as f:
                Checker.raw_lines = f.readlines()
            
            lines = [
                    x for x in Checker.raw_lines if (
                        x.strip() and not x.lstrip().startswith("#")
                    )
                ]
        except OSError as error:
            err_mess = "There is something wrong with the given path"
            raise ParseError(f"{err_mess} : {error}")
        try:
            Checker.check_and_take_drones_nb(lines, graph)
            Checker.check_and_take_startpoint(lines, graph)
            Checker.check_and_take_endpoint(lines, graph)
            Checker.check_and_take_hubs(lines, graph)
            Checker.check_and_take_links(lines, graph)
        except ParseError as error:
            err_mess = "Invalid input"
            raise ParseError(f"{err_mess}: {error}")
        if lines:
            print("The following lines are invalid:\n")
            for line in lines:
                line_number = Checker.raw_lines.index(line) + 1
                print(f"\t[line:{line_number}] - '{line.strip()}'")
            raise ParseError(
                f""
            )
