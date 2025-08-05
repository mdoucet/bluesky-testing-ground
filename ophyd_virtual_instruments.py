"""
Ophyd Virtual Instrument Examples

This module demonstrates how to create virtual instrument classes using 
Bluesky's ophyd layer for simulation and testing purposes.

Ophyd provides several key components for creating virtual devices:
- SynSignal: Synthetic signals for simulation
- SynAxis: Synthetic positioners/motors
- Device: Base class for grouping signals
- Component: For defining device structure

Install required packages:
pip install ophyd bluesky
"""

from ophyd import Device, Component as Cpt, Signal
from ophyd.sim import SynSignal, SynAxis
from ophyd import Kind
import numpy as np
import time


# ============================================================================
# Basic Virtual Signal Examples
# ============================================================================

class BasicVirtualDetector(Device):
    """
    A simple virtual detector with noise simulation.
    
    This demonstrates:
    - Basic signal creation
    - Configuration vs primary readings
    - Custom read behavior
    """
    
    # Primary reading - what gets recorded in each measurement
    intensity = Cpt(SynSignal, kind=Kind.normal)
    # Configuration - recorded once per scan
    exposure_time = Cpt(SynSignal, kind=Kind.config)
    gain = Cpt(SynSignal, kind=Kind.config)
    # Hint - suggests this is the primary quantity of interest
    # (set in __init__)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        self.intensity.put(1000)
        self.exposure_time.put(1.0)
        self.gain.put(1.0)
        self.intensity.kind = Kind.hinted
    
    def trigger(self):
        """
        Simulate data acquisition with noise.
        This is called by bluesky when taking a measurement.
        """
        # Simulate some physics: base signal + noise
        base_signal = 1000 * self.gain.get() * self.exposure_time.get()
        noise = np.random.normal(0, np.sqrt(base_signal) * 0.1)
        new_value = max(0, base_signal + noise)
        
        self.intensity.put(new_value)
        
        # Return a status object (completed immediately for virtual device)
        from ophyd.status import DeviceStatus
        status = DeviceStatus(self)
        status.set_finished()
        return status


# ============================================================================
# Advanced Virtual Positioner
# ============================================================================

class VirtualTemperatureController(Device):
    """
    A virtual temperature controller with realistic physics simulation.
    
    Demonstrates:
    - Custom positioner behavior
    - Time-based physics simulation
    - Status objects for motion
    """
    
    # Current temperature (read-only)
    temperature = Cpt(SynSignal, kind=Kind.hinted)
    # Setpoint (what we want the temperature to be)
    setpoint = Cpt(SynSignal, kind=Kind.normal)
    # Configuration parameters
    heating_rate = Cpt(SynSignal, kind=Kind.config)  # deg/min
    cooling_rate = Cpt(SynSignal, kind=Kind.config)  # deg/min
    tolerance = Cpt(SynSignal, kind=Kind.config)     # deg
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_temp = 20.0
        self._last_update = time.time()
        self.temperature.put(20.0)
        self.setpoint.put(20.0)
        self.heating_rate.put(5.0)
        self.cooling_rate.put(3.0)
        self.tolerance.put(0.1)
    
    def set(self, value):
        """
        Set target temperature and return a status object.
        This simulates the time it takes to reach temperature.
        """
        from ophyd.status import DeviceStatus
        
        self._target_temp = float(value)
        self.setpoint.put(value)
        
        # Calculate time to reach target
        current_temp = self.temperature.get()
        temp_diff = abs(value - current_temp)
        
        if value > current_temp:
            time_needed = temp_diff / self.heating_rate.get() * 60  # convert to seconds
        else:
            time_needed = temp_diff / self.cooling_rate.get() * 60
        
        # Create status object
        status = DeviceStatus(self, timeout=time_needed + 10)
        
        # Simulate the temperature change
        self._simulate_temperature_change(status, time_needed)
        
        return status
    
    def _simulate_temperature_change(self, status, duration):
        """Simulate gradual temperature change over time."""
        import threading
        
        def temperature_ramp():
            start_temp = self.temperature.get()
            target_temp = self._target_temp
            start_time = time.time()
            
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                progress = elapsed / duration
                
                # Linear interpolation with some realistic overshoot/undershoot
                current_temp = start_temp + (target_temp - start_temp) * progress
                
                # Add some realistic temperature control noise
                noise = np.random.normal(0, 0.05)
                current_temp += noise
                
                self.temperature.put(current_temp)
                time.sleep(0.1)  # Update every 100ms
            
            # Final temperature (within tolerance)
            final_temp = target_temp + np.random.normal(0, self.tolerance.get()/3)
            self.temperature.put(final_temp)
            status.set_finished()
        
        # Start the simulation in a background thread
        thread = threading.Thread(target=temperature_ramp)
        thread.daemon = True
        thread.start()


# ============================================================================
# Multi-Component Virtual Instrument
# ============================================================================

