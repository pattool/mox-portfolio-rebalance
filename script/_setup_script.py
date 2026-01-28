from boa.contracts.abi.abi_contract import ABIContract
from typing import Tuple
from moccasin.config import get_active_network, Network
import boa


STARTING_ETH_BALANCE  = int(1000e18) # 1000 ETH
STARTING_WETH_BALANCE = int(1e18)    # 1 WETH
STARTING_USDC_BALANCE = int(100e6)   # 100 usdc has 6 decimals

def _add_eth_balance():
    boa.env.set_balance(boa.env.eoa, STARTING_ETH_BALANCE)
    

def _add_token_balance(usdc: ABIContract, weth: ABIContract):
    print(f"Starting balance of USDC: {usdc.balanceOf(boa.env.eoa)}")
    print(f"Starting balance of WETH: {weth.balanceOf(boa.env.eoa)}")
    weth.deposit(value=STARTING_WETH_BALANCE) # check deposit on etherscan WETH -> write contract
    print(f"Ending balance of WETH: {weth.balanceOf(boa.env.eoa)}")
    
    our_address = boa.env.eoa
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(our_address) # check updateMasterMinter on etherscan usdc contract

    usdc.configureMinter(our_address, STARTING_USDC_BALANCE) # check configureMinter on usdc contract
    usdc.mint(our_address, STARTING_USDC_BALANCE)
    print(f"Ending balance of USDC: {usdc.balanceOf(boa.env.eoa)}")
    
    

def setup_script() -> Tuple[ABIContract, ABIContract]: 
    """
    1. Give ourselves some ETH
    2. Give ourselves some USDC and WETH
    """
    
    print("Starting setup script...")

    active_network = get_active_network()

    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")
    
    if active_network.is_local_or_forked_network():
        _add_eth_balance()
        _add_token_balance(usdc, weth)

    return usdc, weth

def moccasin_main():
    setup_script()