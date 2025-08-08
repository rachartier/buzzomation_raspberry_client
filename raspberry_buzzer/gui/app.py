# pyright: basic

import uuid

import streamlit as st

from raspberry_buzzer.src.buzzer_monitor import BuzzerMonitor
from raspberry_buzzer.src.game_api import GameAPI
from raspberry_buzzer.src.gpio_handler import gpio_handler
from raspberry_buzzer.src.player_manager import PlayerManager

# Page configuration
st.set_page_config(page_title="Buzzer Configuration")

# Clean, flat design CSS
st.markdown(
    """
<style>
    /* Reset and base styles */
    .main-content {
        max - width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }

    /* Header */
    .header {
        background: #2563eb;
        color: white;
        padding: 1.5rem 2rem;
        margin: -1rem -2rem 2rem -2rem;
        border-bottom: 3px solid #1d4ed8;
    }

    .header h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 600;
        color: white;
    }

    .header p {
        margin: 0.25rem 0 0 0;
        opacity: 0.9;
        color: white;
    }

    /* Status bar */
    .status-bar {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: #475569;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .status-dot.green {
        background: #10b981;
    }

    .status-dot.red {
        background: #ef4444;
    }

    .status-dot.orange {
        background: #f59e0b;
    }

    /* Card design */
    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .card h3 {
        margin: 0 0 1rem 0;
        font-size: 1.125rem;
        font-weight: 600;
        color: #1e293b;
    }

    /* Form styles */
    .stForm {
        border: none !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input {
        border: 1px solid #d1d5db !important;
        border-radius: 4px !important;
        padding: 0.5rem 0.75rem !important;
    }

    .stSelectbox > div > div > div {
        border: 1px solid #d1d5db !important;
        border-radius: 4px !important;
    }

    /* Button styles */
    .stButton > button {
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: background-color 0.2s ease !important;
    }

    .stButton > button:hover {
        background: #1d4ed8 !important;
    }

    .btn-secondary > button {
        background: #6b7280 !important;
    }

    .btn-secondary > button:hover {
        background: #4b5563 !important;
    }

    .btn-danger > button {
        background: #dc2626 !important;
    }

    .btn-danger > button:hover {
        background: #b91c1c !important;
    }

    .btn-success > button {
        background: #059669 !important;
    }

    .btn-success > button:hover {
        background: #047857 !important;
    }

    /* Player list */
    .player-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .player-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .player-name {
        font - weight: 500;
        color: #1e293b;
    }

    .player-pin {
        font - size: 0.75rem;
        color: #64748b;
    }

    /* Development controls */
    .dev-controls {
        background: #fefce8;
        border: 1px solid #eab308;
        border-radius: 6px;
        padding: 1rem;
        margin-top: 1.5rem;
    }

    .dev-controls h4 {
        margin: 0 0 0.75rem 0;
        color: #92400e;
        font-size: 1rem;
    }

    .buzzer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 0.75rem;
        margin-top: 0.75rem;
    }

    /* Control bar */
    .control-bar {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e2e8f0;
    }

    /* Hide Streamlit elements */
    .stDeployButton {
        display: none;
    }

    header[data-testid="stHeader"] {
        display: none;
    }

    .stApp > div:first-child {
        margin - top: -80px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "player_manager" not in st.session_state:
    st.session_state.player_manager = PlayerManager()
if "game_api" not in st.session_state:
    st.session_state.game_api = GameAPI()
if "buzzer_monitor" not in st.session_state:
    st.session_state.buzzer_monitor = BuzzerMonitor(
        st.session_state.game_api, st.session_state.player_manager
    )

# Header
st.markdown(
    """
<div class="header">
    <h1>Buzzer Configuration</h1>
</div>
""",
    unsafe_allow_html=True,
)

# Status Overview with simple dots
players = st.session_state.player_manager.get_all_players()
server_connected = st.session_state.game_api.connected
game_connected = bool(st.session_state.game_api.game_id)
monitoring = st.session_state.buzzer_monitor.monitoring
buzzers_available = st.session_state.game_api.buzzers_available
buzzer_status = st.session_state.game_api.get_buzzer_status()

# Clean status without emojis
server_dot = "green" if server_connected else "red"
game_dot = "green" if game_connected else "red"
monitor_dot = "green" if monitoring else "red"
buzzer_dot = "green" if buzzers_available else ("orange" if game_connected else "red")

st.markdown(
    f"""
<div class="status-bar">
    <div class="status-item">
        <div class="status-dot {server_dot}"></div>
        <span>Server: {"Connected" if server_connected else "Disconnected"}</span>
    </div>
    <div class="status-item">
        <div class="status-dot {game_dot}"></div>
        <span>Game: {"Connected" if game_connected else "Not Connected"}</span>
    </div>
    <div class="status-item">
        <div class="status-dot {monitor_dot}"></div>
        <span>Monitoring: {"Active" if monitoring else "Stopped"}</span>
    </div>
    <div class="status-item">
        <div class="status-dot {buzzer_dot}"></div>
        <span>Buzzers: {buzzer_status}</span>
    </div>
    <div class="status-item">
        <span>Players: {len(players)} configured</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Game Connection Section (First Priority)
st.divider()
st.markdown("<h3>Game Connection</h3>", unsafe_allow_html=True)

with st.form("game_connection"):
    server_url = st.text_input("Server URL", value="http://localhost:3001")
    game_code = st.text_input("Game Code", placeholder="Enter 6-digit code")

    connect_submitted = st.form_submit_button("Connect All Players")

    if connect_submitted and server_url and game_code and len(players) > 0:
        # Connect to server
        st.session_state.game_api.server_url = server_url
        print(f"Starting connection process with {len(players)} players")

        if st.session_state.game_api.connect_to_server():
            print("Main connection successful, registering players...")
            # Register all players
            success_count = 0
            for player_id, config in players.items():
                print(f"Registering player {config.name} (local ID: {player_id})")
                result = st.session_state.game_api.join_game(game_code, config.name)
                if result:
                    print(
                        f"API registration successful for {config.name}, creating socket connection..."
                    )
                    st.session_state.game_api.register_player_mapping(
                        player_id, result["playerId"]
                    )
                    success_count += 1
                else:
                    print(f"API registration failed for {config.name}")
                    st.error(f"Failed to register {config.name}")

            if success_count > 0:
                print("Starting buzzer monitoring...")
                st.session_state.buzzer_monitor.start_monitoring()
                st.success(f"Connected {success_count} players successfully")
            else:
                st.error("Failed to register any players")
        else:
            print("Main connection failed")
            st.error("Failed to connect to server")

if len(players) == 0:
    st.info("Add players below to enable connection")

st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.markdown("<h3>Players</h3>", unsafe_allow_html=True)

# Add player form
with st.form("add_player"):
    col1, col2 = st.columns([2, 1])
    with col1:
        player_name = st.text_input("Player Name", placeholder="Enter name")
    with col2:
        available_pins = st.session_state.player_manager.get_available_gpio_pins()
        if available_pins:
            gpio_pin = st.selectbox("GPIO Pin", available_pins)
        else:
            st.warning("No GPIO pins available")
            gpio_pin = None

    submitted = st.form_submit_button("Add Player")

    if submitted and player_name and gpio_pin:
        player_id = str(uuid.uuid4())[:8]
        if st.session_state.player_manager.add_player(player_id, player_name, gpio_pin):
            st.success(f"Added {player_name}")
            st.rerun()
        else:
            st.error("Failed to add player")

# Current players list
if players:
    for player_id, config in players.items():
        st.markdown(
            f"""
        <div class="player-item">
            <div class="player-info">
                <div class="player-name">{config.name}</div>
                <div class="player-pin">GPIO: {config.gpio_pin}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Remove", key=f"remove_{player_id}", help=f"Remove {config.name}"):
            st.session_state.player_manager.remove_player(player_id)
            st.rerun()
else:
    st.info("No players configured yet")

st.markdown("</div>", unsafe_allow_html=True)

# Development Controls (if in mock mode)
if gpio_handler.mock_mode and len(players) > 0:
    st.markdown(
        """
    <div class="dev-controls">
        <h4>Development Mode - Test Buzzers</h4>
        <p>Use these buttons to simulate buzzer presses</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="buzzer-grid">', unsafe_allow_html=True)

    # Create buzzer test buttons in a grid
    cols = st.columns(min(len(players), 4))
    for idx, (player_id, config) in enumerate(players.items()):
        with cols[idx % 4]:
            button_key = f"test_buzzer_{player_id}_{config.gpio_pin}"
            if st.button(
                f"Test {config.name}",
                key=button_key,
                help=f"Test buzzer for {config.name}",
            ):
                st.session_state.buzzer_monitor.mock_buzzer_press(player_id)
                st.success(f"Buzzer pressed: {config.name}")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Control buttons
if len(players) > 0:
    st.markdown('<div class="control-bar">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Refresh Status"):
            st.rerun()

    with col2:
        if monitoring:
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button("Stop Monitoring"):
                st.session_state.buzzer_monitor.stop_monitoring()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        if server_connected:
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button("Disconnect"):
                st.session_state.game_api.disconnect_from_server()
                st.session_state.buzzer_monitor.stop_monitoring()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        if server_connected and game_connected:
            st.markdown('<div class="btn-success">', unsafe_allow_html=True)
            if st.button("Clear Buzzers"):
                # Send clear buzzer command to server using any connected player
                connections = list(
                    st.session_state.game_api.player_connections.values()
                )
                if connections:
                    try:
                        # Use the first available connection to send the clear command
                        connections[0].sio.emit(
                            "game_action", {"type": "clear_buzzers", "data": {}}
                        )
                        st.success("Buzzers cleared")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to clear buzzers: {e}")
                else:
                    st.error("No player connections available")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Entry point for the GUI application"""
    pass  # Streamlit app runs automatically when the module is executed


if __name__ == "__main__":
    main()
