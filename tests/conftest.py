import pytest
from script._setup_script import setup_script
from script.rebalance_portfolio import run_script
from moccasin.config import get_active_network

@pytest.fixture(scope="function")
def setup():
    """Run setup script and return contracts."""
    return setup_script()

@pytest.fixture(scope="session")
def active_network():
    """Get the active network configuration."""
    return get_active_network()

@pytest.fixture(scope="function")
def contracts(active_network):
    """Get USDC and WETH contracts."""
    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")
    return usdc, weth


@pytest.fixture(scope="function")
def aave_contracts(active_network):
    """Get Aave pool and related contracts."""
    pool_address_provider = active_network.manifest_named("aavev3_pool_address_provider")
    pool_address = pool_address_provider.getPool()
    pool_contract = active_network.manifest_named("pool", address=pool_address)
    return pool_contract, pool_address_provider


@pytest.fixture(scope="function")
def rebalance_contracts(active_network):
    """Run rebalance script and return all 4 contracts: usdc, weth, a_usdc, a_weth."""
    if active_network.is_local_or_forked_network():
        return run_script()
    return None, None, None, None

   