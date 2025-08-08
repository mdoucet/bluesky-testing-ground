"""
Examples of how to change PV names when instantiating EnergySelectorDevice
"""
import numpy as np
import time

from ophyd import Device, Component as Cpt
from ophyd import EpicsSignal, Signal
from ophyd.status import DeviceStatus

from triple_axis.devices import create_energy_selector_device


def usage_examples():
    """Examples of different ways to instantiate with custom PV names."""
    
    print("=== Different Ways to Change PV Names ===\n")
    
    # Method 1: Factory function (most flexible)
    print("1. Using factory function:")
    MonoDevice = create_energy_selector_device(
        pv_a1_suffix='mono:theta',      # Your real PV suffix
        pv_a2_suffix='mono:two_theta'   # Your real PV suffix
    )
    
    mono1 = MonoDevice(
        d_spacing=3.35,
        prefix='HFIR:',
        name='incident_energy'
    )
    print(f"   PV1: {mono1.prefix}{mono1.pv_a1.suffix}")  # HFIR:mono:theta
    print(f"   PV2: {mono1.prefix}{mono1.pv_a2.suffix}")  # HFIR:mono:two_theta
    
    # Method 2: Different PV names for analyzer
    print("\n2. Creating analyzer device:")
    AnalyzerDevice = create_energy_selector_device(
        pv_a1_suffix='analyzer:angle',
        pv_a2_suffix='analyzer:detector_angle'
    )
    
    analyzer = AnalyzerDevice(
        d_spacing=3.35,
        prefix='SPEC:',
        name='final_energy'
    )
    print(f"   PV1: {analyzer.prefix}{analyzer.pv_a1.suffix}")  # SPEC:analyzer:angle
    print(f"   PV2: {analyzer.prefix}{analyzer.pv_a2.suffix}")  # SPEC:analyzer:detector_angle
    

    return mono1, analyzer, hfir_mono


def bluesky_usage_example():
    """Example using the devices with Bluesky."""
    
    try:
        from bluesky import RunEngine
        from bluesky.plans import count, scan
        from bluesky.callbacks import LiveTable
        
        print("\n=== Bluesky Usage Examples ===\n")
        
        # Create devices with real PV names
        MonoDevice = create_energy_selector_device('mono:theta', 'mono:two_theta')
        AnalyzerDevice = create_energy_selector_device('analyzer:theta', 'analyzer:two_theta')
        
        incident_energy = MonoDevice(prefix='HFIR:', name='ei')
        final_energy = AnalyzerDevice(prefix='HFIR:', name='ef')
        
        # Mock detector
        from ophyd.sim import SynSignal
        
        class Detector(Device):
            counts = Cpt(SynSignal, kind='hinted')
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.counts.put(1000)
        
        detector = Detector(name='detector')
        
        RE = RunEngine()
        
        # 1. Set incident energy and measure
        print("1. Setting incident energy to 14.7 meV:")
        incident_energy.set(14.7).wait()
        RE(count([detector, incident_energy], num=1),
           LiveTable(['detector_counts', 'ei_energy']))
        
        # 2. Energy scan
        print("\n2. Incident energy scan:")
        RE(scan([detector], incident_energy, 10, 20, 3),
           LiveTable(['ei_energy', 'detector_counts']))
        
        # 3. Two-energy device measurement  
        print("\n3. Reading both incident and final energies:")
        final_energy.set(5.0).wait()
        RE(count([incident_energy, final_energy], num=1),
           LiveTable(['ei_energy', 'ef_energy']))
        
        print("\n✅ All Bluesky examples completed successfully!")
        
    except ImportError:
        print("Bluesky not available. Install with: pip install bluesky")


if __name__ == "__main__":
    # Demonstrate different instantiation methods
    mono1, analyzer, hfir_mono = usage_examples()
    
    # Show Bluesky integration
    bluesky_usage_example()
