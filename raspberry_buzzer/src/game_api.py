import time
from collections.abc import Callable
from typing import Any

import requests
import socketio


class PlayerConnection:
    def __init__(
        self, server_url: str, player_id: str, game_id: str, game_api: "GameAPI"
    ):
        self.server_url: str = server_url
        self.player_id: str = player_id
        self.game_id: str = game_id
        self.game_api: GameAPI = game_api
        self.sio: socketio.Client = socketio.Client()
        self.connected: bool = False
        self._setup_socket_events()

    def _setup_socket_events(self):
        @self.sio.event
        def connect():
            self.connected = True
            print(f"✅ Player {self.player_id} connected to server")
            try:
                self.sio.emit(
                    "join_game", {"gameId": self.game_id, "playerId": self.player_id}
                )
            except Exception as e:
                print(f"Failed to join game room for player {self.player_id}: {e}")

        @self.sio.event
        def disconnect():
            self.connected = False

        @self.sio.event
        def error(data):
            pass

        @self.sio.event
        def game_update(data):
            """Handle game state updates including all state changes"""
            try:
                if "data" in data and "game" in data["data"]:
                    game_data = data["data"]["game"]

                    old_locked = self.game_api.buzzers_locked
                    old_active = self.game_api.is_active
                    old_countdown = self.game_api.countdown_active

                    self.game_api.buzzers_locked = game_data.get("buzzersLocked", False)
                    self.game_api.is_active = game_data.get("isActive", False)
                    self.game_api.countdown_active = game_data.get(
                        "countdownActive", False
                    )

                    if old_locked != self.game_api.buzzers_locked:
                        status = (
                            "LOCKED" if self.game_api.buzzers_locked else "UNLOCKED"
                        )
                        print(f"[GAME] Buzzers are now {status}")

                    if old_active != self.game_api.is_active:
                        status = "ACTIVE" if self.game_api.is_active else "INACTIVE"
                        print(f"[GAME] Game is now {status}")

                    if old_countdown != self.game_api.countdown_active:
                        status = (
                            "COUNTDOWN"
                            if self.game_api.countdown_active
                            else "NO COUNTDOWN"
                        )
                        print(f"[GAME] Countdown state: {status}")

                    if self.game_api.game_update_callback:
                        self.game_api.game_update_callback(data)
            except Exception as e:
                print(f"Error processing game update: {e}")

    def connect_to_server(self) -> bool:
        """Connect this player to the server"""
        try:
            print(f"Connecting player {self.player_id} to {self.server_url}")
            self.sio.connect(self.server_url, wait_timeout=5)
            return True
        except Exception as e:
            print(f"Failed to connect player {self.player_id}: {e}")
            return False

    def press_buzzer(self) -> bool:
        """Press buzzer for this specific player"""
        if not self.connected:
            print(f"Cannot press buzzer: player {self.player_id} not connected")
            return False

        try:
            self.sio.emit("press_buzzer")
            print(f"Buzzer pressed for player {self.player_id}")
            return True
        except Exception as e:
            print(f"Error pressing buzzer for player {self.player_id}: {e}")
            return False

    def disconnect_from_server(self):
        """Disconnect this player from the server"""
        if self.connected:
            try:
                self.sio.disconnect()
                print(f"✅ Player {self.player_id} disconnected cleanly")
            except Exception as e:
                print(f"❌ Error disconnecting player {self.player_id}: {e}")


