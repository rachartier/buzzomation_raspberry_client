import sys
import uuid
import os

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.buzzer_monitor import BuzzerMonitor
from src.game_api import GameAPI
from src.player_manager import PlayerManager

player_manager = PlayerManager()
game_api = GameAPI()
buzzer_monitor = BuzzerMonitor(game_api, player_manager)


def print_status():
    players = player_manager.get_all_players()
    print(f"Players: {len(players)} configured")
    print(f"Server connected: {game_api.connected}")
    print(f"Game ID: {game_api.game_id}")
    print(f"Buzzers available: {game_api.buzzers_available}")
    print(f"Monitoring: {buzzer_monitor.monitoring}")


def list_players():
    players = player_manager.get_all_players()
    if not players:
        print("No players configured.")
        return
    for pid, config in players.items():
        print(
            f"{pid}: {config.name} (GPIO {config.gpio_pin}){' [ENABLED]' if config.enabled else ''}"
        )


def add_player():
    name = input("Player name: ").strip()
    pins = player_manager.get_available_gpio_pins()
    if not pins:
        print("No GPIO pins available.")
        return
    print(f"Available GPIO pins: {pins}")
    try:
        pin = int(input("GPIO pin: ").strip())
    except Exception:
        print("Invalid pin.")
        return
    if pin not in pins:
        print("Pin not available.")
        return
    pid = str(uuid.uuid4())[:8]
    if player_manager.add_player(pid, name, pin):
        print(f"Added player {name} on pin {pin}.")
    else:
        print("Failed to add player.")


def remove_player():
    list_players()
    pid = input("Player ID to remove: ").strip()
    if player_manager.remove_player(pid):
        print("Player removed.")
    else:
        print("Player not found.")


def connect():
    url = input(f"Server URL [{game_api.server_url}]: ").strip() or game_api.server_url
    code = input("Game code: ").strip()
    players = player_manager.get_all_players()
    if not players:
        print("No players configured.")
        return
    game_api.server_url = url
    if not game_api.connect_to_server():
        print("Failed to connect to server.")
        return
    success = 0
    for pid, config in players.items():
        result = game_api.join_game(code, config.name)
        if result:
            game_api.register_player_mapping(pid, result["playerId"])
            success += 1
        else:
            print(f"Failed to register {config.name}")
    if success:
        buzzer_monitor.start_monitoring()
        print(f"Connected {success} players and started monitoring.")
    else:
        print("No players registered.")


def monitor():
    buzzer_monitor.start_monitoring()
    print("Monitoring started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        buzzer_monitor.stop_monitoring()
        print("Monitoring stopped.")


def mock_press():
    list_players()
    pid = input("Player ID to mock press: ").strip()
    buzzer_monitor.mock_buzzer_press(pid)


def help():
    print("Commands:")
    print("  status         Show status")
    print("  list           List players")
    print("  add            Add player")
    print("  remove         Remove player")
    print("  connect        Connect to server/game")
    print("  monitor        Start monitoring buzzers")
    print("  mock           Simulate buzzer press (dev mode)")
    print("  quit           Exit")


def main():
    print("Simple Buzzer CLI. Type 'help' for commands.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == "status":
            print_status()
        elif cmd == "list":
            list_players()
        elif cmd == "add":
            add_player()
        elif cmd == "remove":
            remove_player()
        elif cmd == "connect":
            connect()
        elif cmd == "monitor":
            monitor()
        elif cmd == "mock":
            mock_press()
        elif cmd == "help":
            help()
        elif cmd == "quit":
            break
        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
