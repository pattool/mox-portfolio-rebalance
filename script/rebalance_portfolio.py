# ------------------------------------------------------------------
#                         IMPORT LIBRARIES
# ------------------------------------------------------------------
from boa.contracts.abi.abi_contract import ABIContract
from typing import Tuple
from moccasin.config import get_active_network
import boa


# ------------------------------------------------------------------
#                            VARIABLES
# ------------------------------------------------------------------
STARTING_ETH_BALANCE = int(1000e18)
STARTING_WETH_BALANCE = int(1e18)
STARTING_USDC_BALANCE = int(100e6) # usdc 6 decimals not 18
REFERRAL_CODE = 0


# ------------------------------------------------------------------
#                            FUNCTIONS
# ------------------------------------------------------------------
# Add 1000 ETH
def _add_eth_balance():
    boa.env.set_balance(boa.env.eoa, STARTING_ETH_BALANCE)


# Add 100 usdc and 1 weth
def _add_token_balance(usdc: ABIContract, weth: ABIContract):

    # Add 1 weth to balance
    print()
    print("Add tokens")
    print(f"Starting balance of WETH: {weth.balanceOf(boa.env.eoa)}")
    weth.deposit(value=STARTING_WETH_BALANCE)
    print(f"Ending balance of WETH: {weth.balanceOf(boa.env.eoa)}")

    # Add 100 usdc to balance (usdc contract is centralized)
    print(f"Starting balance USDC: {usdc.balanceOf(boa.env.eoa)}")
    our_address = boa.env.eoa
    # Pretend to be the owner
    with boa.env.prank(usdc.owner()):
        # give us the power to be the master minter
        usdc.updateMasterMinter(our_address) 

    # Configure ourself to be a regular minter
    usdc.configureMinter(our_address, STARTING_USDC_BALANCE)
    usdc.mint(our_address, STARTING_USDC_BALANCE)        
    print(f"Ending balance USDC: {usdc.balanceOf(boa.env.eoa)}")
    print()


# Depositing into Aave 
def deposit(pool_contract, token, amount):
    allowed_amount = token.allowance(boa.env.eoa, pool_contract.address)
    if allowed_amount < amount:
        token.approve(pool_contract.address, amount)
    print(f"Depositing {token.name()} into Aave contract {pool_contract.address}")
    pool_contract.supply(token.address, amount, boa.env.eoa, REFERRAL_CODE) # verify on aave doc
          

# Get Chainlink Pricefeed on ETHEREUM MAINNET
def get_price(feed_name: str) -> float:
    active_network = get_active_network()
    price_feed = active_network.manifest_named(feed_name) # feed_name: usdc_usd or eth_usd
    price = price_feed.latestAnswer()
    decimals = price_feed.decimals()
    decimals_normalized = 10 ** decimals
    return price / decimals_normalized


# Print Balances
def print_usdc_weth_token_balances():
    active_network = get_active_network()

    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")

    print("Balances:")
    print(f"USDC balance: {usdc.balanceOf(boa.env.eoa)}")
    print(f"WETH balance: {weth.balanceOf(boa.env.eoa)}")


# Calaculate Allocations
def calculate_rebalancing_trades(
    usdc_data: dict,  # {"balance": float, "price": float, "contract": Contract}
    weth_data: dict,  # {"balance": float, "price": float, "contract": Contract}
    target_allocations: dict[str, float],  # {"usdc": 0.3, "weth": 0.7}
) -> dict[str, dict]:
    """
    Calculate the trades needed to rebalance a portfolio of USDC and WETH.

    Args:
        usdc_data: Dict containing USDC balance, price and contract
        weth_data: Dict containing WETH balance, price and contract
        target_allocations: Dict of token symbol to target allocation (must sum to 1)

    Returns:
        Dict of token symbol to dict containing contract and trade amount:
            {"usdc": {"contract": Contract, "trade": int},
             "weth": {"contract": Contract, "trade": int}}
    """
    # Calculate current values
    usdc_value = usdc_data["balance"] * usdc_data["price"]
    weth_value = weth_data["balance"] * weth_data["price"]
    total_value = usdc_value + weth_value

    # Calculate target values
    target_usdc_value = total_value * target_allocations["usdc"]
    target_weth_value = total_value * target_allocations["weth"]

    # Calculate trades needed in USD
    usdc_trade_usd = target_usdc_value - usdc_value
    weth_trade_usd = target_weth_value - weth_value

    # Convert to token amounts
    return {
        "usdc": {
            "contract": usdc_data["contract"],
            "trade": usdc_trade_usd / usdc_data["price"],
        },
        "weth": {
            "contract": weth_data["contract"],
            "trade": weth_trade_usd / weth_data["price"],
        },
    }
    

