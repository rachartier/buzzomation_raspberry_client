import json
import os
from typing import NamedTuple


class PlayerConfig(NamedTuple):
    name: str
    gpio_pin: int
    enabled: bool = True


class PlayerManager:
    def __init__(self, config_file: str = "player_config.json") -> None:
        self.config_file: str = config_file
        self.players: dict[str, PlayerConfig] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load player configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    self.players = {
                        player_id: PlayerConfig(**config)
                        for player_id, config in data.items()
                    }
            except Exception as e:
                print(f"Error loading config: {e}")
                self.players = {}
        else:
            self.players = {}

    def save_config(self) -> None:
        """Save player configuration to JSON file"""
        try:
            data = {
                player_id: config._asdict()
                for player_id, config in self.players.items()
            }
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def add_player(self, player_id: str, name: str, gpio_pin: int) -> bool:
        """Add a new player configuration"""
        if self.is_gpio_pin_used(gpio_pin, exclude_player=player_id):
            return False

        self.players[player_id] = PlayerConfig(name=name, gpio_pin=gpio_pin)
        self.save_config()
        return True

    def remove_player(self, player_id: str) -> bool:
        """Remove a player configuration"""
        if player_id in self.players:
            del self.players[player_id]
            self.save_config()
            return True
        return False

    def update_player(
        self,
        player_id: str,
        name: str | None = None,
        gpio_pin: int | None = None,
        enabled: bool | None = None,
    ) -> bool:
        """Update player configuration"""
        if player_id not in self.players:
            return False

        current = self.players[player_id]

        if gpio_pin is not None and gpio_pin != current.gpio_pin:
            if self.is_gpio_pin_used(gpio_pin, exclude_player=player_id):
                return False

        self.players[player_id] = PlayerConfig(
            name=name if name is not None else current.name,
            gpio_pin=gpio_pin if gpio_pin is not None else current.gpio_pin,
            enabled=enabled if enabled is not None else current.enabled,
        )
        self.save_config()
        return True

    def get_player(self, player_id: str) -> PlayerConfig | None:
        """Get player configuration"""
        return self.players.get(player_id)

    def get_all_players(self) -> dict[str, PlayerConfig]:
        """Get all player configurations"""
        return self.players.copy()

    def get_enabled_players(self) -> dict[str, PlayerConfig]:
        """Get only enabled player configurations"""
        return {
            player_id: config
            for player_id, config in self.players.items()
            if config.enabled
        }

    def is_gpio_pin_used(
        self, gpio_pin: int, exclude_player: str | None = None
    ) -> bool:
        """Check if a GPIO pin is already in use"""
        return any(
            player_id != exclude_player and config.gpio_pin == gpio_pin
            for player_id, config in self.players.items()
        )

    def get_available_gpio_pins(self) -> list[int]:
        """Get list of commonly used GPIO pins that are available"""
        common_pins = [
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
        ]
        used_pins = {config.gpio_pin for config in self.players.values()}
        return [pin for pin in common_pins if pin not in used_pins]
