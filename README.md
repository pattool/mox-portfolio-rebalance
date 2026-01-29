# Mox Algorithmic Trading

🐍 Welcome to the Portfolio Rebalance project!

## What we want to do:
1. Deposit into Aave : get % yield
2. Withdraw from Aave
3. Trade tokens through Uniswap for rebalancing portfolio:
   - Allocation: 30% USDC and 70% ETHs
5. Redeposit into Aave: get % yield

## Quickstart

1. Deploy to a fake local network that titanoboa automatically spins up!

```bash
mox run rebalance_portfolio --network eth-forked
```

2. Run tests 

```
mox test -s
```

_For documentation, please run `mox --help` or visit [the Moccasin documentation](https://cyfrin.github.io/moccasin)_