# ------------------------------------------------------------------
#                       RUN SCRIPT FUNCTION
# ------------------------------------------------------------------
def run_script() -> [ABIContract, ABIContract, ABIContract, ABIContract]:
    """
    1. Give ourselves some ETH
    2. Give ourselves some USDC and WETH
    """
    
    # Setup
    print()
    print( "Starting setup script...")

    active_network = get_active_network()

    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")
    aavev3_pool_address_provider = active_network.manifest_named("aavev3_pool_address_provider")

    # Where we will put money to it
    pool_address = aavev3_pool_address_provider.getPool() 
    pool_contract = active_network.manifest_named("pool", address=pool_address) # address can change
    
    if active_network.is_local_or_forked_network():
        _add_eth_balance() # add eth
        _add_token_balance(usdc, weth) # add usdc and weth

    usdc_balance = usdc.balanceOf(boa.env.eoa)
    weth_balance = weth.balanceOf(boa.env.eoa)

    if usdc_balance > 0:
        deposit(pool_contract, usdc, usdc_balance)

    if weth_balance > 0:
        deposit(pool_contract, weth, weth_balance)

    (
        totalCollateralBase,
        totalDebtBase,
        availableBorrowsBase,
        currentLiquidationThreshold,
        ltv,                       # loan to value of the user
        healthFactor,
    ) = pool_contract.getUserAccountData(boa.env.eoa)
    print(f"""User account data:
        totalCollateralBase: {totalCollateralBase}
        totalDebtBase: {totalDebtBase}
        availableBorrowsBase: {availableBorrowsBase}
        currentLiquidationThreshold: {currentLiquidationThreshold}
        ltv: {ltv} 
        healthFactor: {healthFactor}
          """)
    print()

    # Get list of Atokens
    print("Scanning for WETH and USDC, make take a while...\n")
    aave_protocol_data_provider = active_network.manifest_named("aave_protocol_data_provider")
    a_tokens = aave_protocol_data_provider.getAllATokens() # give a list of tuples: [(token, address), (token, address)]
    print()
    #print("List Atokens:", a_tokens)

    # Scanning for WETH and USDC
    print("Atokens for WETH and USDC ....")
    print("------------------------------")
    for a_token in a_tokens:
        if"WETH" in a_token[0]:
            a_weth = active_network.manifest_named("usdc", address=a_token[1])
        if"USDC" in a_token[0]:
            a_usdc = active_network.manifest_named("usdc", address=a_token[1])
    print("Atoken USDC:", a_usdc)
    print("Atoken WETH:", a_weth)
    print()

    # Check balance a_usdc & a_weth
    a_usdc_balance = a_usdc.balanceOf(boa.env.eoa) # 6 decimals
    a_weth_balance = a_weth.balanceOf(boa.env.eoa) # 18 decimals

    # Normalized the amounts
    a_usdc_balance_normalized = a_usdc_balance / int(1e6)  # 1000000
    a_weth_balance_normalized = a_weth_balance / int(1e18) # 1000000000000000000 
    print("aUSDC balance:", a_usdc_balance_normalized) # 100 -> around 100$ price
    print("aWETH balance:", a_weth_balance_normalized) # 1 ETH

    # Get Price for usdc and weth
    usdc_price = get_price("usdc_usd")
    weth_price = get_price("eth_usd")
    print("USDC price:", usdc_price) 
    print("WETH price:", weth_price) 
    print()
        
    # Total value
    usdc_value = a_usdc_balance_normalized * usdc_price
    weth_value = a_weth_balance_normalized * weth_price
    total_value = usdc_value + weth_value

    # Check Allocation
    BUFFER = 0.1
    target_usdc_value = 0.3
    target_weth_value = 0.7

    usdc_percent_allocation = usdc_value / total_value
    weth_percent_allocation = weth_value / total_value

    needs_rebalancing = (
        abs(usdc_percent_allocation - target_usdc_value) > BUFFER
        or abs(weth_percent_allocation - target_weth_value) > BUFFER                
    )
    print("Rebalancing needed:", needs_rebalancing)
    print(f"Current USDC % allocation, {usdc_percent_allocation * 100:.2f}%")
    print(f"Current WETH % allocation, {weth_percent_allocation * 100:.2f}%")

    print(f"Target allocation of USDC: {target_usdc_value * 100:.2f}%")
    print(f"Target allocation of WETH: {target_weth_value * 100:.2f}%")
    print()
    
    # Withdrawing Weth from Aave
    a_weth.approve(pool_contract.address, a_weth.balanceOf(boa.env.eoa))
    pool_contract.withdraw(weth.address, a_weth.balanceOf(boa.env.eoa), boa.env.eoa)
                          #  asset         whole amount                    to
    
    # Print token balances
    print("Redrawing WETH from Aave")
    print_usdc_weth_token_balances()
    print(f"aUSDC balance: {a_usdc.balanceOf(boa.env.eoa)}")
    print(f"aWETH balance: {a_weth.balanceOf(boa.env.eoa)}")
    print()

    # Rebalance Trades 
    usdc_data = {"balance": a_usdc_balance_normalized, "price": usdc_price, "contract": usdc}
    weth_data = {"balance": a_weth_balance_normalized, "price": weth_price, "contract": weth}
    target_allocations = {"usdc": 0.3, "weth": 0.7}  
    
    trades = calculate_rebalancing_trades(usdc_data, weth_data, target_allocations)
    print("Rebalancing Trades:")
    #for k, v in trades.items():
    #    print(f"{k}: {v}")
    #print()

    usdc_to_buy = trades["usdc"]["trade"]
    weth_to_sell = trades["weth"]["trade"]
    print("USDC to buy:", usdc_to_buy)
    print("WETH to sell:", weth_to_sell)
    print()

    # Uniswap 
