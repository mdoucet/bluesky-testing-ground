# Bluesky Ophyd Virtual Instruments Guide

This repository demonstrates how to create virtual instrument classes using Bluesky's **ophyd** layer for simulation, testing, and development purposes.

## What is Ophyd?

**Ophyd** (Observable Physical Devices) is Python library that provides:

- **Hardware Abstraction**: Unified interface for different control systems (EPICS, Tango, etc.)
- **Device Composition**: Group related signals into logical devices
- **Integration with Bluesky**: Seamless data acquisition and experiment control
- **Status Management**: Track long-running operations like motor movements
- **Virtual Devices**: Simulation capabilities for testing and development

### Key Concepts

1. **Signals**: Individual control/readback channels (like EPICS PVs)
2. **Devices**: Collections of related signals with coordination logic
3. **Components**: Define the structure of devices
4. **Status Objects**: Track the progress of operations
5. **Kinds**: Categorize readings (primary data, configuration, etc.)

## Virtual Instruments Overview

Virtual instruments in ophyd allow you to:

- **Test control logic** without hardware
- **Develop new experiments** safely
- **Train users** on software interfaces
- **Simulate realistic physics** for development
- **Create reproducible test scenarios**

## Installation

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install ophyd bluesky numpy matplotlib
```

## Core Classes for Virtual Devices

### 1. SynSignal (Synthetic Signal)
```python
from ophyd.sim import SynSignal
from ophyd import Component as Cpt, Device

class SimpleDevice(Device):
    value = Cpt(SynSignal, value=0.0)
```

### 2. SynAxis (Synthetic Positioner)
```python
from ophyd.sim import SynAxis

# Creates a virtual motor/positioner
motor = SynAxis(name='virtual_motor')
```

### 3. Custom Virtual Devices
See `ophyd_virtual_instruments.py` for complete examples.

## Examples in This Repository

### 1. BasicVirtualDetector
- Simulates a detector with noise
- Demonstrates configuration vs. primary readings
- Shows proper `trigger()` implementation

### 2. VirtualTemperatureController
- Realistic physics simulation
- Time-based temperature ramping
- Status objects for long operations

### 3. VirtualSpectrometer
- Array data handling
- Complex multi-component device
- Blackbody spectrum simulation

## Key Ophyd Concepts for Virtual Devices

### Device Structure
```python
from ophyd import Device, Component as Cpt
from ophyd.sim import SynSignal
from ophyd import Kind

class MyDevice(Device):
    # Primary reading (goes in Event documents)
    reading = Cpt(SynSignal, kind=Kind.normal)
    
    # Configuration (goes in Event Descriptor)
    setting = Cpt(SynSignal, kind=Kind.config)
    
    # Hinted (suggested for live displays)
    main_value = Cpt(SynSignal, kind=Kind.hinted)
```

### Signal Kinds
- `Kind.normal`: Regular readings, recorded with each measurement
- `Kind.config`: Configuration, recorded once per scan
- `Kind.hinted`: Primary quantity of interest for live displays
- `Kind.omitted`: Not recorded in data

### Status Objects
```python
from ophyd.status import DeviceStatus

def trigger(self):
    status = DeviceStatus(self)
    # ... do work ...
    status.set_finished()  # Mark as complete
    return status
```

### Device Methods
- `read()`: Get current values of normal-kind signals
- `read_configuration()`: Get configuration values
- `trigger()`: Initiate data acquisition
- `set(value)`: Move to new position (for positioners)
- `stop()`: Halt operations

## Running the Examples

### Basic Test
```bash
python test_virtual_instruments.py
```

### Interactive Usage
```python
from ophyd_virtual_instruments import BasicVirtualDetector

detector = BasicVirtualDetector(name='my_detector')
print(detector.read())

# Trigger measurement
status = detector.trigger()
status.wait()
print(detector.read())
```

### With Bluesky RunEngine
```python
from bluesky import RunEngine
from bluesky.plans import count
from bluesky.callbacks import LiveTable

RE = RunEngine()
detector = BasicVirtualDetector(name='detector')

# Take 5 measurements with 1 second delay
RE(count([detector], num=5, delay=1), LiveTable(['detector_intensity']))
```

## Best Practices for Virtual Devices

### 1. Realistic Physics
- Simulate actual device behavior (noise, drift, etc.)
- Include realistic timing for operations
- Model temperature dependencies, nonlinearities

### 2. Proper Status Management
```python
def set(self, value):
    status = DeviceStatus(self, timeout=10)
    
    def complete_move():
        # Simulate movement time
        time.sleep(abs(value - self.position.get()) / self.velocity)
        self.position.put(value)
        status.set_finished()
    
    threading.Thread(target=complete_move, daemon=True).start()
    return status
```

### 3. Configuration Management
- Use `Kind.config` for settings that don't change during a scan
- Use `Kind.normal` for measurements
- Use `Kind.hinted` for the primary quantity of interest

### 4. Error Simulation
```python
def trigger(self):
    if random.random() < 0.05:  # 5% chance of error
        status = DeviceStatus(self)
        status.set_exception(RuntimeError("Simulated device error"))
        return status
    # ... normal operation
