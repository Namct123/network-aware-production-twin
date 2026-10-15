"""Quick connection check that does not write to Factory I/O."""

from factoryio_mcp.modbus_gateway import ModbusGateway, ModbusSettings


if __name__ == "__main__":
    print(ModbusGateway(ModbusSettings()).status())

