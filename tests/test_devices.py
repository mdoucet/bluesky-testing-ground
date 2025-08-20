"""
Unit tests for triple_axis.devices module.

Tests the EnergySelectorDevice class and related functionality,
following patterns from pv_name_examples.py.

This version focuses on testing the core logic without EPICS dependencies.
"""

import pytest
from tavi.instrument.components.mono_ana import MonoAna

from triple_axis.devices import create_energy_selector_device


@pytest.fixture
def mono_pg002():
    """Fixture for a Monochromator using PG(002) reflection."""
    param_dict = {
        "type": "PG002",
        "sense": "-",
        "mosaic_h": 30,
        "mosaic_v": 30,
    }
    mono = MonoAna(param_dict=param_dict, component_name="mono")
    return mono


class TestCreateEnergySelectorDevice:
    """Test the factory function for creating EnergySelectorDevice."""

    def test_factory_creates_class(self):
        """Test that factory function returns a class."""
        DeviceClass = create_energy_selector_device()
        assert isinstance(DeviceClass, type)
        # Check it's a Device subclass by inspecting the MRO
        assert any(base.__name__ == "Device" for base in DeviceClass.__mro__)

    def test_factory_with_custom_suffixes(self):
        """Test factory function creates class with custom PV suffixes."""
        DeviceClass = create_energy_selector_device(
            pv_a1_suffix="mono:theta", pv_a2_suffix="mono:two_theta"
        )

        # Check that the class has the expected component attributes
        assert hasattr(DeviceClass, "pv_a1")
        assert hasattr(DeviceClass, "pv_a2")
        assert hasattr(DeviceClass, "energy")

        # Check the suffixes are stored in the component definitions
        assert DeviceClass.pv_a1.suffix == "mono:theta"
        assert DeviceClass.pv_a2.suffix == "mono:two_theta"

    def test_multiple_device_types(self):
        """Test creating different device types like in pv_name_examples.py."""
        # Create monochromator device class
        MonoDevice = create_energy_selector_device(
            pv_a1_suffix="mono:theta", pv_a2_suffix="mono:two_theta"
        )

        # Create analyzer device class
        AnalyzerDevice = create_energy_selector_device(
            pv_a1_suffix="analyzer:angle", pv_a2_suffix="analyzer:detector_angle"
        )

        # Verify they have different suffixes
        assert MonoDevice.pv_a1.suffix != AnalyzerDevice.pv_a1.suffix
        assert MonoDevice.pv_a2.suffix != AnalyzerDevice.pv_a2.suffix

        # Both should be Device subclasses
        assert any(base.__name__ == "Device" for base in MonoDevice.__mro__)
        assert any(base.__name__ == "Device" for base in AnalyzerDevice.__mro__)

    def test_create_monochromator(self, mono_pg002):
        """ "
        Run this command in termial: python3 -m mono_iocs --list-pvs
        """
        MonoDevice = create_energy_selector_device(
            pv_a1_suffix="mono:theta", pv_a2_suffix="mono:two_theta"
        )
        mono = MonoDevice(params=mono_pg002, name="mono")
        assert mono.params.sense == "-"
        mono.set(14.45)
        assert mono.read()["mono_energy"]["value"] == 14.45
        mono.set(1)  # too low
        assert mono.read()["mono_energy"]["value"] == 14.45  # unchanged