```

## Integration with Bluesky Plans

Virtual devices work seamlessly with all Bluesky plans:

```python
from bluesky.plans import scan, count, grid_scan

# 1D scan
RE(scan([detector], motor, 0, 10, 11))

# Grid scan
RE(grid_scan([detector], motor1, 0, 10, 11, motor2, 0, 5, 6))

# Count with temperature control
RE(count([detector], num=10), TemperaturePlan(temp_controller, 25))
```

## Common Patterns

### Array Detectors
```python
class ArrayDetector(Device):
    image = Cpt(SynSignal, value=np.zeros((100, 100)))
    
    def trigger(self):
        # Generate new random image
        new_image = np.random.random((100, 100))
        self.image.put(new_image)
        
        status = DeviceStatus(self)
        status.set_finished()
        return status
```

### Multi-Channel Devices
```python
class MultiChannelDetector(Device):
    ch1 = Cpt(SynSignal, kind=Kind.normal)
    ch2 = Cpt(SynSignal, kind=Kind.normal)
    ch3 = Cpt(SynSignal, kind=Kind.normal)
    
    def trigger(self):
        # Correlated noise between channels
        base = np.random.normal(1000, 100)
        self.ch1.put(base + np.random.normal(0, 10))
        self.ch2.put(base * 0.8 + np.random.normal(0, 15))
        self.ch3.put(base * 1.2 + np.random.normal(0, 20))
        
        status = DeviceStatus(self)
        status.set_finished()
        return status
```

### Example: Physics Quantity Device (E_i as a function of PV1 and PV2)
```python
from ophyd import Device, Component as Cpt
from ophyd import EpicsSignal, Signal

class EiDevice(Device):
    """
    Device representing a physics quantity E_i = f(PV1, PV2)
    where PV1 and PV2 are EPICS process variables.
    """
    # Connect to EPICS PVs
    pv1 = Cpt(EpicsSignal, 'PV1')
    pv2 = Cpt(EpicsSignal, 'PV2')
    
    # Computed physics quantity
    ei = Cpt(Signal, kind='hinted')
    
    def __init__(self, prefix='', name='ei_device', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)
        self.compute_ei()
        # Subscribe to PV changes to update E_i
        self.pv1.subscribe(self._on_pv_change)
        self.pv2.subscribe(self._on_pv_change)
    
    def compute_ei(self):
        # Example: E_i = PV1^2 + 3*PV2
        val1 = self.pv1.get()
        val2 = self.pv2.get()
        ei_value = val1 ** 2 + 3 * val2
        self.ei.put(ei_value)
    
    def _on_pv_change(self, value, old_value, **kwargs):
        self.compute_ei()
    
    def read(self):
        # Return all values
        return {
            f'{self.name}_pv1': {'value': self.pv1.get()},
            f'{self.name}_pv2': {'value': self.pv2.get()},
            f'{self.name}_ei': {'value': self.ei.get()}
        }
```

# Usage Example
```python
# Create device (replace 'MY:PV1' and 'MY:PV2' with actual EPICS PV names)
ei_device = EiDevice(prefix='MY:', name='ei_device')

# Set PVs (if using simulation or caproto)
ei_device.pv1.put(2.0)
ei_device.pv2.put(5.0)

# Read computed E_i
print(ei_device.read())  # {'ei_device_pv1': ..., 'ei_device_pv2': ..., 'ei_device_ei': ...}
```

## Debugging Virtual Devices

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or specific to ophyd
logger = logging.getLogger('ophyd')
logger.setLevel(logging.DEBUG)
```

### Check Device Status
```python
device = MyDevice(name='test')
print(f"Connected: {device.connected}")
print(f"Read attrs: {device.read_attrs}")
print(f"Config attrs: {device.configuration_attrs}")
```

## Advanced Topics

### Custom Signal Classes
```python
from ophyd import Signal

class NoiseSignal(Signal):
    def get(self):
        return self._readback + np.random.normal(0, 0.1)
    
    def put(self, value):
        self._readback = float(value)
        return self._set_and_wait(value)
```

### Subscribing to Changes
```python
def value_changed(value, old_value, **kwargs):
    print(f"Value changed from {old_value} to {value}")

device.signal.subscribe(value_changed)
```

## Resources

- [Ophyd Documentation](https://blueskyproject.io/ophyd/)
- [Bluesky Documentation](https://blueskyproject.io/bluesky/)
- [Bluesky Tutorials](https://blueskyproject.io/tutorials/)
- [NSLS-II Tutorials](https://github.com/NSLS-II/tutorial)

## Contributing

Feel free to add more virtual device examples or improve existing ones. Common additions:
- More realistic physics models
- Complex multi-component devices
- Error simulation scenarios
- Performance benchmarking devices