class VirtualSpectrometer(Device):
    """
    A complex virtual spectrometer with multiple components.
    
    Demonstrates:
    - Multiple related signals
    - Array data
    - Complex device composition
    """
    
    # Spectrometer settings
    integration_time = Cpt(SynSignal, kind=Kind.config)
    wavelength_min = Cpt(SynSignal, kind=Kind.config)
    wavelength_max = Cpt(SynSignal, kind=Kind.config)
    num_pixels = Cpt(SynSignal, kind=Kind.config)
    # Output data
    spectrum = Cpt(SynSignal, kind=Kind.normal)
    wavelengths = Cpt(SynSignal, kind=Kind.normal)
    # Status indicators
    temperature = Cpt(SynSignal, kind=Kind.normal)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.integration_time.put(0.1)
        self.wavelength_min.put(400)
        self.wavelength_max.put(700)
        self.num_pixels.put(1024)
        self.temperature.put(25.0)
        self._generate_wavelength_array()
        self._generate_initial_spectrum()
    
    def _generate_wavelength_array(self):
        """Generate the wavelength array based on current settings."""
        wl_min = self.wavelength_min.get()
        wl_max = self.wavelength_max.get()
        n_pixels = int(self.num_pixels.get())
        
        wavelengths = np.linspace(wl_min, wl_max, n_pixels)
        self.wavelengths.put(wavelengths)
        return wavelengths
    
    def _generate_initial_spectrum(self):
        """Generate a realistic-looking spectrum."""
        wavelengths = self._generate_wavelength_array()
        
        # Simulate a blackbody spectrum with some absorption lines
        spectrum = self._blackbody_spectrum(wavelengths, self.temperature.get())
        
        # Add some absorption lines (simple Gaussians)
        absorption_lines = [500, 550, 600]  # nm
        for line_center in absorption_lines:
            line_strength = np.random.uniform(0.1, 0.3)
            line_width = np.random.uniform(2, 5)
            spectrum *= (1 - line_strength * np.exp(-(wavelengths - line_center)**2 / (2 * line_width**2)))
        
        # Add noise
        noise = np.random.normal(0, 0.01, len(spectrum))
        spectrum += noise
        
        self.spectrum.put(spectrum)
    
    def _blackbody_spectrum(self, wavelengths, temperature):
        """Calculate blackbody spectrum (simplified)."""
        # Planck's law (simplified for demonstration)
        h = 6.626e-34  # Planck constant
        c = 3e8        # Speed of light
        k = 1.381e-23  # Boltzmann constant
        
        wl_m = wavelengths * 1e-9  # Convert nm to m
        
        # Simplified blackbody formula
        spectrum = 1 / (wl_m**5 * (np.exp(h*c/(wl_m*k*temperature)) - 1))
        
        # Normalize
        spectrum = spectrum / np.max(spectrum)
        
        return spectrum
    
    def trigger(self):
        """Acquire a new spectrum."""
        from ophyd.status import DeviceStatus
        
        # Simulate integration time
        integration_time = self.integration_time.get()
        
        # Generate new spectrum with some variation
        temp_variation = np.random.normal(0, 1)  # Temperature fluctuation
        new_temp = self.temperature.get() + temp_variation
        self.temperature.put(new_temp)
        
        # Regenerate spectrum
        self._generate_initial_spectrum()
        
        # Create status that completes after integration time
        status = DeviceStatus(self, timeout=integration_time + 1)
        
        def complete_after_delay():
            time.sleep(integration_time)
            status.set_finished()
        
        import threading
        thread = threading.Thread(target=complete_after_delay)
        thread.daemon = True
        thread.start()
        
        return status


# ============================================================================
# Usage Examples
# ============================================================================

def example_usage():
    """
    Example usage of virtual instruments with Bluesky.
    """
    
    # Create virtual devices
    detector = BasicVirtualDetector(name='detector')
    temp_controller = VirtualTemperatureController(name='temp_ctrl')
    spectrometer = VirtualSpectrometer(name='spec')
    
    print("=== Virtual Instrument Examples ===\n")
    
    # Example 1: Basic detector
    print("1. Basic Virtual Detector:")
    print(f"   Current intensity: {detector.intensity.get()}")
    print(f"   Exposure time: {detector.exposure_time.get()}")
    
    # Trigger a measurement
    status = detector.trigger()
    status.wait()  # Wait for completion
    print(f"   After trigger: {detector.intensity.get()}")
    print()
    
    # Example 2: Temperature controller
    print("2. Virtual Temperature Controller:")
    print(f"   Current temperature: {temp_controller.temperature.get():.1f}°C")
    
    # Set new temperature (this would normally be done by bluesky)
    print("   Setting temperature to 50°C...")
    status = temp_controller.set(50.0)
    print(f"   Status: {status}")
    print(f"   Estimated time: {status.timeout:.1f}s")
    print()
    
    # Example 3: Spectrometer
    print("3. Virtual Spectrometer:")
    wavelengths = spectrometer.wavelengths.get()
    spectrum = spectrometer.spectrum.get()
    print(f"   Wavelength range: {wavelengths[0]:.1f} - {wavelengths[-1]:.1f} nm")
    print(f"   Spectrum shape: {spectrum.shape}")
    print(f"   Peak intensity: {np.max(spectrum):.3f}")
    print()
    
    # Example 4: Reading device configurations
    print("4. Device Configurations:")
    print("   Detector config:", detector.read_configuration())
    print("   Temp controller config:", temp_controller.read_configuration())
    print()


if __name__ == "__main__":
    # Run examples
    example_usage()
    
    print("=== Integration with Bluesky ===")
    print("""
To use these devices with Bluesky RunEngine:

from bluesky import RunEngine
from bluesky.plans import count, scan
from bluesky.callbacks import LiveTable

RE = RunEngine()

# Simple count plan
RE(count([detector], num=5, delay=1))

# Temperature scan
RE(scan([detector], temp_controller, 20, 80, 10))

# With live table
RE(count([detector, spectrometer], num=3), LiveTable(['detector_intensity', 'spec_temperature']))
""")
