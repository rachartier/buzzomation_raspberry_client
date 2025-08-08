from collections.abc import Callable

try:
    import RPi.GPIO as GPIO

    MOCK_MODE = False
except ImportError:
    GPIO = None
    MOCK_MODE = True
    print("⚠️  RPi.GPIO not available - running in mock mode")


class GPIOHandler:
    def __init__(self) -> None:
        self.mock_mode = MOCK_MODE
        self.callbacks: dict[int, Callable[[int], None]] = {}
        self.mock_states: dict[int, bool] = {}

        if GPIO is not None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

    def setup_button(self, pin: int, callback: Callable[[int], None]) -> None:
        """Setup a button on the specified GPIO pin with a callback function"""
        if self.mock_mode:
            self.mock_states[pin] = False
            self.callbacks[pin] = callback
            print(f"Mock: Button setup on pin {pin}")
        elif GPIO is not None:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin, GPIO.FALLING, callback=lambda pin: callback(pin), bouncetime=300
            )

    def cleanup(self) -> None:
        """Cleanup GPIO resources"""
        if GPIO is not None:
            GPIO.cleanup()

    def mock_button_press(self, pin: int) -> None:
        """Mock a button press for testing purposes"""
        if self.mock_mode and pin in self.callbacks:
            print(f"Mock: Button {pin} pressed!")
            self.callbacks[pin](pin)
        elif GPIO is not None:
            print("Mock button press only available in mock mode")


gpio_handler = GPIOHandler()
