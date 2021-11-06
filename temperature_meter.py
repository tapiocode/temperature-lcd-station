# Copyright (c) 2021 tapiocode
# https://github.com/tapiocode
# MIT License

from machine import Pin
import onewire, ds18x20, time

class temperature_meter:

    def __init__(self, pin: int):
        self._pin = pin
        self._sensor: ds18x20.DS18X20
        self._roms: list[object]
        self._initialized = False
        self._started_at: int
        self._cur = 0.0
        self._max = -1000.0
        self._min = 1000.0

        self.init_sensor()
        self.reset_elapsed_time()

    def is_initialized(self) -> bool:
        return self._initialized

    def init_sensor(self) -> None:
        self._sensor = ds18x20.DS18X20(onewire.OneWire(Pin(self._pin)))
        self._roms = self._sensor.scan()

    def read_temperature(self) -> float | bool:
        try:
            self._sensor.convert_temp()
            if self._roms and self._roms[0]:
                temp = self._sensor.read_temp(self._roms[0])
            else:
                raise onewire.OneWireError

            # Discard initial read since it often contains value 85.0
            if self._initialized == False:
                self._initialized = True
                return self.read_temperature()
            self._cur = temp
            self._max = max(temp, self._max)
            self._min = min(temp, self._min)
            self._initialized = True
            return temp
        except onewire.OneWireError:
            return False

    def get_temps(self) -> tuple[float, float, float]:
        return (self._cur, self._min, self._max)

    def reset(self) -> None:
        self.reset_elapsed_time()
        self._max = self._cur
        self._min = self._cur

    def reset_elapsed_time(self) -> None:
        self._started_at = time.time()

    def get_elapsed_time(self) -> int:
        return time.time() - self._started_at
