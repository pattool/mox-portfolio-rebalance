import pytest
from script._setup_script import setup_script
from moccasin.config import get_active_network

@pytest.fixture(scope="function")
def setup():
    """Run setup script and return contracts."""
    return setup_script()

@pytest.fixture(scope="session")
def active_network():
    """Get the active network configuration."""
    return get_active_network()

   