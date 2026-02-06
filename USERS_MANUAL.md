# Phoenix User's Manual

## Broadcom Vantage BCM85667 PCIe Gen6 Retimer API & Dashboard

**Version 0.1.0**

**Serial Cables**
[serialcables.com](https://serialcables.com)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)
4. [Hardware Setup](#4-hardware-setup)
5. [Getting Started](#5-getting-started)
6. [Web Dashboard](#6-web-dashboard)
   - 6.1 [Device Discovery Page](#61-device-discovery-page)
   - 6.2 [Device Dashboard](#62-device-dashboard)
   - 6.3 [Port Status Page](#63-port-status-page)
   - 6.4 [Configuration Page](#64-configuration-page)
   - 6.5 [Diagnostics Page](#65-diagnostics-page)
   - 6.6 [Register Browser](#66-register-browser)
7. [Command-Line Interface](#7-command-line-interface)
8. [REST API Reference](#8-rest-api-reference)
9. [Python API Reference](#9-python-api-reference)
10. [Configuration Reference](#10-configuration-reference)
    - 10.1 [Bifurcation Modes](#101-bifurcation-modes)
    - 10.2 [Data Rates](#102-data-rates)
    - 10.3 [Clocking Modes](#103-clocking-modes)
    - 10.4 [Reset Types](#104-reset-types)
    - 10.5 [Port Orientation](#105-port-orientation)
    - 10.6 [Interrupt Configuration](#106-interrupt-configuration)
    - 10.7 [TX Equalization Coefficients](#107-tx-equalization-coefficients)
11. [Diagnostics Guide](#11-diagnostics-guide)
    - 11.1 [PRBS Testing](#111-prbs-testing)
    - 11.2 [Eye Diagram Capture](#112-eye-diagram-capture)
    - 11.3 [Embedded Logic Analyzer (ELA)](#113-embedded-logic-analyzer-ela)
    - 11.4 [Broadcom Embedded Logic Analyzer (BELA)](#114-broadcom-embedded-logic-analyzer-bela)
    - 11.5 [Link Channel Analysis Tool (LinkCAT)](#115-link-channel-analysis-tool-linkcat)
12. [Register Map Reference](#12-register-map-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [Appendix A: LTSSM State Reference](#14-appendix-a-ltssm-state-reference)
15. [Appendix B: Error Statistics Reference](#15-appendix-b-error-statistics-reference)
16. [Appendix C: PRBS Pattern Reference](#16-appendix-c-prbs-pattern-reference)

---

## 1. Introduction

Phoenix is a Python-based control and monitoring platform for the **Broadcom Vantage BCM85667 PCIe Gen6 x16 Retimer**. It provides four complementary interfaces for interacting with retimer hardware:

- **Web Dashboard** -- A browser-based UI for real-time monitoring, configuration, diagnostics, and register-level debugging
- **Command-Line Interface (CLI)** -- Terminal commands for scripted or interactive device operations
- **REST API** -- HTTP endpoints for integration with other tools and automation systems
- **Python API** -- Direct Python library for custom scripts and advanced automation

Phoenix communicates with the BCM85667 over **I2C/SMBus** (via FTDI FT232H USB adapters) or **UART** (via on-board MCU serial debug). All operations use the Broadcom Vantage VNT6_0_0_2 SDK protocol with automatic PEC (Packet Error Checking) for data integrity.

### Key Capabilities

- Discover and connect to retimer devices on I2C or UART bus
- Monitor temperature, voltage rails, link status, and LTSSM state in real time
- Configure bifurcation (33 modes), data rates (Gen1--Gen6), clocking, and interrupts
- Run PRBS bit error rate tests across all 16 lanes
- Capture eye diagrams with margin analysis
- Browse and edit individual registers with field-level decode
- Reset the device (hard, soft, MAC, PERST, global software reset)

### About the BCM85667

The Broadcom Vantage BCM85667 is a 16-lane PCIe retimer supporting Gen1 through Gen6 (2.5 GT/s to 64 GT/s). It features:

- Two pseudo ports: **PPA** (Pseudo Port A) and **PPB** (Pseudo Port B)
- Up to 8 sub-ports via lane bifurcation
- Per-lane TX equalization with configurable coefficients for Gen3--Gen6
- Built-in PRBS generator/checker for signal integrity testing
- Eye diagram capture with margin reporting
- Embedded logic analyzers (ELA, BELA) for protocol-level debugging
- LinkCAT channel analysis for insertion loss measurement

---

## 2. System Requirements

### Software

| Requirement | Minimum |
|-------------|---------|
| Python | 3.10 or higher |
| Operating System | Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+ |
| Web Browser | Chrome, Firefox, or Edge (for dashboard) |

### Hardware

| Component | Details |
|-----------|---------|
| Retimer | Serial Cables Gen6 PCIe/CXL Retimer (Broadcom BCM85667) |
| I2C Adapter | FTDI FT232H USB-to-I2C adapter (recommended) |
| UART | USB-to-serial adapter or on-board MCU debug header |
| Pull-up Resistors | 4.7k ohm on SDA/SCL lines (for I2C) |

### I2C Address Range

The BCM85667 typically responds at addresses **0x50 through 0x57**, configurable via hardware strapping pins on the board.

---

## 3. Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/serialcables/serialcables-phoenix.git
cd serialcables-phoenix

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### From PyPI

```bash
pip install serialcables-phoenix
```

### Optional: Aardvark Adapter Support

```bash
pip install -e ".[aardvark]"
```

### Verify Installation

```bash
# Check that the CLI is available
phoenix --help

# Expected output:
# Usage: phoenix [OPTIONS] COMMAND [ARGS]...
#
# Phoenix - Broadcom Vantage PCIe Gen6 Retimer CLI.
#
# Options:
#   --debug  Enable debug logging
#   --help   Show this message and exit
#
# Commands:
#   config      Get device configuration.
#   discover    Discover retimer devices on I2C bus.
#   read-reg    Read a register.
#   reset       Reset the device.
#   serve       Start the REST API server with optional NiceGUI dashboard.
#   set-config  Set device configuration.
#   status      Get device status.
#   write-reg   Write a register.
```

---

## 4. Hardware Setup

### 4.1 I2C Connection (Recommended)

The I2C interface provides reliable, low-latency access to the retimer over a standard SMBus connection.

**Wiring:**

| FT232H Pin | Retimer Pin | Signal |
|------------|-------------|--------|
| AD0 | SCL | Clock |
| AD1/AD2 | SDA | Data |
| GND | GND | Ground |

**Setup steps:**

1. Connect the FTDI FT232H USB adapter to your computer via USB.
2. Wire the I2C signals (SDA, SCL, GND) between the adapter and the retimer's SMBus header.
3. Ensure **4.7k ohm pull-up resistors** are present on both SDA and SCL lines (some boards include these on-board).
4. Verify the USB adapter is recognized by the OS:
   - **Windows**: Check Device Manager for "USB Serial Converter"
   - **Linux**: Check `dmesg` or `lsusb` for FTDI device (vendor 0x0403)
   - **macOS**: Check System Information > USB

**Default I2C settings:**

| Parameter | Default |
|-----------|---------|
| Bus Speed | 400 kHz |
| Adapter Port | 0 |
| Device Addresses | 0x50--0x57 |

### 4.2 UART Connection

The UART interface connects to the retimer's on-board MCU debug port.

**Wiring:**

| Adapter Pin | Retimer Pin | Signal |
|-------------|-------------|--------|
| TX | RX | Transmit |
| RX | TX | Receive |
| GND | GND | Ground |

**UART settings:**

| Parameter | Default |
|-----------|---------|
| Baud Rate | 115200 |
| Data Bits | 8 |
| Stop Bits | 1 |
| Parity | None |
| Flow Control | None |

**Setup steps:**

1. Connect a USB-to-serial adapter (or use the on-board debug header) to your computer.
2. Wire TX, RX, and GND between the adapter and the retimer's MCU debug header.
3. Note the serial port name:
   - **Windows**: `COM3`, `COM4`, etc. (check Device Manager)
   - **Linux**: `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.
   - **macOS**: `/dev/tty.usbserial-*`

### 4.3 Linux Permissions

On Linux, you may need to add your user to the `dialout` group for serial access and create a udev rule for the USB adapter:

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Create udev rule for FTDI USB adapter
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-ftdi.rules
sudo udevadm control --reload-rules

# Log out and back in for group changes to take effect
```

---

## 5. Getting Started

### 5.1 Start the Web Dashboard

The fastest way to interact with Phoenix is through the web dashboard:

```bash
phoenix serve
```

This starts the server at `http://localhost:8000`. Your default browser should open automatically. If not, navigate to that URL manually.

The REST API is available simultaneously at `http://localhost:8000/api/devices/`.

**Custom host and port:**

```bash
phoenix serve --host 0.0.0.0 --port 8080
```

**API-only mode (no dashboard):**

```bash
phoenix serve --no-ui
```

### 5.2 Discover Devices via CLI

```bash
# Scan default I2C addresses (0x50-0x57)
phoenix discover

# Scan specific addresses
phoenix discover --address 0x50 --address 0x51

# Scan with custom bus speed
phoenix discover --speed 100

# Scan on a different adapter port
phoenix discover --port 1
```

### 5.3 Check Device Status

```bash
phoenix status 0x50
```

Example output:

```
=== Device Status ===

Temperature:     45 C
Firmware:        1.23
Healthy:         Yes

--- Voltages ---
  DVDD1:   820 mV
  DVDD2:   820 mV
  DVDD3:   1100 mV
  DVDD4:   1100 mV
  DVDD5:   1800 mV
  DVDD6:   1800 mV
  DVDDIO:  1800 mV

--- Port A (PPA) ---
  LTSSM State:  FWD_FORWARDING
  Link Speed:   GEN5_32G
  Link Width:   x16
  Link Up:      Yes
  Forwarding:   Yes

--- Port B (PPB) ---
  LTSSM State:  FWD_FORWARDING
  Link Speed:   GEN5_32G
  Link Width:   x16
  Link Up:      Yes
  Forwarding:   Yes

--- Interrupts ---
  Global:        Clear
  EQ Phase Err:  Clear
  PHY Phase Err: Clear
  Internal Err:  Clear
```

### 5.4 Configure a Device

```bash
# Set bifurcation to two x8 links
phoenix set-config 0x50 --bifurcation X8_X8

# Set maximum data rate to Gen5
phoenix set-config 0x50 --data-rate GEN5_32G

# Set clocking mode
phoenix set-config 0x50 --clocking COMMON_SSC

# Combine multiple settings
phoenix set-config 0x50 --bifurcation X8_X8 --data-rate GEN5_32G --clocking COMMON_SSC
```

### 5.5 Read and Write Registers

```bash
# Read a 32-bit register
phoenix read-reg 0x50 0x0000

# Read a 16-bit register
phoenix read-reg 0x50 0x0100 --width 16

# Write a register
phoenix write-reg 0x50 0x0000 0x12345678
```

---

## 6. Web Dashboard

The Phoenix web dashboard provides a complete browser-based interface for all device operations. It is built with NiceGUI (Python) and uses WebSocket connections for real-time updates.

### Architecture Overview

- **Framework**: NiceGUI 2.0+ (FastAPI + Vue/Quasar)
- **Transport**: WebSocket-based real-time communication
- **Updates**: Automatic 2-second polling for live status data
- **Charts**: ECharts for temperature gauges and voltage bar charts
- **Theme**: Dark theme with cyan accent colors, designed for hardware engineers

### Navigation

The dashboard uses a persistent left sidebar for navigation. When connected to one or more devices, each device appears as an expandable tree node with links to its sub-pages (Dashboard, Ports, Configuration, Diagnostics, Registers).

### Page Summary

| Route | Page | Description |
|-------|------|-------------|
| `/` | Discovery | Scan for devices, connect |
| `/device/{handle}` | Dashboard | Real-time monitoring |
| `/device/{handle}/ports` | Ports | PPA/PPB detail with lane grid |
| `/device/{handle}/config` | Configuration | Edit all settings |
| `/device/{handle}/diagnostics` | Diagnostics | PRBS, eye diagram, ELA/BELA/LinkCAT |
| `/device/{handle}/registers` | Registers | Register browser, direct read/write |

---

### 6.1 Device Discovery Page

**Route:** `/`

The discovery page is the landing page when you first open the dashboard. It allows you to scan for retimer devices on the I2C or UART bus and connect to them.

#### Transport Selection

At the top of the page, a toggle switch selects between **I2C / SMBus** and **UART** transport modes. The scan settings below change depending on the selected transport.

#### I2C Settings

| Field | Description | Default |
|-------|-------------|---------|
| Adapter Port | USB adapter port number (0--7) | 0 |
| Bus Speed | I2C bus clock speed | 400 kHz |
| Addresses | Comma-separated hex addresses to scan | 0x50, 0x51, 0x52, 0x53 |

#### UART Settings

| Field | Description | Default |
|-------|-------------|---------|
| Serial Port | OS serial port name | COM3 |
| Baud Rate | UART baud rate | 115200 |

#### Scanning

Click **Scan for Devices** to initiate a bus scan. The scan probes each specified address and reports any retimer devices found. Each discovered device appears as a card showing:

- Device address (hex)
- Vendor ID and Device ID
- Firmware version
- Maximum supported data rate
- **Connect** button

#### Direct Connect

Click **Direct Connect** to connect to the first specified address without scanning. This is useful when you know the exact device address.

#### Connecting

Click the **Connect** button on any discovered device card. Upon successful connection, you are automatically redirected to that device's Dashboard page. The device also appears in the sidebar navigation tree.

---

### 6.2 Device Dashboard

**Route:** `/device/{handle}`

The dashboard provides a real-time overview of the connected retimer's health and status. All values update automatically every 2 seconds.

#### Health Status

A color-coded health badge at the top indicates overall device health:

- **Healthy** (green): No internal errors, temperature below 100 C
- **Warning** (yellow): Temperature between 85 C and 100 C
- **Error** (red): Internal error detected or temperature above 100 C

The firmware version and device handle are displayed alongside the health badge.

#### Temperature Gauge

A circular ECharts gauge displays the die temperature in degrees Celsius. The gauge uses color bands to indicate thermal zones:

| Range | Color | Status |
|-------|-------|--------|
| 0--85 C | Green | Normal |
| 85--100 C | Yellow | Warning |
| 100--125 C | Red | Critical |

The gauge range is 0--125 C with the current temperature shown numerically at center.

#### Voltage Chart

A horizontal bar chart displays all 7 voltage rails in millivolts:

| Rail | Typical Value | Description |
|------|---------------|-------------|
| DVDD1 | 820 mV | Core digital supply 1 |
| DVDD2 | 820 mV | Core digital supply 2 |
| DVDD3 | 1100 mV | Core digital supply 3 |
| DVDD4 | 1100 mV | Core digital supply 4 |
| DVDD5 | 1800 mV | Core digital supply 5 |
| DVDD6 | 1800 mV | Core digital supply 6 |
| DVDDIO | 1800 mV | I/O digital supply |

#### Port Status Summary

Two side-by-side cards show the status of PPA and PPB:

- **LTSSM State**: Current state machine state (e.g., FWD_FORWARDING, DETECT)
- **Link Speed**: Current negotiated speed (e.g., GEN5_32G)
- **Link Width**: Current negotiated width (e.g., x16)
- **Link State**: UP or DOWN with color indicator
- **Forwarding**: Whether packet forwarding is active

#### Interrupt Status

A row of badges shows the current interrupt status:

| Interrupt | Description |
|-----------|-------------|
| Global Interrupt | Master interrupt status |
| EQ Phase Error | Equalization phase error |
| PHY Phase Error | PHY phase error |
| Internal Error | Internal device error |

Each badge is colored green (clear) or red (set).

---

### 6.3 Port Status Page

**Route:** `/device/{handle}/ports`

The port status page provides detailed information about both pseudo ports (PPA and PPB) with per-lane visualization.

#### Port Detail Cards

Each port (PPA and PPB) is displayed in a card with the following information:

| Field | Description |
|-------|-------------|
| Port Type | Upstream or Downstream |
| LTSSM State | Current state machine state |
| Link Speed | Negotiated PCIe generation |
| Link Width | Negotiated lane count |
| Link State | UP or DOWN |
| Forwarding Mode | Enabled or Disabled |
| Enabled Lanes | Number of active lanes |

#### 16-Lane Grid

Below each port card, a **16-lane visual grid** (arranged as 8 columns x 2 rows) shows per-lane status with color coding:

| Color | Meaning |
|-------|---------|
| Green | All equalization complete (TX EQ + RX EQ done) |
| Yellow | Receiver detected only (RX Detect, but EQ not complete) |
| Gray | Lane inactive or no receiver detected |

Hovering over a lane cell shows a tooltip with:

- Lane number
- RX Detect status
- TX EQ Done status
- RX EQ Done status

#### LTSSM State Reference

A collapsible reference table at the bottom of the page lists all LTSSM states and their hex values for quick lookup during debugging.

---

### 6.4 Configuration Page

**Route:** `/device/{handle}/config`

The configuration page allows you to view and modify all retimer settings. The current configuration is loaded automatically when you navigate to the page.

#### Bifurcation Mode

A dropdown selector with all 33 supported bifurcation modes. The current mode is pre-selected. See [Section 10.1](#101-bifurcation-modes) for the complete list.

#### Maximum Data Rate

A dropdown selector for the maximum negotiated PCIe data rate:

| Option | Speed |
|--------|-------|
| GEN1_2P5G | 2.5 GT/s |
| GEN2_5G | 5.0 GT/s |
| GEN3_8G | 8.0 GT/s |
| GEN4_16G | 16.0 GT/s |
| GEN5_32G | 32.0 GT/s |
| GEN6_64G | 64.0 GT/s |

#### Clocking Mode

A dropdown selector for the reference clock configuration. See [Section 10.3](#103-clocking-modes) for details.

#### Port Orientation

A dropdown selector to choose between **Static** (PPA/PPB predefined) and **Dynamic** (PPA/PPB assigned dynamically based on which side trains first).

#### Interrupt Enables

Toggle switches to enable or disable each interrupt source:

- Global Interrupt Enable
- EQ Phase Error Enable
- PHY Phase Error Enable
- Internal Error Enable

#### Applying Configuration

Click **Apply Configuration** to write the selected settings to the device. A confirmation dialog appears before applying to prevent accidental changes.

A status message below the button indicates success or failure.

#### Reset Controls

Three reset buttons are available at the bottom of the page:

| Button | Reset Type | Description |
|--------|-----------|-------------|
| Soft Reset | SOFT | Resets device except sticky registers |
| Hard Reset | HARD | Full chip reset including all registers |
| PERST | PERST | PCIe fundamental reset (PERST#) |

Each reset button shows a confirmation dialog before executing. After a reset, the device may need to re-train links and the dashboard will reflect the new state after the next polling cycle.

---

### 6.5 Diagnostics Page

**Route:** `/device/{handle}/diagnostics`

The diagnostics page provides access to signal integrity testing and analysis tools through five tabs.

#### 6.5.1 PRBS Tab

**Pseudo-Random Bit Sequence (PRBS) testing** verifies signal integrity by comparing generated and received bit patterns across selected lanes.

**Configuration:**

| Setting | Options | Default |
|---------|---------|---------|
| Pattern | PRBS7, PRBS9, PRBS10, PRBS11, PRBS13, PRBS15, PRBS20, PRBS23, PRBS31, PRBS49, PRBS58 | PRBS31 |
| Data Rate | Gen1 through Gen6 | GEN5_32G |
| Lanes | Checkboxes for lanes 0--15 | All enabled |
| Sample Count | Hex value for checker sample count | 0x100000 |

**Controls:**

- **Start PRBS**: Starts PRBS generator and checker on selected lanes
- **Stop PRBS**: Stops the running test
- **Get Results**: Reads current results from the device

**Results Table:**

| Column | Description |
|--------|-------------|
| Lane | Lane number |
| Bit Count | Total bits checked |
| Errors | Number of bit errors detected |
| BER | Bit Error Rate (scientific notation, or "< 1e-15" for zero errors) |
| Sync | Whether the checker acquired pattern synchronization |
| Complete | Whether the test completed its sample count |

See [Section 11.1](#111-prbs-testing) for a complete guide to PRBS testing.

#### 6.5.2 Eye Diagram Tab

**Eye diagram capture** measures signal margin at the receiver to assess signal quality.

**Configuration:**

| Setting | Options | Default |
|---------|---------|---------|
| Lane | 0--15 | 0 |
| Data Rate | Gen1 through Gen6 | GEN5_32G |

Click **Capture Eye** to run the measurement. Results display:

- **Capture Valid**: Whether the capture completed successfully
- **Middle Eye** margins (always present):
  - Left Margin (mUI)
  - Right Margin (mUI)
  - Upper Margin (mV)
  - Lower Margin (mV)
  - Horizontal Opening (mUI) -- sum of left + right
  - Vertical Opening (mV) -- sum of upper + lower
- **Lower Eye** margins (Gen6 only, PAM4 signaling)
- **Upper Eye** margins (Gen6 only, PAM4 signaling)

See [Section 11.2](#112-eye-diagram-capture) for interpretation guidance.

#### 6.5.3 ELA Tab

The **Embedded Logic Analyzer (ELA)** captures protocol-level signal transitions for debugging link training and equalization issues.

**Configuration options:**

| Setting | Options |
|---------|---------|
| ELA Type | Lane Pipe A, Lane Pipe B, Pseudo Port, Pseudo Port A, Pseudo Port B |
| Trigger Position | 0%, 25%, 50%, 75% |
| Mixed Mode | AND trigger mode (multiple conditions) |

**Note:** ELA configuration and capture controls are present in the UI but require firmware support. Controls are disabled with "Not yet implemented" indicators in the current release.

#### 6.5.4 BELA Tab

The **Broadcom Embedded Logic Analyzer (BELA)** is a lane-level logic analyzer for capturing PHY-layer signal transitions.

**Configuration options:**

| Setting | Options |
|---------|---------|
| Lane | 0--15 |
| Trigger Rate | Gen1 through Gen6 |
| Trigger Type | Live Datarate, Datarate Entry, Datarate Exit, Datarate Entry/Exit |
| Force Capture | On/Off |
| Auto Restart | On/Off |

**Note:** BELA controls are present in the UI but require firmware support. Controls are disabled in the current release. BELA captures may impact link performance.

#### 6.5.5 LinkCAT Tab

The **Link Channel Analysis Tool (LinkCAT)** characterizes the PCIe channel by measuring insertion loss at the symbol rate.

**Configuration options:**

| Setting | Options | Default |
|---------|---------|---------|
| Mode | LP TX, Loopback, Pre-RX, RX Measure | LP TX |
| TX Amplitude Scale | 0--99 (0 = default) | 0 |

**Note:** LinkCAT controls are present in the UI but require firmware support. Controls are disabled in the current release. The link must be in a specific state before running LinkCAT.

---

### 6.6 Register Browser

**Route:** `/device/{handle}/registers`

The register browser provides low-level access to all retimer registers for advanced debugging and development.

#### Named Register Table

A table lists all known registers from the register map:

| Column | Description |
|--------|-------------|
| Name | Register name (e.g., GLOBAL_PARAM0) |
| Address | Hex address (e.g., 0x0000) |
| Size | Register width in bytes |
| Description | Brief description of register purpose |

Click any row to select it. The register's address is automatically populated in the direct access fields below.

#### Direct Register Access

Below the register table, a form allows direct register reads and writes:

| Field | Description |
|-------|-------------|
| Address | Register address in hex (e.g., 0x0000) |
| Value | Register value in hex (for writes) |
| Width | Register width: 16-bit or 32-bit |

**Buttons:**

- **Read**: Reads the register at the specified address and displays the value
- **Write**: Writes the specified value to the register address

#### Field Decode

When you read a register that has known field definitions (e.g., GLOBAL_PARAM0), the register browser displays:

1. **Field Table**: Lists each field's name, bit range, extracted value (hex), and description
2. **Bit Map**: A horizontal visualization showing field positions within the register word, with color-coded segments for each field

This decode view makes it easy to inspect individual configuration bits without manual bit manipulation.

---

## 7. Command-Line Interface

The Phoenix CLI provides terminal-based access to all device operations.

### Global Options

```
phoenix [OPTIONS] COMMAND [ARGS]...

Options:
  --debug    Enable debug logging
  --help     Show this message and exit
```

### Commands

#### `discover` -- Find Devices

Scan the I2C bus for retimer devices.

```bash
phoenix discover [OPTIONS]

Options:
  -p, --port INTEGER     USB adapter port number [default: 0]
  -a, --address TEXT     I2C address to scan (hex, repeatable)
  -s, --speed INTEGER    I2C bus speed in kHz [default: 400]
```

**Examples:**

```bash
# Scan default addresses
phoenix discover

# Scan specific addresses
phoenix discover -a 0x50 -a 0x51

# Scan at 100 kHz
phoenix discover --speed 100
```

#### `status` -- Get Device Status

Read the current status of a retimer device.

```bash
phoenix status ADDRESS [OPTIONS]

Arguments:
  ADDRESS    Device I2C address (hex, e.g., 0x50)

Options:
  -p, --port INTEGER     USB adapter port number [default: 0]
  -s, --speed INTEGER    I2C bus speed in kHz [default: 400]
```

**Example:**

```bash
phoenix status 0x50
```

#### `config` -- Get Configuration

Display the current device configuration.

```bash
phoenix config ADDRESS [OPTIONS]

Arguments:
  ADDRESS    Device I2C address (hex)

Options:
  -p, --port INTEGER     USB adapter port number [default: 0]
  -s, --speed INTEGER    I2C bus speed in kHz [default: 400]
```

#### `set-config` -- Update Configuration

Modify device configuration. Only specified fields are changed; others remain unchanged.

```bash
phoenix set-config ADDRESS [OPTIONS]

Arguments:
  ADDRESS    Device I2C address (hex)

Options:
  -p, --port INTEGER           USB adapter port [default: 0]
  -s, --speed INTEGER          Bus speed in kHz [default: 400]
  -b, --bifurcation TEXT       Bifurcation mode name
  -d, --data-rate TEXT         Max data rate name
  -c, --clocking TEXT          Clocking mode name
```

**Examples:**

```bash
# Set bifurcation to dual x8
phoenix set-config 0x50 -b X8_X8

# Set max data rate to Gen5
phoenix set-config 0x50 -d GEN5_32G

# Set multiple options at once
phoenix set-config 0x50 -b X8_X8 -d GEN5_32G -c COMMON_SSC
```

#### `reset` -- Reset Device

Perform a device reset.

```bash
phoenix reset ADDRESS [OPTIONS]

Arguments:
  ADDRESS    Device I2C address (hex)

Options:
  -p, --port INTEGER     USB adapter port [default: 0]
  -s, --speed INTEGER    Bus speed in kHz [default: 400]
  -t, --type [HARD|SOFT|MAC|PERST|GLOBAL_SWRST]
                         Reset type [default: SOFT]
```

**Examples:**

```bash
# Soft reset (default)
phoenix reset 0x50

# Hard reset
phoenix reset 0x50 --type HARD

# PERST reset
phoenix reset 0x50 -t PERST
```

#### `read-reg` -- Read Register

Read a register value.

```bash
phoenix read-reg ADDRESS REGISTER [OPTIONS]

Arguments:
  ADDRESS     Device I2C address (hex)
  REGISTER    Register address (hex)

Options:
  -p, --port INTEGER     USB adapter port [default: 0]
  -s, --speed INTEGER    Bus speed in kHz [default: 400]
  -w, --width [16|32]    Register width in bits [default: 32]
```

**Examples:**

```bash
# Read GLOBAL_PARAM0 (32-bit)
phoenix read-reg 0x50 0x0000

# Read temperature register (16-bit)
phoenix read-reg 0x50 0x0100 -w 16
```

#### `write-reg` -- Write Register

Write a value to a register.

```bash
phoenix write-reg ADDRESS REGISTER VALUE [OPTIONS]

Arguments:
  ADDRESS     Device I2C address (hex)
  REGISTER    Register address (hex)
  VALUE       Value to write (hex)

Options:
  -p, --port INTEGER     USB adapter port [default: 0]
  -s, --speed INTEGER    Bus speed in kHz [default: 400]
  -w, --width [16|32]    Register width in bits [default: 32]
```

**Example:**

```bash
phoenix write-reg 0x50 0x0000 0x12345678
```

#### `serve` -- Start Server

Start the REST API server with optional web dashboard.

```bash
phoenix serve [OPTIONS]

Options:
  -h, --host TEXT        Host to bind [default: 127.0.0.1]
  -p, --port INTEGER     Port to bind [default: 8000]
  --no-ui                API-only mode, no web dashboard
```

**Examples:**

```bash
# Start with dashboard (default)
phoenix serve

# API-only mode
phoenix serve --no-ui

# Bind to all interfaces on port 8080
phoenix serve --host 0.0.0.0 --port 8080
```

---

## 8. REST API Reference

The REST API provides HTTP endpoints for all device operations. When the server is running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Base URL

All API endpoints are prefixed with `/api/`:

```
http://localhost:8000/api/
```

### Endpoints

#### Root

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/` | API information and connected device count |
| `GET` | `/health` | Health check |

#### Discovery & Connection

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/devices/discover` | Discover devices on bus |
| `GET` | `/api/devices/` | List discovered devices |
| `GET` | `/api/devices/{handle}` | Get device info by handle |
| `POST` | `/api/devices/{handle}/connect` | Connect to a device |
| `POST` | `/api/devices/{handle}/disconnect` | Disconnect a device |

#### Status & Monitoring

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/devices/{handle}/status` | Complete device status |
| `GET` | `/api/devices/{handle}/temperature` | Temperature reading |
| `GET` | `/api/devices/{handle}/voltage` | Voltage rail readings |

#### Configuration

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/devices/{handle}/config` | Current configuration |
| `PUT` | `/api/devices/{handle}/config` | Update configuration |
| `POST` | `/api/devices/{handle}/reset` | Reset device |

#### Register Access

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/devices/{handle}/register/{addr}` | Read register |
| `PUT` | `/api/devices/{handle}/register/{addr}` | Write register |

#### Diagnostics

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/devices/{handle}/prbs/start` | Start PRBS test |
| `GET` | `/api/devices/{handle}/prbs/status` | Get PRBS status |
| `POST` | `/api/devices/{handle}/prbs/stop` | Stop PRBS test |
| `GET` | `/api/devices/{handle}/prbs/results` | Get PRBS results |
| `POST` | `/api/devices/{handle}/eye-diagram` | Capture eye diagram |

### Example API Calls

**Discover devices:**

```bash
curl -X POST http://localhost:8000/api/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"transport_type": "i2c", "adapter_port": 0}'
```

**Get device status:**

```bash
curl http://localhost:8000/api/devices/1/status
```

**Update configuration:**

```bash
curl -X PUT http://localhost:8000/api/devices/1/config \
  -H "Content-Type: application/json" \
  -d '{
    "bifurcation_mode": "X8_X8",
    "max_data_rate": "GEN5_32G"
  }'
```

**Read a register:**

```bash
curl http://localhost:8000/api/devices/1/register/0x0000
```

**Write a register:**

```bash
curl -X PUT http://localhost:8000/api/devices/1/register/0x0000 \
  -H "Content-Type: application/json" \
  -d '{"value": "0x12345678", "width": 32}'
```

**Reset device:**

```bash
curl -X POST http://localhost:8000/api/devices/1/reset \
  -H "Content-Type: application/json" \
  -d '{"reset_type": "SOFT"}'
```

**Start PRBS test:**

```bash
curl -X POST http://localhost:8000/api/devices/1/prbs/start \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "PRBS31",
    "data_rate": "GEN5_32G",
    "lanes": [0, 1, 2, 3],
    "sample_count": 1048576
  }'
```

**Capture eye diagram:**

```bash
curl -X POST http://localhost:8000/api/devices/1/eye-diagram \
  -H "Content-Type: application/json" \
  -d '{"lane": 0, "data_rate": "GEN5_32G"}'
```

---

## 9. Python API Reference

The Phoenix Python API allows direct programmatic control of retimer devices from Python scripts and applications.

### 9.1 Device Connection

#### I2C Connection

```python
import asyncio
from phoenix.core.device import RetimerDevice

async def main():
    # Method 1: Factory method with auto-connect
    device = await RetimerDevice.from_i2c(
        address=0x50,
        adapter_port=0,
        bus_speed_khz=400,
    )

    # Method 2: Context manager (auto-disconnect on exit)
    async with await RetimerDevice.from_i2c(address=0x50) as device:
        status = await device.get_status()
        print(f"Temperature: {status.temperature_c} C")

asyncio.run(main())
```

#### UART Connection

```python
import asyncio
from phoenix.core.device import RetimerDevice

async def main():
    device = await RetimerDevice.from_uart(
        port="COM3",          # or "/dev/ttyUSB0" on Linux
        baud_rate=115200,
    )

    try:
        status = await device.get_status()
        print(f"Temperature: {status.temperature_c} C")
    finally:
        await device.disconnect()

asyncio.run(main())
```

### 9.2 Device Discovery

```python
import asyncio
from phoenix.core.discovery import DeviceDiscovery

async def main():
    discovery = DeviceDiscovery()

    # Discover on I2C bus
    devices = await discovery.discover_i2c(
        adapter_port=0,
        addresses=[0x50, 0x51, 0x52, 0x53],
        bus_speed_khz=400,
    )

    for dev in devices:
        print(f"Handle:   {dev.product_handle}")
        print(f"Address:  0x{dev.device_address:02X}")
        print(f"Vendor:   {dev.vendor_id_str}")
        print(f"Device:   {dev.device_id_str}")
        print(f"Firmware: {dev.firmware_version_str}")
        print(f"Max Rate: {dev.max_speed.name}")
        print()

asyncio.run(main())
```

### 9.3 Status Monitoring

```python
async def monitor_device(device):
    status = await device.get_status()

    # Temperature
    print(f"Temperature: {status.temperature_c} C")
    print(f"Healthy: {status.is_healthy}")

    # Voltages
    v = status.voltage_info
    print(f"DVDD1:  {v.dvdd1_mv} mV")
    print(f"DVDD2:  {v.dvdd2_mv} mV")
    print(f"DVDD3:  {v.dvdd3_mv} mV")
    print(f"DVDD4:  {v.dvdd4_mv} mV")
    print(f"DVDD5:  {v.dvdd5_mv} mV")
    print(f"DVDD6:  {v.dvdd6_mv} mV")
    print(f"DVDDIO: {v.dvddio_mv} mV")

    # Port A status
    ppa = status.ppa_status
    print(f"PPA LTSSM: {ppa.current_ltssm_state.name}")
    print(f"PPA Speed: {ppa.current_link_speed.name}")
    print(f"PPA Width: x{ppa.current_link_width}")
    print(f"PPA Up: {ppa.is_link_up}")

    # Port B status
    ppb = status.ppb_status
    print(f"PPB LTSSM: {ppb.current_ltssm_state.name}")
    print(f"PPB Speed: {ppb.current_link_speed.name}")
    print(f"PPB Width: x{ppb.current_link_width}")
    print(f"PPB Up: {ppb.is_link_up}")

    # Interrupts
    intr = status.interrupt_status
    print(f"Global IRQ: {intr.global_interrupt}")
    print(f"EQ Error: {intr.eq_phase_error}")
    print(f"PHY Error: {intr.phy_phase_error}")
    print(f"Internal Error: {intr.internal_error}")

    # Per-lane status (via port)
    for lane in ppa.lane_status:
        print(f"  Lane {lane.lane_number}: "
              f"RX={lane.rx_detect} "
              f"TX_EQ={lane.tx_eq_done} "
              f"RX_EQ={lane.rx_eq_done}")
```

### 9.4 Configuration

```python
from phoenix.models.configuration import ConfigurationUpdate
from phoenix.protocol.enums import BifurcationMode, MaxDataRate, ClockingMode

async def configure_device(device):
    # Read current configuration
    config = await device.get_configuration()
    print(f"Current bifurcation: {config.bifurcation_mode.name}")
    print(f"Current data rate: {config.max_data_rate.name}")
    print(f"Current clocking: {config.clocking_mode.name}")

    # Update configuration (partial update)
    update = ConfigurationUpdate(
        bifurcation_mode=BifurcationMode.X8_X8,
        max_data_rate=MaxDataRate.GEN5_32G,
        clocking_mode=ClockingMode.COMMON_SSC,
    )
    await device.set_configuration(update)
    print("Configuration applied.")
```

### 9.5 Register Access

```python
async def register_operations(device):
    # Read a 32-bit register
    value = await device.read_register(0x0000)
    print(f"GLOBAL_PARAM0: 0x{value:08X}")

    # Read a 16-bit register
    value = await device.read_register(0x0100, width=16)
    print(f"TEMPERATURE: 0x{value:04X}")

    # Write a 32-bit register
    await device.write_register(0x0000, 0x12345678)

    # Use RegisterField for field extraction
    from phoenix.protocol.register_maps import GLOBAL_PARAM0
    raw = await device.read_register(0x0000)
    for field in GLOBAL_PARAM0.fields:
        fval = field.extract(raw)
        print(f"  {field.name}: 0x{fval:X} ({field.description})")
```

### 9.6 PRBS Testing

```python
from phoenix.models.diagnostics import PRBSConfig
from phoenix.protocol.enums import PRBSPattern, MaxDataRate

async def run_prbs_test(device):
    config = PRBSConfig(
        pattern=PRBSPattern.PRBS31,
        data_rate=MaxDataRate.GEN5_32G,
        lanes=list(range(16)),    # All 16 lanes
        generator_enable=True,
        checker_enable=True,
        sample_count=0x100000,
    )

    # Start test
    await device.start_prbs(config)
    print("PRBS test started.")

    # Wait for test to complete, then get results
    results = await device.get_prbs_results()

    for r in results:
        print(f"Lane {r.lane_number}: "
              f"Bits={r.bit_count:,} "
              f"Errors={r.error_count:,} "
              f"BER={r.ber_string} "
              f"Sync={r.sync_acquired} "
              f"Complete={r.test_complete}")

    # Stop test
    await device.stop_prbs()
```

### 9.7 Eye Diagram

```python
from phoenix.protocol.enums import MaxDataRate

async def capture_eye(device):
    result = await device.capture_eye_diagram(
        lane=0,
        data_rate=MaxDataRate.GEN5_32G,
    )

    print(f"Lane {result.lane_number}, Valid: {result.capture_valid}")

    if result.middle_eye:
        m = result.middle_eye
        print(f"Middle Eye:")
        print(f"  Left: {m.left_margin_mui} mUI")
        print(f"  Right: {m.right_margin_mui} mUI")
        print(f"  Upper: {m.upper_margin_mv} mV")
        print(f"  Lower: {m.lower_margin_mv} mV")
        print(f"  H Opening: {m.horizontal_opening_mui} mUI")
        print(f"  V Opening: {m.vertical_opening_mv} mV")

    # Gen6 PAM4: lower and upper eyes
    if result.lower_eye:
        print(f"Lower Eye (Gen6 PAM4):")
        print(f"  H Opening: {result.lower_eye.horizontal_opening_mui} mUI")
    if result.upper_eye:
        print(f"Upper Eye (Gen6 PAM4):")
        print(f"  H Opening: {result.upper_eye.horizontal_opening_mui} mUI")
```

### 9.8 Device Reset

```python
from phoenix.protocol.enums import ResetType

async def reset_device(device):
    # Soft reset (preserves sticky registers)
    await device.reset(ResetType.SOFT)

    # Hard reset (full chip reset)
    await device.reset(ResetType.HARD)

    # PERST (PCIe fundamental reset)
    await device.reset(ResetType.PERST)
```

### 9.9 Error Handling

```python
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
        print("Device not found at the specified address.")
    except TransportError as e:
        print(f"Communication error: {e}")
    except TimeoutError as e:
        print(f"Operation timed out: {e}")
    except PhoenixError as e:
        print(f"Phoenix error: {e}")
```

**Exception hierarchy:**

```
PhoenixError                    # Base exception
  +-- DeviceNotFoundError       # Device not found at address
  +-- TransportError            # I2C/UART communication failure
  +-- TimeoutError              # Operation timed out
```

---

## 10. Configuration Reference

### 10.1 Bifurcation Modes

The BCM85667 supports 33 bifurcation modes that subdivide the 16 lanes into different link configurations. The mode determines how lanes are grouped into PCIe links.

| Mode | Enum Name | Description | Total Lanes |
|------|-----------|-------------|-------------|
| 0 | `X16` | Single x16 link | 16 |
| 1 | `X8` | Single x8 link | 8 |
| 2 | `X4` | Single x4 link | 4 |
| 3 | `X8_X8` | Two x8 links | 16 |
| 4 | `X8_X4_X4` | One x8 + two x4 links | 16 |
| 5 | `X4_X4_X8` | Two x4 + one x8 links | 16 |
| 6 | `X4_X4_X4_X4` | Four x4 links | 16 |
| 7 | `X2_X2_X2_X2_X2_X2_X2_X2` | Eight x2 links | 16 |
| 8 | `X8_X4_X2_X2` | x8 + x4 + two x2 | 16 |
| 9 | `X8_X2_X2_X4` | x8 + two x2 + x4 | 16 |
| 10 | `X2_X2_X4_X8` | Two x2 + x4 + x8 | 16 |
| 11 | `X4_X2_X2_X8` | x4 + two x2 + x8 | 16 |
| 12 | `X2_X2_X2_X2_X8` | Four x2 + x8 | 16 |
| 13 | `X8_X2_X2_X2_X2` | x8 + four x2 | 16 |
| 14 | `X2_X2_X4_X4_X4` | Two x2 + three x4 | 16 |
| 15 | `X4_X2_X2_X4_X4` | x4 + two x2 + two x4 | 16 |
| 16 | `X4_X4_X2_X2_X4` | Two x4 + two x2 + x4 | 16 |
| 17 | `X4_X4_X4_X2_X2` | Three x4 + two x2 | 16 |
| 18 | `X2_X2_X2_X2_X4_X4` | Four x2 + two x4 | 16 |
| 19 | `X2_X2_X4_X2_X2_X4` | Two x2 + x4 + two x2 + x4 | 16 |
| 20 | `X4_X2_X2_X2_X2_X4` | x4 + four x2 + x4 | 16 |
| 21 | `X2_X2_X4_X4_X2_X2` | Two x2 + two x4 + two x2 | 16 |
| 22 | `X4_X2_X2_X4_X2_X2` | x4 + two x2 + x4 + two x2 | 16 |
| 23 | `X4_X4_X2_X2_X2_X2` | Two x4 + four x2 | 16 |
| 24 | `X2_X2_X2_X2_X2_X2_X4` | Six x2 + x4 | 16 |
| 25 | `X2_X2_X2_X2_X4_X2_X2` | Four x2 + x4 + two x2 | 16 |
| 26 | `X2_X2_X4_X2_X2_X2_X2` | Two x2 + x4 + four x2 | 16 |
| 27 | `X4_X2_X2_X2_X2_X2_X2` | x4 + six x2 | 16 |
| 28 | `X4_X4` | Two x4 links | 8 |
| 29 | `X2_X2_X4` | Two x2 + x4 | 8 |
| 30 | `X4_X2_X2` | x4 + two x2 | 8 |
| 31 | `X2_X2_X2_X2` | Four x2 links | 8 |
| 32 | `X2_X2` | Two x2 links | 4 |

### 10.2 Data Rates

| Enum Name | Speed | PCIe Generation | Encoding |
|-----------|-------|-----------------|----------|
| `GEN1_2P5G` | 2.5 GT/s | Gen1 | 8b/10b |
| `GEN2_5G` | 5.0 GT/s | Gen2 | 8b/10b |
| `GEN3_8G` | 8.0 GT/s | Gen3 | 128b/130b |
| `GEN4_16G` | 16.0 GT/s | Gen4 | 128b/130b |
| `GEN5_32G` | 32.0 GT/s | Gen5 | 128b/130b |
| `GEN6_64G` | 64.0 GT/s | Gen6 | 1b/1b (PAM4) |

**Note:** The `max_data_rate` configuration sets the **maximum** rate the retimer will negotiate. The actual link speed depends on both endpoints and channel quality.

### 10.3 Clocking Modes

| Enum Name | Description | Use Case |
|-----------|-------------|----------|
| `COMMON_WO_SSC` | Common clock without Spread Spectrum Clocking | Standard server/desktop platforms |
| `COMMON_SSC` | Common clock with SSC | Platforms requiring SSC for EMI compliance |
| `SRNS_WO_SSC` | Separate Reference, No SSC | Systems with independent reference clocks |
| `SRIS_SSC` | Separate Reference, Independent SSC with SSC | Hot-plug and add-in card applications |
| `SRIS_WO_SSC` | Separate Reference, Independent SSC without SSC | Debug and testing only |
| `SRIS_WO_SSC_LL` | Separate Reference, Independent SSC without SSC (low latency) | Low-latency SRIS applications |

**Selecting the correct clocking mode:**

- Most server platforms use **COMMON_WO_SSC** or **COMMON_SSC**
- Add-in cards and hot-plug applications typically use **SRIS_SSC**
- Use **SRNS_WO_SSC** only when the system has separate, frequency-locked reference clocks
- **SRIS_WO_SSC** is for debug purposes only and should not be used in production

### 10.4 Reset Types

| Enum Name | Description | Preserves |
|-----------|-------------|-----------|
| `HARD` | Full chip reset -- resets all registers and state | Nothing |
| `SOFT` | Soft reset -- resets most state but preserves sticky registers | Sticky configuration registers |
| `MAC` | Global MAC software reset -- resets the MAC layer | PHY configuration |
| `PERST` | PCIe fundamental reset (PERST#) | Hardware strapping configuration |
| `GLOBAL_SWRST` | Toggle global software link reset | Configuration registers |

**When to use each reset type:**

- **SOFT**: General-purpose reset for re-initializing the retimer without losing configuration
- **HARD**: When you need a complete reset to factory defaults
- **PERST**: Simulates a PCIe bus reset; use when testing link training from scratch
- **MAC**: Use when only the MAC layer needs to be reset (e.g., after configuration changes)
- **GLOBAL_SWRST**: Use to force link re-training without resetting configuration

### 10.5 Port Orientation

| Enum Name | Description |
|-----------|-------------|
| `STATIC` | PPA and PPB are predefined by hardware strapping |
| `DYNAMIC` | PPA and PPB are assigned dynamically based on which side trains first |

Most configurations use **STATIC** orientation. Use **DYNAMIC** when the retimer is placed in a system where either port could be upstream.

### 10.6 Interrupt Configuration

The retimer supports four interrupt sources, each individually maskable:

| Interrupt | Description | Typical Cause |
|-----------|-------------|---------------|
| Global Interrupt | Master interrupt enable | Any enabled sub-interrupt |
| EQ Phase Error | Equalization phase error | Link training failure during EQ phase |
| PHY Phase Error | PHY-level phase error | Signal integrity problem |
| Internal Error | Internal device error | PLL unlock, CDR unlock, WDT timeout, SMBus error |

**Internal error sub-sources:**

| Sub-Source | Description |
|------------|-------------|
| TX PLL Unlock | Transmit PLL lost lock |
| US RX CDR Unlock | Upstream receiver CDR lost lock |
| DS RX CDR Unlock | Downstream receiver CDR lost lock |
| CMU PLL Unlock | Common PLL lost lock |
| PLL SSC Unlock | SSC PLL lost lock |
| WDT Timeout | Watchdog timer expired |
| SMBus Access Error | SMBus communication error |

### 10.7 TX Equalization Coefficients

TX equalization can be configured per lane, per PCIe generation (Gen3--Gen6). Each lane's TX EQ has the following parameters:

| Parameter | Range | Description |
|-----------|-------|-------------|
| `tx_preset` | 0--15 | TX preset number (PCIe-defined) |
| `tx_preset_req` | 0--15 | TX preset request to link partner |
| `tx_pre_cursor` | 0--63 | Pre-cursor emphasis |
| `tx_post_cursor` | 0--63 | Post-cursor emphasis |
| `tx_cursor` | 0--63 | Main cursor coefficient |
| `tx_precode_req` | bool | TX precoding request (Gen5+ only) |
| `tx_preset_sel` | bool | Use preset (False) or manual coefficients (True) |
| `tx_pre2_cursor` | 0--63 | Pre2-cursor emphasis (Gen6 only) |

**Note:** When `tx_preset_sel` is False (default), the retimer uses the standard PCIe preset values. Set it to True only when you need to manually specify cursor coefficients for advanced signal integrity tuning.

---

## 11. Diagnostics Guide

### 11.1 PRBS Testing

#### Overview

PRBS (Pseudo-Random Bit Sequence) testing is the primary method for verifying signal integrity on individual lanes. The retimer generates a known PRBS pattern on the TX side and checks the received pattern on the RX side, counting any bit errors.

#### Supported Patterns

| Pattern | Polynomial Length | Use Case |
|---------|-------------------|----------|
| PRBS7 | 2^7 - 1 = 127 bits | Quick test, low-order pattern |
| PRBS9 | 2^9 - 1 = 511 bits | Short pattern testing |
| PRBS10 | 2^10 - 1 = 1023 bits | Medium pattern |
| PRBS11 | 2^11 - 1 = 2047 bits | Medium pattern |
| PRBS13 | 2^13 - 1 = 8191 bits | Standard pattern |
| PRBS15 | 2^15 - 1 = 32767 bits | Common test pattern |
| PRBS20 | 2^20 - 1 | Extended pattern |
| PRBS23 | 2^23 - 1 | Standard for high-speed serial |
| PRBS31 | 2^31 - 1 | Industry standard for PCIe/SerDes |
| PRBS49 | 2^49 - 1 | Extended for Gen5+ |
| PRBS58 | 2^58 - 1 | Extended for Gen6 (PAM4) |

#### Recommended Test Procedure

1. **Select pattern**: Use **PRBS31** for standard testing. Use **PRBS58** for Gen6 PAM4 testing.
2. **Select data rate**: Match the target PCIe generation speed.
3. **Select lanes**: Enable all lanes you want to test. Typically all 16 for a full link test.
4. **Set sample count**: Use at least `0x100000` (1M samples) for a meaningful BER measurement. For production testing, use `0x10000000` or higher.
5. **Start the test**: Click "Start PRBS" or call `device.start_prbs(config)`.
6. **Wait for completion**: The test runs until the sample count is reached on each lane.
7. **Read results**: Click "Get Results" or call `device.get_prbs_results()`.

#### Interpreting Results

| BER | Assessment | Action |
|-----|------------|--------|
| < 1e-15 | Excellent | No errors; link is clean |
| < 1e-12 | Good | Within PCIe specification |
| 1e-12 to 1e-9 | Marginal | Investigate signal integrity |
| > 1e-9 | Failing | Check cabling, connectors, and board layout |

- **Sync Acquired = No**: The checker could not lock onto the PRBS pattern. This indicates a severe signal integrity issue or incorrect test configuration.
- **Test Complete = No**: The test is still running or was interrupted before reaching the sample count.

### 11.2 Eye Diagram Capture

#### Overview

Eye diagram capture measures the signal margin at the receiver by sampling the signal at various timing and voltage offsets. The result quantifies how much timing and voltage margin exists before errors occur.

#### Margin Values

| Metric | Unit | Description |
|--------|------|-------------|
| Left Margin | mUI | Timing margin to the left of center |
| Right Margin | mUI | Timing margin to the right of center |
| Upper Margin | mV | Voltage margin above center |
| Lower Margin | mV | Voltage margin below center |
| H Opening | mUI | Total horizontal eye opening (Left + Right) |
| V Opening | mV | Total vertical eye opening (Upper + Lower) |

**mUI** = milli-Unit Interval. 1000 mUI = 1 UI = 1 bit period.

#### Gen6 PAM4 Eyes

At Gen6 (64 GT/s), PCIe uses PAM4 signaling with 4 voltage levels. This creates three eye openings:

- **Upper Eye**: Between the top two voltage levels
- **Middle Eye**: Between the middle two voltage levels
- **Lower Eye**: Between the bottom two voltage levels

All three eyes are reported separately. Gen1--Gen5 (NRZ signaling) only have a middle eye.

#### Recommended Margins

| Generation | Minimum H Opening | Minimum V Opening |
|------------|-------------------|-------------------|
| Gen3 (8 GT/s) | 200 mUI | 80 mV |
| Gen4 (16 GT/s) | 150 mUI | 60 mV |
| Gen5 (32 GT/s) | 100 mUI | 40 mV |
| Gen6 (64 GT/s) | 80 mUI | 30 mV |

These are approximate guidelines. Refer to the PCIe specification for exact requirements.

### 11.3 Embedded Logic Analyzer (ELA)

The ELA captures protocol-level signal transitions for debugging link training and state machine behavior. It supports up to 8 trigger signals with configurable trigger types (rising edge, falling edge, or pattern match).

**ELA Types:**

| Type | Description |
|------|-------------|
| Lane Pipe A | Capture on a specific Lane Pipe A signal |
| Lane Pipe B | Capture on a specific Lane Pipe B signal |
| Pseudo Port | Capture on a pseudo port signal |
| Pseudo Port A | Capture on PPA-specific signal |
| Pseudo Port B | Capture on PPB-specific signal |

**Trigger Positions:**

| Position | Description |
|----------|-------------|
| 0% | Trigger at the beginning of the capture buffer |
| 25% | Trigger at 25% into the buffer (75% pre-trigger) |
| 50% | Trigger at center (50% pre/post) |
| 75% | Trigger at 75% into the buffer (25% post-trigger) |

**Note:** ELA capture and configuration require firmware support and are not yet implemented in the current release.

### 11.4 Broadcom Embedded Logic Analyzer (BELA)

BELA is a lane-level logic analyzer that captures PHY-layer signal transitions on a single lane. It is useful for debugging equalization, speed negotiation, and lane-level issues.

**Trigger Types:**

| Type | Description |
|------|-------------|
| Live Datarate | Trigger at the current operating data rate |
| Datarate Entry | Trigger when the lane transitions to the target rate |
| Datarate Exit | Trigger when the lane transitions away from the target rate |
| Datarate Entry/Exit | Trigger on both entry and exit |

**BELA Status Values:**

| Status | Description |
|--------|-------------|
| BUSY | Capture is in progress, waiting for trigger |
| TRIGGERED | Trigger condition was met, data captured |
| ABORTED | Capture was aborted (manually or by error) |
| INVALID | Invalid state (no capture configured) |

**Note:** BELA captures require firmware support and may impact link performance. Not yet implemented in the current release.

### 11.5 Link Channel Analysis Tool (LinkCAT)

LinkCAT characterizes the PCIe channel by measuring insertion loss at the symbol rate. This helps determine if the physical channel (PCB traces, connectors, cables) meets PCIe specifications.

**Modes:**

| Mode | Description |
|------|-------------|
| LP TX | Local port transmit mode |
| Loopback | Loopback mode for self-test |
| Pre-RX | Pre-receiver measurement mode |
| RX Measure | Receiver measurement mode |

**Result Fields:**

| Field | Description |
|-------|-------------|
| Insertion Loss (dB) | Channel insertion loss at symbol rate |
| Fit Factor | Calculation accuracy indicator |
| Clipped | Data was clipped during measurement |
| Error/Warning | Error or warning occurred |

**Note:** LinkCAT requires the link to be in a specific state before running. Not yet implemented in the current release.

---

## 12. Register Map Reference

The BCM85667 register space is organized into blocks:

| Block | Base Address | Description |
|-------|-------------|-------------|
| Retimer Config | 0x0000 | Global configuration registers |
| XAGENT | 0x4000 | Device information and firmware |
| PPA | 0x8000 | Pseudo Port A status and control |
| PPB | 0xC000 | Pseudo Port B status and control |

### Named Registers

#### RETIMER_CFG_GLOBAL_PARAM0 (0x0000)

Global Parameter Register 0 -- primary device configuration.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| PROFILE | [2:0] | 3 | Profile revision |
| BIFURCATION | [12:7] | 6 | Lane bifurcation mode |
| EEPROM_DATA_VAL | [14:13] | 2 | EEPROM data valid indicator |
| AUTOINC | [15] | 1 | SMBus autoincrement support |
| CLK_MODE | [18:16] | 3 | Clocking mode |
| ENH_LINK_BEHAV | [20:18] | 3 | Enhanced link behavior |
| EEPROM_TIMEOUT | [23:21] | 3 | EEPROM timeout |
| MAX_DATA_RATE | [26:24] | 3 | Maximum data rate |
| SRIS_LINK_PAYLOAD_SIZE | [30:28] | 3 | SRIS link payload size |
| PORT_ORIEN_METHOD | [31] | 1 | Port orientation method |

#### RETIMER_CFG_GLOBAL_PARAM1 (0x0004)

Global Parameter Register 1 -- device identification.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| REVISION_ID | [7:0] | 8 | Device revision ID |
| DEVICE_ID | [15:8] | 8 | Device ID |
| VENDOR_ID | [31:16] | 16 | Vendor ID (Broadcom: 0x14E4) |

#### RETIMER_CFG_GLOBAL_INTR (0x0008)

Global Interrupt and Mask Register.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| INTR_STS | [0] | 1 | Global interrupt status |
| EQ_PHASE_ERR_STS | [1] | 1 | EQ phase error status |
| PHY_PHASE_ERR_STS | [2] | 1 | PHY phase error status |
| RTMR_INT_ERR_STS | [3] | 1 | Retimer internal error status |
| INTR_EN | [16] | 1 | Global interrupt enable |
| EQ_PHASE_ERR_EN | [17] | 1 | EQ phase error enable |
| PHY_PHASE_ERR_EN | [18] | 1 | PHY phase error enable |
| RTMR_INT_ERR_EN | [19] | 1 | Retimer internal error enable |

#### RETIMER_CFG_RESET_CTRL (0x0010)

Reset Control Register.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| HARD_RESET | [0] | 1 | Hard reset (write 1 to trigger) |
| SOFT_RESET | [1] | 1 | Soft reset (write 1 to trigger) |
| MAC_RESET | [2] | 1 | MAC reset (write 1 to trigger) |
| PERST | [3] | 1 | PERST reset (write 1 to trigger) |
| GLOBAL_SWRST | [4] | 1 | Global software reset (write 1 to trigger) |

#### RETIMER_TEMPERATURE (0x0100)

Temperature Reading Register.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| TEMPERATURE | [15:0] | 16 | Temperature in degrees Celsius |
| VALID | [31] | 1 | Temperature reading valid |

#### Voltage Registers

| Register | Address | Description |
|----------|---------|-------------|
| RETIMER_VOLTAGE_DVDD1 | 0x0104 | DVDD1 voltage in millivolts |
| RETIMER_VOLTAGE_DVDD2 | 0x0108 | DVDD2 voltage in millivolts |
| RETIMER_VOLTAGE_DVDD3 | 0x010C | DVDD3 voltage in millivolts |
| RETIMER_VOLTAGE_DVDD4 | 0x0110 | DVDD4 voltage in millivolts |
| RETIMER_VOLTAGE_DVDD5 | 0x0114 | DVDD5 voltage in millivolts |
| RETIMER_VOLTAGE_DVDD6 | 0x0118 | DVDD6 voltage in millivolts |
| RETIMER_VOLTAGE_DVDDIO | 0x011C | DVDDIO voltage in millivolts |

#### XAGENT_XAGENT_INFO_0 (0x4000)

XAGENT Info Register 0 -- product information.

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| FW_VERSION | [15:0] | 16 | Firmware version (major.minor) |
| PRODUCT_ID | [31:16] | 16 | Product ID |

#### Port LTSSM State Registers

| Register | Address | Port |
|----------|---------|------|
| PPA_LTSSM_STATE | 0x8000 | Pseudo Port A |
| PPB_LTSSM_STATE | 0xC000 | Pseudo Port B |

Both registers share the same field layout:

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| CURRENT_STATE | [7:0] | 8 | Current LTSSM state (see Appendix A) |
| LINK_SPEED | [11:8] | 4 | Current link speed |
| LINK_WIDTH | [16:12] | 5 | Current link width |
| FORWARDING_MODE | [17] | 1 | Forwarding mode enabled |

### TX Coefficient Registers

TX equalization coefficient registers are organized per generation and per lane:

| Generation | Base Address | Lane Stride |
|------------|-------------|-------------|
| Gen3 | 0x0200 | 0x10 (16 bytes) |
| Gen4 | 0x0280 | 0x10 |
| Gen5 | 0x0300 | 0x10 |
| Gen6 | 0x0380 | 0x10 |

**Address calculation:** `base + (lane * 0x10) + offset`

### Error Statistics Registers

Per-lane error statistics registers:

| Base Address | Lane Stride |
|-------------|-------------|
| 0x0500 | 0x20 (32 bytes) |

**Address calculation:** `0x0500 + (lane * 0x20) + (error_type * 4)`

---

## 13. Troubleshooting

### Device Not Found

**Symptom:** `phoenix discover` finds no devices, or the dashboard scan returns empty results.

**Solutions:**

1. **Check physical connections**: Verify I2C wiring (SDA, SCL, GND) or UART wiring (TX, RX, GND).
2. **Check power**: Ensure the retimer board is powered.
3. **Verify adapter**: Check that the USB adapter is recognized by the OS.
4. **Scan all addresses**: Try scanning the full range: `phoenix discover -a 0x50 -a 0x51 -a 0x52 -a 0x53 -a 0x54 -a 0x55 -a 0x56 -a 0x57`
5. **Lower bus speed**: Try 100 kHz: `phoenix discover --speed 100`
6. **Check pull-ups**: Ensure 4.7k ohm pull-up resistors are on SDA and SCL.

### Communication Errors

**Symptom:** Operations fail with TransportError or timeout messages.

**Solutions:**

1. **PEC failures**: May indicate signal integrity issues on the I2C bus. Check wiring length and add pull-ups.
2. **Timeouts**: The device may be busy (e.g., during reset). Wait and retry.
3. **I2C NAK**: The device address may be wrong, or the device is in reset.
4. **Bus contention**: Ensure no other master is driving the I2C bus.

### Dashboard Not Loading

**Symptom:** `phoenix serve` starts but the browser shows a blank page or connection error.

**Solutions:**

1. **Check URL**: Navigate to `http://localhost:8000` (not `/api/`).
2. **Check port**: Ensure port 8000 is not in use by another application. Use `--port 8080` to try a different port.
3. **Check firewall**: Ensure the local firewall allows connections on the server port.
4. **Check NiceGUI**: Ensure NiceGUI is installed: `pip install nicegui>=2.0`

### Temperature Reads as 0 C

**Symptom:** The temperature gauge always shows 0 degrees.

**Solutions:**

1. **Check VALID bit**: Read register 0x0100 and verify bit 31 is set. If not, the sensor may not be calibrated.
2. **Wait after power-on**: The temperature sensor may need a few seconds to stabilize after power-up.
3. **Firmware check**: Ensure firmware is loaded and running (check firmware version via `phoenix status`).

### Link Not Training (LTSSM Stuck in DETECT)

**Symptom:** Port status shows DETECT state and link is DOWN.

**Solutions:**

1. **Check physical connection**: Ensure PCIe connector is fully seated.
2. **Check endpoint**: The other end of the link must be present and powered.
3. **Check bifurcation**: Ensure the bifurcation mode matches the physical connection.
4. **Check data rate**: Try limiting to a lower data rate (e.g., GEN3_8G) to isolate speed issues.
5. **Reset**: Try a soft reset: `phoenix reset 0x50 --type SOFT`
6. **Check clocking**: Ensure the clocking mode matches the system configuration.

### PRBS Test Shows All Errors

**Symptom:** Every lane reports high BER or sync not acquired.

**Solutions:**

1. **Verify loopback**: PRBS testing requires either a loopback connection or a link partner that also generates the same PRBS pattern.
2. **Match pattern**: Both ends must use the same PRBS polynomial.
3. **Match data rate**: Both ends must be configured for the same data rate.
4. **Check lanes**: Ensure the tested lanes are physically connected.

### Permission Errors (Linux)

**Symptom:** "Permission denied" when accessing USB adapter or serial port.

**Solution:**

```bash
# For serial ports
sudo usermod -a -G dialout $USER

# For USB adapters (FTDI)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-ftdi.rules
sudo udevadm control --reload-rules

# Log out and log back in for changes to take effect
```

---

## 14. Appendix A: LTSSM State Reference

The Link Training and Status State Machine (LTSSM) controls PCIe link initialization and operation.

### Reset/Exit/Startup States

| Value | State | Description |
|-------|-------|-------------|
| 0x00 | DETECT | Receiver detection (initial state after reset) |
| 0x03 | RATE_CHANGE | Speed negotiation in progress |

### Forwarding States

| Value | State | Description |
|-------|-------|-------------|
| 0x04 | FWD_FORWARDING | Normal forwarding operation (link is up and active) |
| 0x05 | FWD_HOT_RESET | Hot reset forwarding |
| 0x06 | FWD_DISABLE | Link disabled forwarding |
| 0x07 | FWD_LOOPBACK | Loopback mode forwarding |
| 0x08 | FWD_CPL_RCV | Compliance receive mode |
| 0x09 | FWD_ENTER_CPL | Entering compliance mode |
| 0x0A | FWD_PM_L1_1 | Power management L1.1 state |

### Execution States

| Value | State | Description |
|-------|-------|-------------|
| 0x10 | EXE_CLB_ENTRY | Calibration entry |
| 0x11 | EXE_CLB_PATTERN | Calibration pattern |
| 0x12 | EXE_CLB_EXIT | Calibration exit |
| 0x14 | EXE_EQ_PH2_ACTIVE | EQ Phase 2 Active (retimer adjusting) |
| 0x15 | EXE_EQ_PH2_PASSIVE | EQ Phase 2 Passive (retimer forwarding) |
| 0x16 | EXE_EQ_PH3_ACTIVE | EQ Phase 3 Active |
| 0x17 | EXE_EQ_PH3_PASSIVE | EQ Phase 3 Passive |
| 0x18 | EXE_EQ_FORCE_TIMEOUT | EQ forced timeout |
| 0x1C | EXE_SLAVE_LPBK_ENTRY | Slave loopback entry |
| 0x1D | EXE_SLAVE_LPBK_ACTIVE | Slave loopback active |
| 0x1E | EXE_SLAVE_LPBK_EXIT | Slave loopback exit |

### Normal Operation

A healthy link should show **FWD_FORWARDING (0x04)** as the LTSSM state. Any other state indicates the link is in training, reset, or error recovery.

---

## 15. Appendix B: Error Statistics Reference

Per-lane error statistics track various signal integrity and protocol errors.

| Error Type | Description | Typical Cause |
|------------|-------------|---------------|
| Invalid Symbol | Invalid 8b/10b or 128b/130b symbol received | Signal integrity issue, crosstalk |
| Symbol Lock Loss | Receiver lost symbol lock | Severe signal degradation |
| Elastic Buffer Over/Underflow | Elastic buffer overflow or underflow | Clock frequency mismatch |
| Lane-to-Lane Deskew | Lane deskew error | Physical trace length mismatch |
| Block Alignment Loss | Loss of 128b/130b block alignment | Signal quality issue (Gen3+) |
| Block Header Error | Invalid block header received | Signal quality issue (Gen3+) |
| SOS Block Error | SOS (Skip Ordered Set) block error | Elastic buffer timing issue |

---

## 16. Appendix C: PRBS Pattern Reference

| Pattern | Polynomial | Period (bits) | Typical Use |
|---------|-----------|---------------|-------------|
| PRBS7 | x^7 + x^6 + 1 | 127 | Quick lane check |
| PRBS9 | x^9 + x^5 + 1 | 511 | Short pattern |
| PRBS10 | x^10 + x^7 + 1 | 1,023 | Medium test |
| PRBS11 | x^11 + x^9 + 1 | 2,047 | Medium test |
| PRBS13 | x^13 + x^12 + x^2 + x + 1 | 8,191 | Standard test |
| PRBS15 | x^15 + x^14 + 1 | 32,767 | Standard for BERT |
| PRBS20 | x^20 + x^3 + 1 | 1,048,575 | Extended test |
| PRBS23 | x^23 + x^18 + 1 | 8,388,607 | High-speed serial standard |
| PRBS31 | x^31 + x^28 + 1 | 2,147,483,647 | PCIe/SerDes industry standard |
| PRBS49 | x^49 + x^40 + 1 | ~5.6 x 10^14 | Gen5+ extended |
| PRBS58 | x^58 + x^39 + 1 | ~2.9 x 10^17 | Gen6 PAM4 testing |

**Recommendation:** Use **PRBS31** for Gen1--Gen5 testing and **PRBS58** for Gen6 (PAM4) testing.

---

## Document Information

| | |
|---|---|
| **Product** | Phoenix -- Broadcom Vantage PCIe Gen6 Retimer API |
| **Version** | 0.1.0 |
| **Date** | 2026 |
| **Author** | Serial Cables |
| **Website** | [serialcables.com](https://serialcables.com) |

---

Copyright 2024 Serial Cables. All rights reserved.

Based on the Broadcom Vantage VNT6_0_0_2 SDK. Built with FastAPI, NiceGUI, Click, and Pydantic.
