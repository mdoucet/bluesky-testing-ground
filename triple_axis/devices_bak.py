"""Calculates monochromator or analyzer energy as a function of angle and d-spacing

"""
import numpy as np
import time

from ophyd import Device, Component as Cpt
from ophyd import EpicsSignal, Signal

from ophyd.status import DeviceStatus

# Mock tavi_interface for this example
class MockTavi:
    @staticmethod
    def tavi_bragg_angle_to_energy(angle, d_spacing):
        # E = (h*c) / (2*d*sin(theta))
        # Simplified calculation for demonstration
        return 81.81 / (d_spacing * np.sin(np.radians(angle)))
    
    @staticmethod
    def tavi_bragg_energy_to_angle(energy, d_spacing):
        # theta = arcsin((h*c) / (2*d*E))
        return np.degrees(np.arcsin(81.81 / (d_spacing * energy)))

tavi = MockTavi()


def create_energy_selector_device(pv_a1_suffix='A1', pv_a2_suffix='A2'):
    """
    Factory function to create EnergySelectorDevice with custom PV suffixes.
    Alternative approach for creating devices with custom PV names.
    
    Parameters
    ----------
    pv_a1_suffix : str
        Suffix for the first angle PV (e.g., 'mono:theta', 'M1:ANGLE')
    pv_a2_suffix : str
        Suffix for the second angle PV (e.g., 'mono:two_theta', 'M2:ANGLE')
    
    Returns
    -------
    class
        EnergySelectorDevice class with the specified PV suffixes
    """
    
    class EnergySelectorDevice(Device):
        """
        Device representing incident energy from monochromator angles.
        Created with custom PV suffixes.
        """
        
        # EPICS PVs with custom suffixes
        pv_a1 = Cpt(EpicsSignal, pv_a1_suffix, kind='config')
        pv_a2 = Cpt(EpicsSignal, pv_a2_suffix, kind='config') 
        
        # Computed energy - this is what we read/set
        energy = Cpt(Signal, kind='hinted')

        def __init__(self, d_spacing=3.35, prefix='', name='energy_selector', **kwargs):
            super().__init__(prefix=prefix, name=name, **kwargs)
            
            self.d_spacing = d_spacing  # Crystal d-spacing in angstroms
            
            # Set initial energy value
            self.energy.put(0.0)
            
            # Subscribe to angle changes to update energy
            self.pv_a1.subscribe(self._on_angle_change)

        def set_d_spacing(self, d_spacing):
            """Set the d-spacing for energy calculations."""
            self.d_spacing = d_spacing
            self._compute_energy()

        def _compute_energy(self):
            """Compute energy based on current angle."""
            try:
                angle = self.pv_a1.get()
                if angle > 0:
                    energy_value = tavi.tavi_bragg_angle_to_energy(angle, self.d_spacing)
                    self.energy.put(energy_value)
            except Exception:
                # Handle cases where angle is invalid
                self.energy.put(0.0)

        def _on_angle_change(self, value, old_value, **kwargs):
            """Called when angle PV changes."""
            self._compute_energy()

        def set(self, energy):
            """
            Set the energy by moving the monochromator angle.
            Returns a status object for Bluesky integration.
            """
            status = DeviceStatus(self, timeout=30)
            
            try:
                # Calculate required angle
                theta = tavi.tavi_bragg_energy_to_angle(energy, self.d_spacing)
                two_theta = 2 * theta
                
                # Move the motors (this would normally return status objects)
                self.pv_a1.put(theta)
                self.pv_a2.put(two_theta)
                
                # Update our energy reading
                self.energy.put(energy)
                
                # Mark as complete (in real implementation, wait for motors)
                status.set_finished()
                
            except Exception as e:
                status.set_exception(e)
            
            return status

        def read(self):
            """Return current energy reading."""
            return {
                f'{self.name}_energy': {
                    'value': self.energy.get(),
                    'timestamp': time.time()
                }
            }

        def read_configuration(self):
            """Return configuration information."""
            return {
                f'{self.name}_d_spacing': {
                    'value': self.d_spacing,
                    'timestamp': time.time()
                },
                f'{self.name}_pv_a1': {
                    'value': self.pv_a1.get(),
                    'timestamp': time.time()
                },
                f'{self.name}_pv_a2': {
                    'value': self.pv_a2.get(),
                    'timestamp': time.time()
                }
            }
    
    return EnergySelectorDevice
