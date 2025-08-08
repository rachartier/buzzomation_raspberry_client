import time

from .game_api import GameAPI
from .gpio_handler import gpio_handler
from .player_manager import PlayerManager


class BuzzerMonitor:
    game_api: GameAPI
    player_manager: PlayerManager
    monitoring: bool
    last_buzzer_times: dict[str, float]
    pin_to_player_map: dict[int, str]

    def __init__(self, game_api: GameAPI, player_manager: PlayerManager):
        self.game_api = game_api
        self.player_manager = player_manager
        self.monitoring = False
        self.last_buzzer_times = {}
        self.pin_to_player_map = {}

    def start_monitoring(self):
        """Start monitoring buzzers"""
        if self.monitoring:
            return

        self.monitoring = True
        players = self.player_manager.get_enabled_players()

        self.pin_to_player_map = {}

        for player_id, config in players.items():
            self.pin_to_player_map[config.gpio_pin] = player_id

            def create_pin_callback(pin_number):
                def pin_callback(triggered_pin):
                    mapped_player_id = self.pin_to_player_map.get(triggered_pin)
                    if mapped_player_id:
                        self._handle_buzzer(mapped_player_id)
                    else:
                        print(f"Warning: No player mapped to GPIO pin {triggered_pin}")

                return pin_callback

            callback = create_pin_callback(config.gpio_pin)
            gpio_handler.setup_button(config.gpio_pin, callback)
            print(
                f"Monitoring {config.name} on GPIO {config.gpio_pin} -> Player ID {player_id}"
            )

    def stop_monitoring(self):
        """Stop monitoring buzzers"""
        self.monitoring = False
        self.pin_to_player_map = {}
        gpio_handler.cleanup()
        print("Stopped monitoring")

    def _handle_buzzer(self, player_id: str):
        """Handle buzzer press"""
        now = time.time()

        if player_id in self.last_buzzer_times and now - self.last_buzzer_times[player_id] < 0.5:
            return

        self.last_buzzer_times[player_id] = now

        players = self.player_manager.get_all_players()
        player_config = players.get(player_id)
        player_name = player_config.name if player_config else "Unknown"

        if self.game_api.connected:
            success = self.game_api.press_buzzer(player_id)
            if success:
                print(f"[BUZZER] Pressed: {player_name} (ID: {player_id})")
            else:
                pass
        else:
            print(f"[BUZZER] Pressed by {player_name} but not connected to game")

    def mock_buzzer_press(self, player_id: str):
        """Test buzzer press for a specific player"""
        print(f"Mock buzzer press for player ID: {player_id}")

        players = self.player_manager.get_all_players()
        player_config = players.get(player_id)

        if not player_config:
            print(f"Error: Player {player_id} not found")
            return

        gpio_handler.mock_button_press(player_config.gpio_pin)
