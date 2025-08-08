import uuid

from rich.align import Align
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
        console.print("Raspberry Pi Buzzer Control", style="dim")
        console.print()

    def show_status_and_players(self):
        """Display system status and players in a compact view"""
        players = self.player_manager.get_all_players()
        enabled_players = sum(1 for p in players.values() if p.enabled)

        # Status line
        status_parts = []
        if self.game_api.connected:
            status_parts.append("[green]Connected[/green]")
        else:
            status_parts.append("[red]Disconnected[/red]")
        
        if self.buzzer_monitor.monitoring:
            status_parts.append("[green]Monitoring[/green]")
        else:
            status_parts.append("[dim]Stopped[/dim]")
        
        status_parts.append(f"{enabled_players}/{len(players)} players")
        
        console.print(f"Status: {' • '.join(status_parts)}")

        # Players table (only if players exist)
        if players:
            console.print()
            table = Table(show_header=True, header_style="dim")
            table.add_column("ID", width=8, style="dim")
            table.add_column("Name", width=15)
            table.add_column("GPIO", width=5, justify="center")
            table.add_column("Status", width=8)

            for pid, config in players.items():
                status = "[green]On[/green]" if config.enabled else "[dim]Off[/dim]"
                table.add_row(pid[:8], config.name, str(config.gpio_pin), status)

            console.print(table)

        console.print()

    def show_players(self):
        """Display all configured players - simplified version"""
        players = self.player_manager.get_all_players()

        if not players:
            console.print("[dim]No players configured[/dim]")
            console.print()
            return

        table = Table(show_header=True, header_style="dim")
        table.add_column("ID", width=8, style="dim")
        table.add_column("Name", width=15)
        table.add_column("GPIO", width=5, justify="center")
        table.add_column("Status", width=8)

        for pid, config in players.items():
            status = "[green]On[/green]" if config.enabled else "[dim]Off[/dim]"
            table.add_row(pid[:8], config.name, str(config.gpio_pin), status)

        console.print(table)
        console.print()

    def show_menu(self):
        """Display the main menu options"""
        commands = ["add", "remove", "connect", "monitor", "mock", "help", "quit"]
        console.print("Commands:")
        for cmd in commands:
            console.print(f"  • {cmd}")
        console.print()

    def add_player(self):
        """Add a new player with Rich prompts"""
        console.print("[bold]Add Player[/bold]")

        name = Prompt.ask("Name")
        if not name.strip():
            console.print("[red]Invalid name[/red]")
            return

        pins = self.player_manager.get_available_gpio_pins()
        if not pins:
            console.print("[red]No GPIO pins available[/red]")
            return

        console.print(f"Available pins: {', '.join(map(str, pins))}")

        try:
            pin = IntPrompt.ask("GPIO pin", choices=[str(p) for p in pins], show_choices=False)
        except KeyboardInterrupt:
            console.print("[yellow]Cancelled[/yellow]")
            return

        pid = str(uuid.uuid4())[:8]
        if self.player_manager.add_player(pid, name.strip(), pin):
            console.print(f"[green]Added {name} on pin {pin}[/green]")
        else:
            console.print("[red]Failed to add player[/red]")

    def remove_player(self):
        """Remove a player with confirmation"""
        players = self.player_manager.get_all_players()
        if not players:
            console.print("[yellow]No players to remove[/yellow]")
            return

        console.print("[bold]Remove Player[/bold]")
        self.show_players()

        player_ids = list(players.keys())

        try:
            pid = Prompt.ask("Player ID", choices=player_ids, show_choices=False)
            player_name = players[pid].name
            
            if Confirm.ask(f"Remove {player_name}?"):
                if self.player_manager.remove_player(pid):
                    console.print(f"[green]Removed {player_name}[/green]")
                else:
                    console.print("[red]Failed to remove player[/red]")
            else:
                console.print("[yellow]Cancelled[/yellow]")

        except KeyboardInterrupt:
            console.print("[yellow]Cancelled[/yellow]")

    def connect_to_game(self):
        """Connect to server and join game"""
        console.print("[bold]Connect to Game[/bold]")

        players = self.player_manager.get_all_players()
        if not players:
            console.print("[red]No players configured[/red]")
            return

        try:
            url = Prompt.ask("Server URL", default=self.game_api.server_url)
            code = Prompt.ask("Game code")
            if not code.strip():
                console.print("[red]Game code required[/red]")
                return
        except KeyboardInterrupt:
            console.print("[yellow]Cancelled[/yellow]")
            return

        console.print("Connecting...")
        self.game_api.server_url = url
        if not self.game_api.connect_to_server():
            console.print("[red]Connection failed[/red]")
            return

        console.print("[green]Connected[/green] - registering players...")
        
        success_count = 0
        for pid, config in players.items():
            if not config.enabled:
                continue

            result = self.game_api.join_game(code.strip(), config.name)
            if result:
                self.game_api.register_player_mapping(pid, result["playerId"])
                success_count += 1
                console.print(f"  [green]✓[/green] {config.name}")
            else:
                console.print(f"  [red]✗[/red] {config.name}")

        if success_count > 0:
            self.buzzer_monitor.start_monitoring()
            console.print(f"[green]Ready! {success_count} players registered[/green]")
        else:
            console.print("[red]No players registered[/red]")

    def start_monitoring(self):
        """Start buzzer monitoring with live display"""
        if not self.game_api.connected:
            console.print("[red]Not connected - use 'connect' first[/red]")
            return

        console.print("[green]Monitoring active[/green] - Press Ctrl+C to stop")
        self.buzzer_monitor.start_monitoring()

        try:
            with console.status("Waiting for buzzer presses...", spinner="dots"):
                while True:
                    pass
        except KeyboardInterrupt:
            self.buzzer_monitor.stop_monitoring()
            console.print("\n[yellow]Monitoring stopped[/yellow]")

    def mock_buzzer_press(self):
        """Simulate a buzzer press for testing"""
        players = self.player_manager.get_all_players()
        if not players:
            console.print("[yellow]No players configured[/yellow]")
            return

        console.print("[bold]Mock Buzzer Press[/bold]")
        self.show_players()

        player_ids = list(players.keys())

        try:
            pid = Prompt.ask("Player ID", choices=player_ids, show_choices=False)
            player_name = players[pid].name
            
            console.print(f"Simulating press for {player_name}...")
            self.buzzer_monitor.mock_buzzer_press(pid)
            console.print("[green]Mock press sent[/green]")

        except KeyboardInterrupt:
            console.print("[yellow]Cancelled[/yellow]")

    def show_help(self):
        """Display detailed help information"""
        console.print("[bold]Buzzer System CLI Help[/bold]")
        console.print()
        console.print("[dim]Getting Started:[/dim]")
        console.print("1. Add players with 'add'")
        console.print("2. Connect to game with 'connect'")
        console.print("3. Start monitoring with 'monitor'")
        console.print()
        console.print("[dim]Commands:[/dim]")
        console.print("add      - Add new player")
        console.print("remove   - Remove player")
        console.print("connect  - Connect to game server")
        console.print("monitor  - Start buzzer monitoring")
        console.print("mock     - Simulate buzzer press")
        console.print("help     - Show this help")
        console.print("quit     - Exit")
        console.print()
        console.print("[dim]Tips:[/dim]")
        console.print("- Players must be added before connecting")
        console.print("- Use Ctrl+C to stop monitoring")
        console.print("- GPIO pins must be unique")

    def run(self):
        """Main application loop"""
        console.clear()
        self.show_header()

        while True:
            try:
                self.show_status_and_players()
                self.show_menu()

                cmd = Prompt.ask(
                    "Command",
                    choices=["add", "remove", "connect", "monitor", "mock", "help", "quit"],
                    show_choices=False,
                ).lower()

                console.print()

                if cmd == "add":
                    self.add_player()
                elif cmd == "remove":
                    self.remove_player()
                elif cmd == "connect":
                    self.connect_to_game()
                elif cmd == "monitor":
                    self.start_monitoring()
                elif cmd == "mock":
                    self.mock_buzzer_press()
                elif cmd == "help":
                    self.show_help()
                elif cmd == "quit":
                    console.print("[blue]Goodbye![/blue]")
                    break

                if cmd != "quit":
                    console.print()
                    Prompt.ask("[dim]Press Enter to continue[/dim]")
                    console.clear()
                    self.show_header()

            except KeyboardInterrupt:
                console.print("\n[blue]Goodbye![/blue]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                Prompt.ask("[dim]Press Enter to continue[/dim]")


def main():
    app = BuzzerCLI()
    app.run()


if __name__ == "__main__":
    main()
