# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
import pytest
from script.rebalance_portfolio import (
    run_script,
    moccasin_main,
    deposit,
    get_price,
    print_usdc_weth_token_balances,
    calculate_rebalancing_trades,
    STARTING_ETH_BALANCE,
    STARTING_WETH_BALANCE,
    STARTING_USDC_BALANCE,
)
import boa

# ------------------------------------------------------------------
#                         TESTS_FUNCTIONS
# ------------------------------------------------------------------
def test_run_script_returns_contracts(active_network):
    """Verify run_script returns USDC, WETH, aUSDC, and aWETH contracts."""
    if active_network.is_local_or_forked_network():
        usdc, weth, a_usdc, a_weth = run_script()
        
        assert usdc is not None
        assert weth is not None
        assert a_usdc is not None
        assert a_weth is not None


def test_moccasin_main_executes(active_network):
    """Verify moccasin_main executes without errors."""
    if active_network.is_local_or_forked_network():
        result = moccasin_main()
        assert result is None


def test_deposit_approves_and_deposits(active_network):
    """Verify deposit function approves and deposits tokens to Aave pool."""
    if active_network.is_local_or_forked_network():
        usdc = active_network.manifest_named("usdc")
        pool_address_provider = active_network.manifest_named("aavev3_pool_address_provider")
        pool_address = pool_address_provider.getPool()
        pool_contract = active_network.manifest_named("pool", address=pool_address)
        
        # Mint some USDC for testing
        our_address = boa.env.eoa
        with boa.env.prank(usdc.owner()):
            usdc.updateMasterMinter(our_address)
        usdc.configureMinter(our_address, STARTING_USDC_BALANCE)
        usdc.mint(our_address, STARTING_USDC_BALANCE)
        
        initial_balance = usdc.balanceOf(our_address)
        deposit(pool_contract, usdc, initial_balance)
        
        # Balance should be zero after deposit
        assert usdc.balanceOf(our_address) == 0


def test_get_price_returns_positive_value(active_network):
    """Verify get_price returns a positive price for USDC and ETH."""
    usdc_price = get_price("usdc_usd")
    eth_price = get_price("eth_usd")
    
    assert usdc_price > 0
    assert eth_price > 0
    # USDC should be close to $1
    assert 0.95 < usdc_price < 1.05
    # ETH should be > $100 (reasonable lower bound)
    assert eth_price > 100


def test_print_usdc_weth_token_balances_executes(active_network, capsys):
    """Verify print_usdc_weth_token_balances prints balances."""
    print_usdc_weth_token_balances()
    
    captured = capsys.readouterr()
    assert "Balances:" in captured.out
    assert "USDC balance:" in captured.out
    assert "WETH balance:" in captured.out


def test_calculate_rebalancing_trades_with_balanced_portfolio():
    """Verify calculate_rebalancing_trades returns zero trades when balanced."""
    usdc_data = {"balance": 300, "price": 1.0, "contract": None}
    weth_data = {"balance": 0.2, "price": 3500, "contract": None}  # $700
    target_allocations = {"usdc": 0.3, "weth": 0.7}
    
    trades = calculate_rebalancing_trades(usdc_data, weth_data, target_allocations)
    
    # Should need minimal trades since already balanced
    assert abs(trades["usdc"]["trade"]) < 10
    assert abs(trades["weth"]["trade"]) < 0.01


def test_calculate_rebalancing_trades_with_unbalanced_portfolio():
    """Verify calculate_rebalancing_trades calculates correct trades when unbalanced."""
    # 100% in USDC, need to rebalance to 30/70
    usdc_data = {"balance": 1000, "price": 1.0, "contract": None}  # $1000
    weth_data = {"balance": 0, "price": 3500, "contract": None}    # $0
    target_allocations = {"usdc": 0.3, "weth": 0.7}
    
    trades = calculate_rebalancing_trades(usdc_data, weth_data, target_allocations)
    
    # Should sell USDC (negative trade) and buy WETH (positive trade)
    assert trades["usdc"]["trade"] < 0  # Sell USDC
    assert trades["weth"]["trade"] > 0  # Buy WETH
    
    # USDC trade should be around -700 (sell 700 USDC)
    assert -750 < trades["usdc"]["trade"] < -650
    # WETH trade should be around 0.2 (buy 0.2 WETH at $3500)
    assert 0.15 < trades["weth"]["trade"] < 0.25


