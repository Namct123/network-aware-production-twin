from __future__ import annotations

import pytest

from factoryio_mcp.modbus_gateway import (
    FactoryIOError,
    ModbusGateway,
    ModbusSettings,
)


class FakeResponse:
    def __init__(self, *, bits=None, registers=None, error=False):
        self.bits = bits or []
        self.registers = registers or []
        self._error = error

    def isError(self):
        return self._error


class FakeClient:
    def __init__(self, *args, connected=True, **kwargs):
        self.connected = connected
        self.closed = False
        self.calls = []

    def connect(self):
        return self.connected

    def close(self):
        self.closed = True

    def read_coils(self, address, *, count, device_id):
        self.calls.append(("read_coils", address, count, device_id))
        return FakeResponse(bits=[True, False, True, False, False, False, False, False])

    def read_discrete_inputs(self, address, *, count, device_id):
        return FakeResponse(bits=[False] * count)

    def read_holding_registers(self, address, *, count, device_id):
        return FakeResponse(registers=list(range(address, address + count)))

    def read_input_registers(self, address, *, count, device_id):
        return FakeResponse(registers=[100] * count)

    def write_coil(self, address, value, *, device_id):
        self.calls.append(("write_coil", address, value, device_id))
        return FakeResponse()

    def write_register(self, address, value, *, device_id):
        self.calls.append(("write_register", address, value, device_id))
        return FakeResponse()


def make_gateway(client):
    return ModbusGateway(
        ModbusSettings(host="127.0.0.1", port=502, device_id=1),
        client_factory=lambda **kwargs: client,
    )


def test_status_reports_connection():
    client = FakeClient()
    status = make_gateway(client).status()
    assert status == {
        "connected": True,
        "host": "127.0.0.1",
        "port": 502,
        "device_id": 1,
    }
    assert client.closed


def test_read_bits_trims_protocol_padding():
    client = FakeClient()
    values = make_gateway(client).read_bits("coils", 5, 3)
    assert values == [True, False, True]
    assert client.calls == [("read_coils", 5, 3, 1)]


def test_read_registers():
    values = make_gateway(FakeClient()).read_registers("holding_registers", 10, 3)
    assert values == [10, 11, 12]


def test_write_values():
    client = FakeClient()
    gateway = make_gateway(client)
    assert gateway.write_coil(2, True) == {"address": 2, "value": True}
    assert gateway.write_holding_register(3, 1200) == {
        "address": 3,
        "value": 1200,
    }


def test_rejects_invalid_ranges_and_values():
    gateway = make_gateway(FakeClient())
    with pytest.raises(ValueError):
        gateway.read_bits("coils", -1, 1)
    with pytest.raises(ValueError):
        gateway.read_registers("holding_registers", 0, 65)
    with pytest.raises(ValueError):
        gateway.write_holding_register(0, 65536)


def test_connection_failure_is_actionable():
    gateway = make_gateway(FakeClient(connected=False))
    with pytest.raises(FactoryIOError, match="Start the Modbus TCP/IP Server"):
        gateway.read_bits("coils", 0, 1)

