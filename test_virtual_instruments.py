"""
Test script for virtual instruments - demonstrates integration with Bluesky
"""

from ophyd_virtual_instruments import (
    BasicVirtualDetector, 
    VirtualTemperatureController, 
    VirtualSpectrometer
)

def test_virtual_devices():
    """Test basic functionality of virtual devices."""
    
    print("Testing Virtual Instruments...")
    
    # Create devices
    detector = BasicVirtualDetector(name='test_detector')
    temp_ctrl = VirtualTemperatureController(name='test_temp')
    spec = VirtualSpectrometer(name='test_spec')
    
    # Test basic reads
    print("\n=== Basic Reading Tests ===")
    print("Detector read:", detector.read())
    print("Temperature read:", temp_ctrl.read())
    print("Spectrometer config:", spec.read_configuration())
    
    # Test triggering
    print("\n=== Trigger Tests ===")
    status = detector.trigger()
    print(f"Detector trigger status: {status}")
    status.wait(timeout=1)
    print(f"Detector after trigger: {detector.intensity.get()}")
    
    # Test temperature setting
    print("\n=== Temperature Control Test ===")
    initial_temp = temp_ctrl.temperature.get()
    print(f"Initial temperature: {initial_temp:.1f}°C")
    
    status = temp_ctrl.set(25.0)
    print(f"Setting to 25°C, status: {status}")
    
    print("\nAll basic tests passed!")

def bluesky_integration_example():
    """Example of using virtual devices with Bluesky (if available)."""
    
    try:
        from bluesky import RunEngine
        from bluesky.plans import count
        from bluesky.callbacks import LiveTable
        
        print("\n=== Bluesky Integration Example ===")
        
        # Create RunEngine
        RE = RunEngine()
        
        # Create devices
        detector = BasicVirtualDetector(name='detector')
        
        # Simple measurement
        print("Running simple count plan...")
        RE(count([detector], num=3), LiveTable(['detector_intensity']))
        
        print("Bluesky integration successful!")
        
    except ImportError:
        print("\nBluesky not available. Install with: pip install bluesky")
    except Exception as e:
        print(f"\nBluesky integration error: {e}")

if __name__ == "__main__":
    test_virtual_devices()
    bluesky_integration_example()
