# Phoenix - Serial Cables PCIe Gen6 Retimer API (Broadcom)

**Phoenix** is a Python API for controlling and monitoring Serial Cables PCIe Gen6 Retimer chips (Broadcom). It provides a comprehensive interface for device configuration, status monitoring, and diagnostics through both I2C/SMBus and UART interfaces.

Developed by [Serial Cables](https://serialcables.com) for their line of PCIe Gen6 Retimer products.

## Features

- **Web Dashboard (NiceGUI)**
  - Real-time device monitoring with live temperature and voltage gauges
  - Interactive configuration editor with all 33 bifurcation modes
  - Per-lane status visualization with 16-lane color-coded grid
  - PRBS testing and eye diagram capture tools
  - Register browser with bit-field decode visualization
  - Dark theme with hardware-engineer aesthetic

- **Dual Transport Support**
  - I2C/SMBus via USB adapters (FTDI, with Aardvark support planned)
  - UART via on-board MCU serial debug interface
  - Automatic PEC (Packet Error Checking) for data integrity

- **Complete Device Control**
  - 33 bifurcation modes (x16, x8x8, x4x4x4x4, and more)
  - PCIe Gen1 through Gen6 data rate configuration
  - Multiple clocking modes (Common, SRIS, SRNS)
  - Port orientation (static/dynamic)

- **Status Monitoring**
  - Real-time temperature and voltage readings
  - LTSSM state machine monitoring
  - Link speed and width status
  - Error statistics and interrupt status

- **Diagnostic Capabilities**
  - PRBS pattern generation and checking
  - Eye diagram capture with margin analysis
  - ELA / BELA logic analyzers
  - LinkCAT channel analysis
  - Register-level access for debugging

- **Four Interfaces**
  - Python API for scripting and automation
  - REST API for programmatic access
  - Web Dashboard for interactive browser use
  - Command-line interface for quick operations

## Requirements

- Python 3.10 or higher
- USB-to-I2C adapter (FTDI FT232H recommended) or serial connection
- Serial Cables Gen6 PCIe/CXL Retimer (Broadcom)

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/serialcables/serialcables-phoenix.git
cd serialcables-phoenix

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install serialcables-phoenix
```

### Optional Dependencies

```bash
# For Aardvark USB adapter support
pip install -e ".[aardvark]"
```

## Quick Start

### 1. Start the Dashboard

```bash
# Start with web dashboard (default)
phoenix serve

# Opens browser to http://localhost:8000
# REST API available at http://localhost:8000/api/devices/

# API-only mode (no dashboard)
phoenix serve --no-ui

# Custom host/port
phoenix serve --host 0.0.0.0 --port 8080
```

### 2. Discover Devices

```bash
# Scan I2C bus for retimer devices
phoenix discover

# Scan specific addresses
phoenix discover --address 0x50 --address 0x51

# Scan with custom bus speed
phoenix discover --speed 100
```

### 3. Check Device Status

```bash
# Get complete device status
phoenix status 0x50

# Output:
# === Device Status ===
# Temperature:     45 C
# Firmware:        1.23
# Healthy:         Yes
#
# --- Port A (PPA) ---
#   LTSSM State:  FWD_FORWARDING
#   Link Speed:   GEN5_32G
#   Link Width:   x16
#   Link Up:      Yes
```

### 4. Configure Device

```bash
# View current configuration
phoenix config 0x50

# Set bifurcation mode
phoenix set-config 0x50 --bifurcation X8_X8

# Set maximum data rate
phoenix set-config 0x50 --data-rate GEN5_32G

# Set clocking mode
phoenix set-config 0x50 --clocking COMMON_SSC
```

## Web Dashboard

The NiceGUI-based web dashboard provides a complete browser interface for all Phoenix operations. Start it with `phoenix serve` and open `http://localhost:8000`.

### Dashboard Pages

| Page | Route | Description |
|------|-------|-------------|
| Discovery | `/` | Scan for devices on I2C or UART, connect |
| Dashboard | `/device/{handle}` | Real-time status: temperature gauge, voltage chart, port status, interrupts |
| Ports | `/device/{handle}/ports` | PPA/PPB detail with 16-lane grid visualization |
| Configuration | `/device/{handle}/config` | Edit bifurcation, data rate, clocking, interrupts; reset controls |
| Diagnostics | `/device/{handle}/diagnostics` | PRBS testing, eye diagram capture, ELA/BELA/LinkCAT |
| Registers | `/device/{handle}/registers` | Named register browser, direct hex read/write, field decode |

### Dashboard Architecture

- Built with NiceGUI >= 2.0 (FastAPI + Vue/Quasar, WebSocket-based)
- Mounted onto the existing FastAPI app via `ui.run_with(app)`
- Direct in-process device calls (no HTTP serialization overhead)
- Real-time updates via `ui.timer()` at 2-second intervals
- ECharts for temperature gauges, voltage bars, and eye diagrams
- Entire UI is Python -- no JavaScript required

## Python API Usage

### Basic Example

```python
import asyncio
from phoenix.core.device import RetimerDevice
from phoenix.models.configuration import ConfigurationUpdate
from phoenix.protocol.enums import BifurcationMode, MaxDataRate

async def main():
    # Connect to device via I2C
    async with await RetimerDevice.from_i2c(address=0x50) as device:
        # Get device status
        status = await device.get_status()
        print(f"Temperature: {status.temperature_c} C")
        print(f"PPA Link Speed: {status.ppa_status.current_link_speed.name}")
        print(f"PPB Link Speed: {status.ppb_status.current_link_speed.name}")

        # Get current configuration
        config = await device.get_configuration()
        print(f"Bifurcation: {config.bifurcation_mode.name}")

        # Update configuration
        update = ConfigurationUpdate(
            bifurcation_mode=BifurcationMode.X8_X8,
            max_data_rate=MaxDataRate.GEN5_32G,
        )
        await device.set_configuration(update)

        # Read a register directly
        value = await device.read_register(0x0000)
        print(f"GLOBAL_PARAM0: 0x{value:08X}")

asyncio.run(main())
```

### Device Discovery

```python
import asyncio
from phoenix.core.discovery import DeviceDiscovery

async def discover_devices():
    discovery = DeviceDiscovery()

    # Discover on I2C bus
    devices = await discovery.discover_i2c(
        adapter_port=0,
        addresses=[0x50, 0x51, 0x52],
        bus_speed_khz=400,
    )

    for device in devices:
        print(f"Found: {device.vendor_id_str}:{device.device_id_str}")
        print(f"  Address: 0x{device.device_address:02X}")
        print(f"  Firmware: {device.firmware_version_str}")

asyncio.run(discover_devices())
```

### UART Connection

```python
import asyncio
from phoenix.core.device import RetimerDevice

async def uart_example():
    # Connect via UART
    device = await RetimerDevice.from_uart(
        port="COM3",  # or "/dev/ttyUSB0" on Linux
        baud_rate=115200,
    )

    try:
        status = await device.get_status()
        print(f"Temperature: {status.temperature_c} C")
    finally:
        await device.disconnect()

asyncio.run(uart_example())
```

### Error Handling

```python
import asyncio
from phoenix.core.device import RetimerDevice
from phoenix.exceptions import (
    PhoenixError,
    DeviceNotFoundError,
    TransportError,
    TimeoutError,
)

async def safe_operation():
    try:
        device = await RetimerDevice.from_i2c(address=0x50)
        status = await device.get_status()
    except DeviceNotFoundError:
        print("Device not found at specified address")
    except TransportError as e:
        print(f"Communication error: {e}")
    except TimeoutError as e:
        print(f"Operation timed out: {e}")
    except PhoenixError as e:
        print(f"Phoenix error: {e}")

asyncio.run(safe_operation())
```

## REST API

The REST API provides HTTP endpoints for all device operations. It is available at `/api/` when the server is running.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/devices/discover` | Discover devices |
| `GET` | `/api/devices/` | List discovered devices |
| `GET` | `/api/devices/{handle}` | Get device info |
| `POST` | `/api/devices/{handle}/connect` | Connect to device |
| `POST` | `/api/devices/{handle}/disconnect` | Disconnect device |
| `GET` | `/api/devices/{handle}/status` | Get device status |
| `GET` | `/api/devices/{handle}/temperature` | Get temperature |
| `GET` | `/api/devices/{handle}/voltage` | Get voltage levels |
| `GET` | `/api/devices/{handle}/config` | Get configuration |
| `PUT` | `/api/devices/{handle}/config` | Update configuration |
| `POST` | `/api/devices/{handle}/reset` | Reset device |
| `GET` | `/api/devices/{handle}/register/{addr}` | Read register |
| `PUT` | `/api/devices/{handle}/register/{addr}` | Write register |
| `POST` | `/api/devices/{handle}/prbs/start` | Start PRBS test |
| `GET` | `/api/devices/{handle}/prbs/status` | Get PRBS status |
| `POST` | `/api/devices/{handle}/prbs/stop` | Stop PRBS test |
| `GET` | `/api/devices/{handle}/prbs/results` | Get PRBS results |
| `POST` | `/api/devices/{handle}/eye-diagram` | Capture eye diagram |

### Example API Calls

```bash
# Discover devices
curl -X POST http://localhost:8000/api/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"transport_type": "i2c", "adapter_port": 0}'

# Get device status
curl http://localhost:8000/api/devices/1/status

# Update configuration
curl -X PUT http://localhost:8000/api/devices/1/config \
  -H "Content-Type: application/json" \
  -d '{"bifurcation_mode": "X8_X8", "max_data_rate": "GEN5_32G"}'

# Read register
curl http://localhost:8000/api/devices/1/register/0x0000

# Reset device
curl -X POST http://localhost:8000/api/devices/1/reset \
  -H "Content-Type: application/json" \
  -d '{"reset_type": "SOFT"}'
```

### OpenAPI Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## CLI Reference

### Global Options

```
phoenix [OPTIONS] COMMAND [ARGS]...

Options:
  --debug    Enable debug logging
  --help     Show this message and exit
```

### Commands

| Command | Description |
|---------|-------------|
| `discover` | Scan I2C bus for retimer devices |
| `status` | Get device status |
| `config` | Get device configuration |
| `set-config` | Update device configuration |
| `reset` | Reset device |
| `read-reg` | Read register directly |
| `write-reg` | Write register directly |
| `serve` | Start REST API server with web dashboard |

### `serve` - Start Server

```bash
phoenix serve [OPTIONS]

Options:
  -h, --host TEXT        Host to bind [default: 127.0.0.1]
  -p, --port INTEGER     Port to bind [default: 8000]
  --no-ui                API-only mode, no web dashboard
```

### `discover` - Find Devices

```bash
phoenix discover [OPTIONS]

Options:
  -p, --port INTEGER     USB adapter port number [default: 0]
  -a, --address TEXT     I2C address(es) to scan (hex)
  -s, --speed INTEGER    I2C bus speed in kHz [default: 400]
```

### `status` - Get Device Status

```bash
phoenix status ADDRESS [OPTIONS]

Arguments:
  ADDRESS    Device I2C address (hex or decimal)

Options:
  -p, --port INTEGER     USB adapter port [default: 0]
  -s, --speed INTEGER    I2C bus speed in kHz [default: 400]
```

### `set-config` - Update Configuration

```bash
phoenix set-config ADDRESS [OPTIONS]

Options:
  -b, --bifurcation TEXT    Bifurcation mode
  -d, --data-rate TEXT      Maximum data rate
  -c, --clocking TEXT       Clocking mode
```

### `reset` - Reset Device

```bash
phoenix reset ADDRESS [OPTIONS]

Options:
  -t, --type [HARD|SOFT|MAC|PERST|GLOBAL_SWRST]
                            Reset type [default: SOFT]
```

### `read-reg` / `write-reg` - Register Access

```bash
phoenix read-reg ADDRESS REGISTER [OPTIONS]
phoenix write-reg ADDRESS REGISTER VALUE [OPTIONS]

Options:
  -w, --width [16|32]    Register width [default: 32]
```

## Architecture

```
+---------------------------------------------------------+
|                    Applications                          |
+-----------+-----------+-----------+---------------------+
| CLI       | REST API  | Web       | Python Scripts      |
| (Click)   | (FastAPI) | Dashboard |                     |
|           |           | (NiceGUI) |                     |
+-----------+-----------+-----------+---------------------+
|                    Core Layer                            |
|  +--------------+  +--------------+  +---------------+  |
|  |RetimerDevice |  |  Discovery   |  | Configuration |  |
|  +--------------+  +--------------+  +---------------+  |
+---------------------------------------------------------+
|                   Protocol Layer                         |
|  +--------------+  +--------------+  +---------------+  |
|  |SMBus Commands|  |Register Maps |  |    Enums      |  |
|  +--------------+  +--------------+  +---------------+  |
+---------------------------------------------------------+
|                  Transport Layer                         |
|  +--------------+  +--------------+                     |
|  |I2C Transport |  |UART Transport|                     |
|  |   (FTDI)     |  |  (pyserial)  |                     |
|  +--------------+  +--------------+                     |
+---------------------------------------------------------+
|                     Hardware                             |
|  +--------------+  +--------------+                     |
|  | USB-to-I2C   |  |  UART/MCU    |                     |
|  |   Adapter    |  |  Interface   |                     |
|  +--------------+  +--------------+                     |
+---------------------------------------------------------+
```

## Hardware Setup

### I2C Connection (Recommended)

1. Connect FTDI FT232H USB adapter to your computer
2. Wire I2C signals to the retimer's SMBus interface:
   - `SDA` (Data)
   - `SCL` (Clock)
   - `GND` (Ground)
3. Ensure proper pull-up resistors on SDA/SCL (typically 4.7k ohm)

### UART Connection

1. Connect to the retimer's MCU debug header
2. Use standard UART settings: 115200 baud, 8N1
3. Wire TX, RX, and GND

### Default I2C Addresses

The BCM85667 typically responds at addresses `0x50` through `0x57`, configurable via hardware strapping.

## Configuration Reference

### Bifurcation Modes

| Mode | Description |
|------|-------------|
| `X16` | Single x16 link |
| `X8` | Single x8 link |
| `X4` | Single x4 link |
| `X8_X8` | Two x8 links |
| `X8_X4_X4` | One x8 + two x4 links |
| `X4_X4_X8` | Two x4 + one x8 links |
| `X4_X4_X4_X4` | Four x4 links |
| `X2_X2_X2_X2_X2_X2_X2_X2` | Eight x2 links |
| ... | (33 modes total) |

### Data Rates

| Rate | Speed | PCIe Gen |
|------|-------|----------|
| `GEN1_2P5G` | 2.5 GT/s | Gen1 |
| `GEN2_5G` | 5 GT/s | Gen2 |
| `GEN3_8G` | 8 GT/s | Gen3 |
| `GEN4_16G` | 16 GT/s | Gen4 |
| `GEN5_32G` | 32 GT/s | Gen5 |
| `GEN6_64G` | 64 GT/s | Gen6 |

### Clocking Modes

| Mode | Description |
|------|-------------|
| `COMMON_WO_SSC` | Common clock without SSC |
| `COMMON_SSC` | Common clock with SSC |
| `SRNS_WO_SSC` | SRNS without SSC |
| `SRIS_SSC` | SRIS with SSC |
| `SRIS_WO_SSC` | SRIS without SSC (debug) |
| `SRIS_WO_SSC_LL` | SRIS without SSC (low latency) |

### Reset Types

| Type | Description |
|------|-------------|
| `HARD` | Full chip reset including all registers |
| `SOFT` | Reset except sticky registers |
| `MAC` | Global MAC software reset |
| `PERST` | PCIe fundamental reset |
| `GLOBAL_SWRST` | Toggle global software link reset |

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/serialcables/serialcables-phoenix.git
cd serialcables-phoenix

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=phoenix --cov-report=html

# Run specific test file
pytest tests/unit/test_transport.py
```

### Code Quality

```bash
# Format code
ruff format src/

# Lint code
ruff check src/

# Type checking
mypy src/phoenix/
```

## Troubleshooting

### Device Not Found

1. **Check connections**: Verify I2C wiring and power
2. **Check address**: Use `phoenix discover` to scan all addresses
3. **Check adapter**: Ensure USB adapter is recognized by the OS
4. **Reduce speed**: Try `--speed 100` for lower bus speeds

### Communication Errors

1. **PEC failures**: May indicate signal integrity issues
2. **Timeouts**: Check for bus contention or incorrect address
3. **I2C NAK**: Device may be busy or address incorrect

### Permission Errors (Linux)

```bash
# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER

# Create udev rule for USB adapter
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-ftdi.rules
sudo udevadm control --reload-rules
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/), [NiceGUI](https://nicegui.io/), [Click](https://click.palletsprojects.com/), and [Pydantic](https://pydantic-docs.helpmanual.io/)

## Support

- **Issues**: [GitHub Issues](https://github.com/jpmutschler/serialcables-phoenix/issues)
- **Email**: support@serialcables.com

---

Copyright 2026 Serial Cables. All rights reserved.
