"""
Command-line interface for Phoenix Retimer API.

Provides CLI access to device discovery, configuration, status, and diagnostics.
"""

import asyncio
import sys
from typing import Optional

import click

from phoenix.core.discovery import DeviceDiscovery
from phoenix.core.device import RetimerDevice
from phoenix.models.configuration import ConfigurationUpdate
from phoenix.protocol.enums import (
    BifurcationMode,
    ClockingMode,
    MaxDataRate,
    PortOrientation,
    ResetType,
)
from phoenix.utils.logging import setup_logging


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, debug):
    """Phoenix - Broadcom Vantage PCIe Gen6 Retimer CLI."""
    ctx.ensure_object(dict)
    setup_logging(level="DEBUG" if debug else "INFO")


@cli.command()
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--address", "-a", multiple=True, type=str, help="I2C address(es) to scan (hex)")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
def discover(port: int, address: tuple, speed: int):
    """Discover retimer devices on I2C bus."""
    async def _discover():
        discovery = DeviceDiscovery()

        addresses = None
        if address:
            addresses = [int(a, 16) for a in address]

        click.echo(f"Scanning I2C bus (port={port}, speed={speed}kHz)...")
        devices = await discovery.discover_i2c(
            adapter_port=port,
            addresses=addresses,
            bus_speed_khz=speed,
        )

        if not devices:
            click.echo("No devices found.")
            return

        click.echo(f"\nFound {len(devices)} device(s):\n")
        for device in devices:
            click.echo(f"  Handle:    {device.product_handle}")
            click.echo(f"  Address:   0x{device.device_address:02X}")
            click.echo(f"  Vendor:    {device.vendor_id_str}")
            click.echo(f"  Device:    {device.device_id_str}")
            click.echo(f"  Revision:  {device.revision_id}")
            click.echo(f"  Firmware:  {device.firmware_version_str}")
            click.echo(f"  Max Speed: {device.max_speed.name}")
            click.echo()

    run_async(_discover())


