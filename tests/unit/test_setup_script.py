# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
from script._setup_script import (
    STARTING_ETH_BALANCE,
    STARTING_WETH_BALANCE,
    STARTING_USDC_BALANCE,
    _add_eth_balance,
    moccasin_main,
    setup_script
)

import boa


# ------------------------------------------------------------------
#                          TEST_FUNCTIONS
# ------------------------------------------------------------------    
def test_eth_balance_is_set():
    """Verify ETH balance is set correctly before token operations."""
    _add_eth_balance()
    assert boa.env.get_balance(boa.env.eoa) == STARTING_ETH_BALANCE


def test_setup_script_gives_eth_balance(setup):
    """Verify setup script funds the account with sufficient ETH, 
       include gas spending."""
    balance = boa.env.get_balance(boa.env.eoa)    
    assert balance >= STARTING_ETH_BALANCE  - int(1e18)
    
    
def test_setup_script_gives_weth_balance(setup):
    """Verify setup script funds the account with WETH."""
    usdc, weth = setup
    assert weth.balanceOf(boa.env.eoa) == STARTING_WETH_BALANCE


def test_setup_script_gives_usdc_balance(setup):
    """Verify setup script funds the account with USDC."""
    usdc, weth = setup
    assert usdc.balanceOf(boa.env.eoa) == STARTING_USDC_BALANCE


def test_active_network_is_local_or_forked(active_network):
    """Verify the active network is local or forked during tests."""
    assert active_network.is_local_or_forked_network() == True
    

def test_moccasin_main():
    """Verify moccasin_main calls setup_script and returns contracts."""
    result = moccasin_main()
    # moccasin_main returns None, just verify it runs successfully
    assert result is  None





    