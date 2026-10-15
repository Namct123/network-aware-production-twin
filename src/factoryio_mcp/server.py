"""MCP tools for a local Factory I/O Modbus TCP Server driver."""

from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from factoryio_mcp.modbus_gateway import ModbusGateway, ModbusSettings


def _settings_from_environment() -> ModbusSettings:
    return ModbusSettings(
        host=os.getenv("FACTORYIO_HOST", "127.0.0.1"),
        port=int(os.getenv("FACTORYIO_PORT", "502")),
        device_id=int(os.getenv("FACTORYIO_DEVICE_ID", "1")),
        timeout=float(os.getenv("FACTORYIO_TIMEOUT", "2.0")),
    )


gateway = ModbusGateway(_settings_from_environment())
mcp = FastMCP(
    "factoryio",
    instructions=(
        "Use these tools only with the local Factory I/O simulation. "
        "Read connection status before other operations. Sensor/actuator addresses "
        "must match the mapping shown in Factory I/O's Modbus TCP/IP Server driver. "
        "Explain the intended simulated action before calling a write tool."
    ),
)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
WRITE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def factoryio_status() -> dict[str, Any]:
    """Check whether the local Factory I/O Modbus TCP server is reachable."""
    return gateway.status()


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def read_digital(
    area: Literal["coils", "discrete_inputs"],
    address: int = 0,
    count: int = 8,
) -> dict[str, Any]:
    """Read digital values from coils or discrete inputs (zero-based addresses)."""
    values = gateway.read_bits(area, address, count)
    return {
        "area": area,
        "start_address": address,
        "values": [
            {"address": address + offset, "value": value}
            for offset, value in enumerate(values)
        ],
    }


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def read_analog(
    area: Literal["holding_registers", "input_registers"],
    address: int = 0,
    count: int = 4,
    scale: float = 1.0,
) -> dict[str, Any]:
    """Read 16-bit registers and optionally divide raw values by a positive scale."""
    if scale <= 0:
        raise ValueError("scale must be greater than zero")
    raw_values = gateway.read_registers(area, address, count)
    return {
        "area": area,
        "start_address": address,
        "scale": scale,
        "values": [
            {
                "address": address + offset,
                "raw": raw,
                "scaled": raw / scale,
            }
            for offset, raw in enumerate(raw_values)
        ],
    }


@mcp.tool(annotations=WRITE, structured_output=True)
def set_digital_output(address: int, value: bool) -> dict[str, Any]:
    """Set one Factory I/O actuator mapped to a Modbus coil."""
    result = gateway.write_coil(address, value)
    return {"area": "coils", **result}


@mcp.tool(annotations=WRITE, structured_output=True)
def set_analog_output(
    address: int,
    value: float,
    scale: float = 1.0,
) -> dict[str, Any]:
    """Set one actuator holding register; raw value is round(value * scale)."""
    if scale <= 0:
        raise ValueError("scale must be greater than zero")
    raw_value = round(value * scale)
    result = gateway.write_holding_register(address, raw_value)
    return {"area": "holding_registers", "scale": scale, **result}


def main() -> None:
    """Run the MCP server over stdio for Codex."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

