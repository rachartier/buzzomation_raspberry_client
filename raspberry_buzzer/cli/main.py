import uuid

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from raspberry_buzzer.src.buzzer_monitor import BuzzerMonitor
from raspberry_buzzer.src.game_api import GameAPI
from raspberry_buzzer.src.player_manager import PlayerManager

console = Console()


class BuzzerCLI:
    def __init__(self):
        self.player_manager = PlayerManager()
        self.game_api = GameAPI()
        self.buzzer_monitor = BuzzerMonitor(self.game_api, self.player_manager)

    def show_header(self):
        """Display the application header"""
        console.print("Buzzer System CLI", style="bold")
        console.print("Raspberry Pi Buzzer Controller", style="dim")
        console.print("-" * 50)
        console.print()

    def show_status(self):
        """Display current system status"""
        players = self.player_manager.get_all_players()
        enabled_players = sum(1 for p in players.values() if p.enabled)

        console.print("SYSTEM STATUS")
        console.print("-" * 20)
        console.print(f"Players Configured:  {len(players)}")
        console.print(f"Players Enabled:     {enabled_players}")

        if self.game_api.connected:
            console.print("Server Status:       Connected", style="green")
        else:
            console.print("Server Status:       Disconnected", style="red")

        if self.game_api.game_id:
            console.print(f"Game ID:             {self.game_api.game_id}")

        if self.game_api.buzzers_available:
            console.print("Buzzers:             Available", style="green")
        else:
            console.print("Buzzers:             Unavailable", style="red")

        if self.buzzer_monitor.monitoring:
            console.print("Monitoring:          Active", style="green")
        else:
            console.print("Monitoring:          Stopped", style="red")
        console.print()

    def show_players(self):
        """Display all configured players"""
        players = self.player_manager.get_all_players()

        if not players:
            console.print("No players configured")
            return

        console.print("PLAYERS")
        console.print("-" * 50)

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", width=10)
        table.add_column("Name", width=20)
        table.add_column("GPIO Pin", width=10, justify="center")
        table.add_column("Status", width=10)

        for pid, config in players.items():
            status = "Enabled" if config.enabled else "Disabled"
            status_style = "green" if config.enabled else "red"
            table.add_row(
                pid, config.name, str(config.gpio_pin), Text(status, style=status_style)
            )

        console.print(table)
        console.print()

    def show_menu(self):
        """Display the main menu options"""
        console.print("COMMANDS")
        console.print("-" * 30)

        commands = [
            ("status", "Show system status"),
            ("list", "List all players"),
            ("add", "Add new player"),
            ("remove", "Remove player"),
            ("connect", "Connect to server/game"),
            ("monitor", "Start monitoring buzzers"),
            ("mock", "Simulate buzzer press"),
            ("help", "Show help"),
            ("quit", "Exit application"),
        ]

        for cmd, desc in commands:
            console.print(f"  {cmd:<10} {desc}")
        console.print()

    def add_player(self):
        """Add a new player with Rich prompts"""
        console.print("Add New Player", style="bold")
        console.print("-" * 20)

        name = Prompt.ask("Player name")
        if not name.strip():
            console.print("Error: Invalid name", style="red")
            return

        pins = self.player_manager.get_available_gpio_pins()
        if not pins:
            console.print("Error: No GPIO pins available", style="red")
            return

        console.print(f"Available GPIO pins: {', '.join(map(str, pins))}")

        try:
            pin = IntPrompt.ask(
                "GPIO pin", choices=[str(p) for p in pins], show_choices=False
            )
        except KeyboardInterrupt:
            console.print("Cancelled", style="yellow")
            return

        pid = str(uuid.uuid4())[:8]
        if self.player_manager.add_player(pid, name.strip(), pin):
            console.print(
                f"Added player '{name}' on GPIO pin {pin} (ID: {pid})", style="green"
            )
        else:
            console.print("Error: Failed to add player", style="red")

    def remove_player(self):
        """Remove a player with confirmation"""
        players = self.player_manager.get_all_players()
        if not players:
            console.print("No players to remove", style="yellow")
            return

        console.print("Remove Player", style="bold")
        console.print("-" * 20)
        self.show_players()

        player_ids = list(players.keys())

        try:
            pid = Prompt.ask(
                "Player ID to remove", choices=player_ids, show_choices=False
            )

            player_name = players[pid].name
            if Confirm.ask(f"Remove player '{player_name}'?"):
                if self.player_manager.remove_player(pid):
                    console.print(f"Player '{player_name}' removed", style="green")
                else:
                    console.print("Error: Failed to remove player", style="red")
            else:
                console.print("Cancelled", style="yellow")

        except KeyboardInterrupt:
            console.print("Cancelled", style="yellow")

    def connect_to_game(self):
        """Connect to server and join game"""
        console.print("Connect to Game", style="bold")
        console.print("-" * 20)

        players = self.player_manager.get_all_players()
        if not players:
            console.print(
                "Error: No players configured. Add players first.", style="red"
            )
            return

        try:
            url = Prompt.ask("Server URL", default=self.game_api.server_url)

            code = Prompt.ask("Game code")
            if not code.strip():
                console.print("Error: Game code required", style="red")
                return

        except KeyboardInterrupt:
            console.print("Cancelled", style="yellow")
            return

        console.print("Connecting to server...", style="yellow")

        self.game_api.server_url = url
        if not self.game_api.connect_to_server():
            console.print("Error: Failed to connect to server", style="red")
            return

        console.print("Connected to server", style="green")
        console.print("Registering players...", style="yellow")

        success_count = 0
        for pid, config in players.items():
            if not config.enabled:
                continue

            result = self.game_api.join_game(code.strip(), config.name)
            if result:
                self.game_api.register_player_mapping(pid, result["playerId"])
                success_count += 1
                console.print(f"Registered {config.name}", style="green")
            else:
                console.print(f"Failed to register {config.name}", style="red")

        if success_count > 0:
            self.buzzer_monitor.start_monitoring()
            console.print(
                f"Connected {success_count} players and started monitoring",
                style="bold green",
            )
        else:
            console.print("Error: No players registered successfully", style="red")

    def start_monitoring(self):
        """Start buzzer monitoring with live display"""
        if not self.game_api.connected:
            console.print(
                "Error: Not connected to server. Use 'connect' first.", style="red"
            )
            return

        console.print("Starting Buzzer Monitor", style="bold")
        console.print("Press Ctrl+C to stop monitoring")

        self.buzzer_monitor.start_monitoring()

        try:
            with console.status("Monitoring buzzers...", spinner="dots"):
                while True:
                    pass
        except KeyboardInterrupt:
            self.buzzer_monitor.stop_monitoring()
            console.print("\nMonitoring stopped", style="yellow")

    def mock_buzzer_press(self):
        """Simulate a buzzer press for testing"""
        players = self.player_manager.get_all_players()
        if not players:
            console.print("No players configured", style="yellow")
            return

        console.print("Mock Buzzer Press", style="bold")
        console.print("-" * 20)
        self.show_players()

        player_ids = list(players.keys())

        try:
            pid = Prompt.ask(
                "Player ID to simulate", choices=player_ids, show_choices=False
            )

            player_name = players[pid].name
            console.print(
                f"Simulating buzzer press for {player_name}...", style="yellow"
            )
            self.buzzer_monitor.mock_buzzer_press(pid)
            console.print("Mock press sent", style="green")

        except KeyboardInterrupt:
            console.print("Cancelled", style="yellow")

    def show_help(self):
        """Display detailed help information"""
        console.print("Buzzer System CLI Help", style="bold")
        console.print("=" * 50)
        console.print()

        console.print("Getting Started:", style="bold")
        console.print("1. Add players with the 'add' command")
        console.print("2. Connect to a game server with 'connect'")
        console.print("3. Start monitoring buzzers with 'monitor'")
        console.print()

        console.print("Commands:", style="bold")
        console.print("  status   - View system status and connection info")
        console.print("  list     - Show all configured players in a table")
        console.print("  add      - Add a new player (name + GPIO pin)")
        console.print("  remove   - Remove an existing player")
        console.print("  connect  - Connect to game server and register players")
        console.print("  monitor  - Start real-time buzzer monitoring")
        console.print("  mock     - Test by simulating a buzzer press")
        console.print("  help     - Show this help screen")
        console.print("  quit     - Exit the application")
        console.print()

        console.print("Tips:", style="bold")
        console.print("- Players must be added before connecting")
        console.print("- Only enabled players will be registered")
        console.print("- Use Ctrl+C to stop monitoring")
        console.print("- GPIO pins must be unique per player")

    def run(self):
        """Main application loop"""
        console.clear()
        self.show_header()

        console.print("Welcome to the Buzzer System CLI", style="bold green")
        console.print("Type commands below or 'help' for assistance.")
        console.print()

        while True:
            try:
                self.show_status()
                self.show_players()
                self.show_menu()

                cmd = Prompt.ask(
                    "Command",
                    choices=[
                        "status",
                        "list",
                        "add",
                        "remove",
                        "connect",
                        "monitor",
                        "mock",
                        "help",
                        "quit",
                    ],
                    show_choices=False,
                ).lower()

                console.print()

                if cmd == "status":
                    continue  # Status already shown
                elif cmd == "list":
                    self.show_players()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "add":
                    self.add_player()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "remove":
                    self.remove_player()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "connect":
                    self.connect_to_game()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "monitor":
                    self.start_monitoring()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "mock":
                    self.mock_buzzer_press()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "help":
                    self.show_help()
                    Prompt.ask("Press Enter to continue")
                elif cmd == "quit":
                    console.print("Goodbye", style="bold")
                    break

            except KeyboardInterrupt:
                console.print("\nGoodbye", style="bold")
                break
            except Exception as e:
                console.print(f"Error: {e}", style="red")
                Prompt.ask("Press Enter to continue")


def main():
    app = BuzzerCLI()
    app.run()


if __name__ == "__main__":
    main()