@cli.command()
@click.argument("address", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
def status(address: str, port: int, speed: int):
    """Get device status."""
    async def _status():
        addr = int(address, 16) if address.startswith("0x") else int(address)

        click.echo(f"Connecting to device at 0x{addr:02X}...")
        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            status = await device.get_status()

            click.echo("\n=== Device Status ===\n")
            click.echo(f"Temperature:     {status.temperature_c}°C")
            click.echo(f"Firmware:        {device.device_info.firmware_version_str}")
            click.echo(f"Healthy:         {'Yes' if status.is_healthy else 'No'}")

            click.echo("\n--- Voltages ---")
            click.echo(f"  DVDD1:   {status.voltage_info.dvdd1_mv} mV")
            click.echo(f"  DVDD2:   {status.voltage_info.dvdd2_mv} mV")
            click.echo(f"  DVDD3:   {status.voltage_info.dvdd3_mv} mV")
            click.echo(f"  DVDD4:   {status.voltage_info.dvdd4_mv} mV")
            click.echo(f"  DVDD5:   {status.voltage_info.dvdd5_mv} mV")
            click.echo(f"  DVDD6:   {status.voltage_info.dvdd6_mv} mV")
            click.echo(f"  DVDDIO:  {status.voltage_info.dvddio_mv} mV")

            click.echo("\n--- Port A (PPA) ---")
            click.echo(f"  LTSSM State:  {status.ppa_status.current_ltssm_state.name}")
            click.echo(f"  Link Speed:   {status.ppa_status.current_link_speed.name}")
            click.echo(f"  Link Width:   x{status.ppa_status.current_link_width}")
            click.echo(f"  Link Up:      {'Yes' if status.ppa_status.is_link_up else 'No'}")
            click.echo(f"  Forwarding:   {'Yes' if status.ppa_status.is_forwarding else 'No'}")

            click.echo("\n--- Port B (PPB) ---")
            click.echo(f"  LTSSM State:  {status.ppb_status.current_ltssm_state.name}")
            click.echo(f"  Link Speed:   {status.ppb_status.current_link_speed.name}")
            click.echo(f"  Link Width:   x{status.ppb_status.current_link_width}")
            click.echo(f"  Link Up:      {'Yes' if status.ppb_status.is_link_up else 'No'}")
            click.echo(f"  Forwarding:   {'Yes' if status.ppb_status.is_forwarding else 'No'}")

            click.echo("\n--- Interrupts ---")
            click.echo(f"  Global:        {'Set' if status.interrupt_status.global_interrupt else 'Clear'}")
            click.echo(f"  EQ Phase Err:  {'Set' if status.interrupt_status.eq_phase_error else 'Clear'}")
            click.echo(f"  PHY Phase Err: {'Set' if status.interrupt_status.phy_phase_error else 'Clear'}")
            click.echo(f"  Internal Err:  {'Set' if status.interrupt_status.internal_error else 'Clear'}")

        finally:
            await device.disconnect()

    run_async(_status())


@cli.command()
@click.argument("address", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
def config(address: str, port: int, speed: int):
    """Get device configuration."""
    async def _config():
        addr = int(address, 16) if address.startswith("0x") else int(address)

        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            config = await device.get_configuration()

            click.echo("\n=== Device Configuration ===\n")
            click.echo(f"Bifurcation Mode:  {config.bifurcation_mode.name}")
            click.echo(f"Max Data Rate:     {config.max_data_rate.name}")
            click.echo(f"Clocking Mode:     {config.clocking_mode.name}")
            click.echo(f"Port Orientation:  {config.port_orientation.name}")

            click.echo("\n--- Interrupt Enables ---")
            click.echo(f"  Global:        {'Enabled' if config.interrupt_config.global_interrupt_enable else 'Disabled'}")
            click.echo(f"  EQ Phase Err:  {'Enabled' if config.interrupt_config.eq_phase_error_enable else 'Disabled'}")
            click.echo(f"  PHY Phase Err: {'Enabled' if config.interrupt_config.phy_phase_error_enable else 'Disabled'}")
            click.echo(f"  Internal Err:  {'Enabled' if config.interrupt_config.internal_error_enable else 'Disabled'}")

        finally:
            await device.disconnect()

    run_async(_config())


@cli.command()
@click.argument("address", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
@click.option("--bifurcation", "-b", help="Bifurcation mode (e.g., X16, X8_X8)")
@click.option("--data-rate", "-d", help="Max data rate (e.g., GEN6_64G)")
@click.option("--clocking", "-c", help="Clocking mode (e.g., COMMON_WO_SSC)")
def set_config(address: str, port: int, speed: int, bifurcation: Optional[str],
               data_rate: Optional[str], clocking: Optional[str]):
    """Set device configuration."""
    async def _set_config():
        addr = int(address, 16) if address.startswith("0x") else int(address)

        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            update = ConfigurationUpdate()

            if bifurcation:
                try:
                    update.bifurcation_mode = BifurcationMode[bifurcation]
                except KeyError:
                    click.echo(f"Error: Invalid bifurcation mode: {bifurcation}")
                    return

            if data_rate:
                try:
                    update.max_data_rate = MaxDataRate[data_rate]
                except KeyError:
                    click.echo(f"Error: Invalid data rate: {data_rate}")
                    return

            if clocking:
                try:
                    update.clocking_mode = ClockingMode[clocking]
                except KeyError:
                    click.echo(f"Error: Invalid clocking mode: {clocking}")
                    return

            await device.set_configuration(update)
            click.echo("Configuration updated successfully.")

        finally:
            await device.disconnect()

    run_async(_set_config())


@cli.command()
@click.argument("address", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
@click.option("--type", "-t", "reset_type", default="SOFT",
              type=click.Choice(["HARD", "SOFT", "MAC", "PERST", "GLOBAL_SWRST"]),
              help="Reset type")
def reset(address: str, port: int, speed: int, reset_type: str):
    """Reset the device."""
    async def _reset():
        addr = int(address, 16) if address.startswith("0x") else int(address)

        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            await device.reset(ResetType[reset_type])
            click.echo(f"Device reset ({reset_type}) completed.")

        finally:
            await device.disconnect()

    run_async(_reset())


@cli.command()
@click.argument("address", type=str)
@click.argument("register", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
@click.option("--width", "-w", default=32, type=click.Choice([16, 32]), help="Register width")
def read_reg(address: str, register: str, port: int, speed: int, width: int):
    """Read a register."""
    async def _read_reg():
        addr = int(address, 16) if address.startswith("0x") else int(address)
        reg = int(register, 16) if register.startswith("0x") else int(register)

        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            value = await device.read_register(reg, width)
            click.echo(f"Register 0x{reg:04X} = 0x{value:0{width // 4}X}")

        finally:
            await device.disconnect()

    run_async(_read_reg())


@cli.command()
@click.argument("address", type=str)
@click.argument("register", type=str)
@click.argument("value", type=str)
@click.option("--port", "-p", default=0, help="USB adapter port number")
@click.option("--speed", "-s", default=400, help="I2C bus speed in kHz")
@click.option("--width", "-w", default=32, type=click.Choice([16, 32]), help="Register width")
def write_reg(address: str, register: str, value: str, port: int, speed: int, width: int):
    """Write a register."""
    async def _write_reg():
        addr = int(address, 16) if address.startswith("0x") else int(address)
        reg = int(register, 16) if register.startswith("0x") else int(register)
        val = int(value, 16) if value.startswith("0x") else int(value)

        device = await RetimerDevice.from_i2c(
            address=addr,
            adapter_port=port,
            bus_speed_khz=speed,
        )

        try:
            await device.write_register(reg, val, width)
            click.echo(f"Wrote 0x{val:0{width // 4}X} to register 0x{reg:04X}")

        finally:
            await device.disconnect()

    run_async(_write_reg())


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind")
@click.option("--port", "-p", default=8000, help="Port to bind")
@click.option("--no-ui", is_flag=True, default=False, help="API-only mode, no NiceGUI dashboard")
def serve(host: str, port: int, no_ui: bool):
    """Start the REST API server with optional NiceGUI dashboard."""
    import uvicorn

    if no_ui:
        from phoenix.api.app import app as server_app
        click.echo(f"Starting Phoenix API server (API-only) at http://{host}:{port}")
    else:
        from phoenix.api.app import create_app_with_ui
        server_app = create_app_with_ui()
        click.echo(f"Starting Phoenix Dashboard at http://{host}:{port}")
        click.echo(f"REST API available at http://{host}:{port}/api/devices/")

    click.echo("Press Ctrl+C to stop.")
    uvicorn.run(server_app, host=host, port=port)


if __name__ == "__main__":
    cli()
