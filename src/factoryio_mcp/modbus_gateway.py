"""Small, testable Modbus TCP gateway for Factory I/O."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pymodbus.client import ModbusTcpClient


class FactoryIOError(RuntimeError):
    """Raised when Factory I/O cannot complete a Modbus operation."""


@dataclass(frozen=True)
class ModbusSettings:
    host: str = "127.0.0.1"
    port: int = 502
    device_id: int = 1
    timeout: float = 2.0

    def __post_init__(self) -> None:
        if not self.host:
            raise ValueError("host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if not 0 <= self.device_id <= 247:
            raise ValueError("device_id must be between 0 and 247")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")


class ModbusGateway:
    """Open one short-lived Modbus connection for each MCP operation."""

    def __init__(
        self,
        settings: ModbusSettings,
        client_factory: Callable[..., Any] = ModbusTcpClient,
    ) -> None:
        self.settings = settings
        self._client_factory = client_factory

    def _client(self) -> Any:
        return self._client_factory(
            host=self.settings.host,
            port=self.settings.port,
            timeout=self.settings.timeout,
        )

    @staticmethod
    def _validate_range(address: int, count: int, maximum_count: int) -> None:
        if not 0 <= address <= 65535:
            raise ValueError("address must be between 0 and 65535")
        if not 1 <= count <= maximum_count:
            raise ValueError(f"count must be between 1 and {maximum_count}")
        if address + count > 65536:
            raise ValueError("address range exceeds 65535")

    @staticmethod
    def _check_response(response: Any, operation: str) -> Any:
        if response is None:
            raise FactoryIOError(f"{operation} returned no response")
        if response.isError():
            raise FactoryIOError(f"{operation} failed: {response}")
        return response

    def status(self) -> dict[str, Any]:
        client = self._client()
        try:
            connected = bool(client.connect())
            return {
                "connected": connected,
                "host": self.settings.host,
                "port": self.settings.port,
                "device_id": self.settings.device_id,
            }
        except OSError as exc:
            return {
                "connected": False,
                "host": self.settings.host,
                "port": self.settings.port,
                "device_id": self.settings.device_id,
                "error": str(exc),
            }
        finally:
            client.close()

    def _execute(self, operation: str, callback: Callable[[Any], Any]) -> Any:
        client = self._client()
        try:
            if not client.connect():
                raise FactoryIOError(
                    f"Cannot connect to Factory I/O at "
                    f"{self.settings.host}:{self.settings.port}. "
                    "Start the Modbus TCP/IP Server driver in Factory I/O."
                )
            return self._check_response(callback(client), operation)
        except FactoryIOError:
            raise
        except (OSError, ConnectionError, TimeoutError) as exc:
            raise FactoryIOError(f"{operation} failed: {exc}") from exc
        finally:
            client.close()

    def read_bits(self, area: str, address: int, count: int) -> list[bool]:
        self._validate_range(address, count, 256)
        readers = {
            "coils": lambda client: client.read_coils(
                address, count=count, device_id=self.settings.device_id
            ),
            "discrete_inputs": lambda client: client.read_discrete_inputs(
                address, count=count, device_id=self.settings.device_id
            ),
        }
        if area not in readers:
            raise ValueError("area must be 'coils' or 'discrete_inputs'")
        response = self._execute(f"read {area}", readers[area])
        return [bool(value) for value in response.bits[:count]]

    def read_registers(self, area: str, address: int, count: int) -> list[int]:
        self._validate_range(address, count, 64)
        readers = {
            "holding_registers": lambda client: client.read_holding_registers(
                address, count=count, device_id=self.settings.device_id
            ),
            "input_registers": lambda client: client.read_input_registers(
                address, count=count, device_id=self.settings.device_id
            ),
        }
        if area not in readers:
            raise ValueError(
                "area must be 'holding_registers' or 'input_registers'"
            )
        response = self._execute(f"read {area}", readers[area])
        return [int(value) for value in response.registers[:count]]

    def write_coil(self, address: int, value: bool) -> dict[str, Any]:
        self._validate_range(address, 1, 1)
        self._execute(
            "write coil",
            lambda client: client.write_coil(
                address, bool(value), device_id=self.settings.device_id
            ),
        )
        return {"address": address, "value": bool(value)}

    def write_holding_register(self, address: int, value: int) -> dict[str, Any]:
        self._validate_range(address, 1, 1)
        if not 0 <= value <= 65535:
            raise ValueError("value must be between 0 and 65535")
        self._execute(
            "write holding register",
            lambda client: client.write_register(
                address, value, device_id=self.settings.device_id
            ),
        )
        return {"address": address, "value": value}