class GameAPI:
    server_url: str
    game_id: str | None
    player_connections: dict[str, PlayerConnection]
    player_mappings: dict[str, str]
    game_update_callback: Callable[[dict[str, Any]], None] | None
    buzzers_locked: bool
    is_active: bool
    countdown_active: bool

    def __init__(self, server_url: str = "http://localhost:3001") -> None:
        self.server_url = server_url
        self.game_id = None
        self.player_connections = {}
        self.player_mappings = {}
        self.game_update_callback = None

        self.buzzers_locked = False
        self.is_active = False
        self.countdown_active = False

    @property
    def connected(self) -> bool:
        """Check if any players are connected"""
        return any(conn.connected for conn in self.player_connections.values())

    @property
    def buzzers_available(self) -> bool:
        """Check if buzzers are available for pressing (only during active round)"""
        return self.is_active and not self.buzzers_locked and not self.countdown_active

    def get_buzzer_status(self) -> str:
        """Get a human-readable buzzer status"""
        if not self.is_active:
            return "Waiting for round to start"
        elif self.countdown_active:
            return "Countdown in progress"
        elif self.buzzers_locked:
            return "Buzzers locked"
        else:
            return "Buzzers ready"

    def connect_to_server(self) -> bool:
        """This method is kept for compatibility but doesn't do anything"""
        return True

    def disconnect_from_server(self) -> None:
        """Disconnect all players from the game server"""
        for connection in self.player_connections.values():
            connection.disconnect_from_server()
        self.player_connections.clear()

    def join_game(self, game_code: str, player_name: str) -> dict[str, any] | None:
        """Join an existing game and return player info"""
        print(f"join_game called: code={game_code}, name={player_name}")

        try:
            print(f"Making API request to {self.server_url}/api/games/join")
            response = requests.post(
                f"{self.server_url}/api/games/join",
                json={"gameCode": game_code, "playerName": player_name},
            )

            print(f"📡 API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if not self.game_id:
                    self.game_id = data["game"]["id"]

                api_player_id = data["playerId"]

                return {
                    "playerId": api_player_id,
                    "playerName": player_name,
                    "game": data["game"],
                }
            else:
                error_msg = response.json().get("error", "Unknown error")
                print(f"API request failed: {error_msg}")
                return None

        except Exception as e:
            print(f"Exception in join_game for {player_name}: {e}")
            return None

    def press_buzzer(self, local_player_id: str) -> bool:
        """Press buzzer for a specific player using their local ID"""
        if not self.is_active or self.buzzers_locked or self.countdown_active:
            if self.countdown_active:
                print(f"[BUZZER] Press ignored: countdown in progress")
            elif not self.is_active:
                print(f"[BUZZER] Press ignored: round not active")
            elif self.buzzers_locked:
                print(f"[BUZZER] Press ignored: buzzers are locked")
            return False

        connection = self.player_connections.get(local_player_id)
        if not connection:
            print(f"No connection found for local player {local_player_id}")
            return False

        return connection.press_buzzer()

    def register_player_mapping(self, local_player_id: str, api_player_id: str) -> None:
        """Register a mapping between local player ID and API player ID"""

        self.player_mappings[local_player_id] = api_player_id
        print(f"Mapped local player {local_player_id} to API player {api_player_id}")

        if self.game_id:
            print(f"Game ID available: {self.game_id}")
            print(
                f"Creating socket connection for player {api_player_id} to {self.server_url}"
            )

            try:
                connection = PlayerConnection(
                    self.server_url, api_player_id, self.game_id, self
                )
                print(f"PlayerConnection object created for {api_player_id}")

                max_retries = 3
                for attempt in range(max_retries):
                    if connection.connect_to_server():
                        self.player_connections[local_player_id] = connection
                        return
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(1)

            except Exception as e:
                print(f"Error creating PlayerConnection for {api_player_id}: {e}")
        else:
            print("Cannot register player mapping: game ID is not set")

    def get_registered_players(self) -> dict[str, str]:
        """Get all registered player mappings"""
        return self.player_mappings.copy()

    def set_game_update_callback(
        self, callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """Set callback for game updates"""
        self.game_update_callback = callback

    def get_game_info(self) -> dict[str, Any] | None:
        """Get current game information"""
        if not self.game_id:
            return None

        try:
            response = requests.get(f"{self.server_url}/api/games/{self.game_id}")
            if response.status_code == 200:
                return response.json()["game"]
            return None
        except Exception as e:
            print(f"Error getting game info: {e}")
            return None
