import time
import random

class MockSensor:
    def __init__(self):
        self._temperature = 22.0
        self._humidity = 45.0

    @property
    def temperature(self):
        # simulate gradual temperature variation
        self._temperature += random.uniform(-0.1, 0.1)
        return self._temperature

    @property
    def relative_humidity(self):
        # simulate gradual humidity variation
        self._humidity += random.uniform(-0.2, 0.2)
        return max(0, min(100, self._humidity))

def get_sensor():
    """Return a simulated sensor instance."""
    return MockSensor()

if __name__ == "__main__":
    sensor = get_sensor()
    while True:
        print(f"Temperature: {sensor.temperature:.2f} °C")
        print(f"Humidity:    {sensor.relative_humidity:.2f} %")
        time.sleep(2)
