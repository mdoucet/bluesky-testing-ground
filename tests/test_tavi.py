import numpy as np
import pytest
from tavi.instrument.components.mono_ana import MonoAna


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


def test_d_spacing(mono_pg002):
    d_spacing = 3.35416
    assert np.isclose(mono_pg002.d_spacing, d_spacing, rtol=1e-5)


def test_bragg_angle_from_energy(mono_pg002):
    """Test energy to angle conversion."""
    two_theta_angle = -41.5367 / 2
    ei = 14.45
    angle = mono_pg002.get_bragg_angle_from_energy(ei)
    assert np.isclose(angle, two_theta_angle, rtol=1e-3)


def test_energy_from_bragg_angle(mono_pg002):
    """Test angle to energy conversion."""
    two_theta_angle = -41.5367 / 2
    ei = 14.45
    energy = mono_pg002.get_energy_from_bragg_angle(two_theta_angle)
    assert np.isclose(energy, ei, rtol=1e-3)


def test_roundtrip_conversion(mono_pg002):
    """Test that angle->energy->angle conversion is consistent."""
    two_theta_angle = -41.5367 / 2
    energy = mono_pg002.get_energy_from_bragg_angle(two_theta_angle)
    converted_angle = mono_pg002.get_bragg_angle_from_energy(energy)

    assert np.isclose(converted_angle, two_theta_angle, rtol=1e-3)


def test_invalid_energy_domain_error(mono_pg002):
    """Test that invalid energy causes arcsin domain error."""
    invalid_energy = 1  # Too low, energy can be as arbitrarily high
    result = mono_pg002.get_bragg_angle_from_energy(invalid_energy)
    assert np.isnan(result)