def test_calculate_rebalancing_trades_allocations_sum_to_one():
    """Verify calculate_rebalancing_trades works when allocations sum to 1."""
    usdc_data = {"balance": 500, "price": 1.0, "contract": None}
    weth_data = {"balance": 0.5, "price": 1000, "contract": None}
    target_allocations = {"usdc": 0.5, "weth": 0.5}  # Sum = 1.0
    
    trades = calculate_rebalancing_trades(usdc_data, weth_data, target_allocations)
    
    assert "usdc" in trades
    assert "weth" in trades
    assert "trade" in trades["usdc"]
    assert "trade" in trades["weth"]


def test_calculate_rebalancing_trades_preserves_total_value():
    """Verify rebalancing trades preserve total portfolio value."""
    usdc_data = {"balance": 600, "price": 1.0, "contract": None}   # $600
    weth_data = {"balance": 0.1, "price": 4000, "contract": None}  # $400
    # Total: $1000
    target_allocations = {"usdc": 0.3, "weth": 0.7}
    
    trades = calculate_rebalancing_trades(usdc_data, weth_data, target_allocations)
    
    # Calculate new values after trades
    new_usdc_balance = usdc_data["balance"] + trades["usdc"]["trade"]
    new_weth_balance = weth_data["balance"] + trades["weth"]["trade"]
    
    new_usdc_value = new_usdc_balance * usdc_data["price"]
    new_weth_value = new_weth_balance * weth_data["price"]
    new_total = new_usdc_value + new_weth_value
    
    original_total = 1000
    
    # Total value should be preserved (within floating point precision)
    assert abs(new_total - original_total) < 1


def test_run_script_returns_four_contracts(rebalance_contracts):
    """Verify run_script returns USDC, WETH, aUSDC, and aWETH contracts."""
    usdc, weth, a_usdc, a_weth = rebalance_contracts
    
    assert usdc is not None
    assert weth is not None
    assert a_usdc is not None
    assert a_weth is not None


# ------------------------------------------------------------------
#                     TESTS_FUNCTIONS_CONFTEST
# ------------------------------------------------------------------
def test_setup_fixture_returns_contracts(setup):
    """Verify setup fixture returns USDC and WETH contracts."""
    usdc, weth = setup
    assert usdc is not None
    assert weth is not None


def test_active_network_fixture(active_network):
    """Verify active_network fixture returns network configuration."""
    assert active_network is not None
    assert hasattr(active_network, 'is_local_or_forked_network')


def test_contracts_fixture_returns_two_contracts(contracts):
    """Verify contracts fixture returns USDC and WETH."""
    usdc, weth = contracts
    assert usdc is not None
    assert weth is not None
    assert hasattr(usdc, 'balanceOf')
    assert hasattr(weth, 'balanceOf')


def test_aave_contracts_fixture_returns_pool_contracts(aave_contracts):
    """Verify aave_contracts fixture returns pool contract and provider."""
    pool_contract, pool_address_provider = aave_contracts
    assert pool_contract is not None
    assert pool_address_provider is not None
    assert hasattr(pool_contract, 'supply')
    assert hasattr(pool_address_provider, 'getPool')


def test_rebalance_contracts_fixture_on_local_network(rebalance_contracts, active_network):
    """Verify rebalance_contracts fixture returns all 4 contracts on local network."""
    if active_network.is_local_or_forked_network():
        usdc, weth, a_usdc, a_weth = rebalance_contracts
        assert usdc is not None
        assert weth is not None
        assert a_usdc is not None
        assert a_weth is not None