#    struct ExactInputSingleParams {
#        address tokenIn;             # what are we selling
#        address tokenOut;            # what are we buying
#        uint24 fee;                  # fee structure
#        address recipient;           # us
#        uint256 amountIn;            # how much are we sending
#        uint256 amountOutMinimum;    # minimum % to get
#        uint160 sqrtPriceLimitX96;   # price optimatisation
#    }

    # Swap Tokens: sell weth & buy usdc
    uniswap_swap_router = active_network.manifest_named("uniswap_swap_router")

    amount_weth = abs(int(weth_to_sell * (10 ** 18)))
    weth.approve(uniswap_swap_router.address, amount_weth)
    min_out = int((trades["usdc"]["trade"] * (10 ** 6)) * 0.90) # minimum 90% to get

    print("Swap tokens!")
    uniswap_swap_router.exactInputSingle(
        (
            weth.address,  # what are we selling
            usdc.address,  # what are we buying
            3000,          # fee structure, 3000 stand for 3% fee pool
            boa.env.eoa,   # us
            amount_weth,   # how much are we sending
            min_out,       # minimum % to getting back
            0              # price optimatisation         
        )        
    )

    # Print token balances    
    print_usdc_weth_token_balances()
    print(f"aUSDC balance: {a_usdc.balanceOf(boa.env.eoa)}")
    print(f"aWETH balance: {a_weth.balanceOf(boa.env.eoa)}")
    print()


    # Finish Rebalance Portfolio back in Aave
    usdc_balance = usdc.balanceOf(boa.env.eoa)
    weth_balance = weth.balanceOf(boa.env.eoa)

    if usdc_balance > 0:
        deposit(pool_contract, usdc, usdc_balance)

    if weth_balance > 0:
        deposit(pool_contract, weth, weth_balance)

    # Print token balances
    print_usdc_weth_token_balances()
    print(f"aUSDC balance: {a_usdc.balanceOf(boa.env.eoa)}")
    print(f"aWETH balance: {a_weth.balanceOf(boa.env.eoa)}")
    print()
    
    a_usdc_balance = a_usdc.balanceOf(boa.env.eoa)
    a_weth_balance = a_weth.balanceOf(boa.env.eoa)

    a_usdc_balance_normalized = a_usdc_balance / int(1e6)  
    a_weth_balance_normalized = a_weth_balance / int(1e18)

    usdc_value = a_usdc_balance_normalized * usdc_price
    weth_value = a_weth_balance_normalized * weth_price
    total_value = usdc_value + weth_value

    weth_percent_allocation = weth_value / total_value
    usdc_percent_allocation = usdc_value / total_value
     
    print(f"Current percent allocation of USDC: {usdc_percent_allocation * 100:.2f}%")
    print(f"Current percent allocation of WETH: {weth_percent_allocation * 100:.2f}%")
    print()
    
    return usdc, weth, a_usdc, a_weth

    
def moccasin_main():
    run_script()

    