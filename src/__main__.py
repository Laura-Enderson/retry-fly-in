"""Provide the Main entry point for the drone simulation application."""

from src import Parser, ParseError, Orchestrator, Graph, Gui, Tui, InitError
import copy


class Main():
    """Control the execution flow of the drone simulation."""

    @staticmethod
    def fly_in() -> None:
        """
        Run the drone simulation from input selection to visualization.

        Handles configuration parsing, graph initialization,
        drone scheduling, and optional GUI display.

        Returns:
            None
        """
        print("\nFly-in\n")
        try:
            orch = Orchestrator()
            path = Tui.select_txt_files()
            if path is None:
                return
            try:
                Parser.parse(path, orch.graph)
            except ParseError as error:
                print(error)
                return
            else:
                try:
                    orch.real_graph = Graph.init_graph(orch.graph)
                except InitError as error:
                    print(error)
                    return
                else:
                    graph = copy.deepcopy(orch.real_graph)
                try:
                    logs = orch.schedule()
                except RuntimeError as err:
                    print(f"Error occures during program process: {err}")
                    return
        except KeyboardInterrupt:
            print("The user interrupted the program.")
            return
        except Exception as error:
            print(error)
            return
        if Tui.ask_for_gui():
            try:
                Gui.display_graph(graph, logs)
            except KeyboardInterrupt:
                print("\nOOPS!")
                return


if __name__ == "__main__":
    try:
        Main.fly_in()
    except KeyboardInterrupt:
        print("The user interrupted the program.")
