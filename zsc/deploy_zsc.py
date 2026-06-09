#!/usr/bin/env python3
"""
ZeroShield Coin (ZSC) — Deployment script for Base mainnet (Chain ID 8453)

Usage:
    pip install web3 py-solcx
    export PRIVATE_KEY=0x...your_deployer_private_key
    export RPC_URL=https://mainnet.base.org
    python3 deploy_zsc.py
"""

import os, sys, json
from web3 import Web3

GENESIS_WALLET = "0x6804b4ff1a85448d654f31db830f3e25277afb78"
CHAIN_ID = 8453

RPC_URL = os.environ.get("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")

def compile_contract(sol_path: str):
    try:
        import solcx
    except ImportError:
        print("Installing py-solcx ...")
        os.system(f"{sys.executable} -m pip install py-solcx")
        import solcx

    solcx.install_solc("0.8.20")
    solcx.set_solc_version("0.8.20")

    with open(sol_path, "r") as f:
        source = f.read()

    compiled = solcx.compile_source(
        source, output_values=["abi", "bin"], solc_version="0.8.20"
    )

    contract_key = None
    for key in compiled:
        if ":ZeroShieldCoin" in key:
            contract_key = key
            break

    if contract_key is None:
        raise RuntimeError("ZeroShieldCoin contract not found in compilation output")

    return compiled[contract_key]["abi"], compiled[contract_key]["bin"]


def main():
    if not PRIVATE_KEY:
        print("ERROR: PRIVATE_KEY env var is not set.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"ERROR: Cannot connect to {RPC_URL}")
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"Deployer: {account.address}")
    print(f"Balance: {Web3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

    sol_path = os.path.join(os.path.dirname(__file__), "contracts", "ZSC.sol")
    print("Compiling ZSC.sol ...")
    abi, bytecode = compile_contract(sol_path)
    print(f"Compilation OK — bytecode length: {len(bytecode)}")

    ZSC = w3.eth.contract(abi=abi, bytecode=bytecode)
    constructor_tx = ZSC.constructor()

    try:
        estimated_gas = constructor_tx.estimate_gas({"from": account.address})
    except Exception as e:
        print(f"Gas estimation failed: {e}, using fallback 5,000,000")
        estimated_gas = 5_000_000

    gas_limit = int(estimated_gas * 1.3)
    nonce = w3.eth.get_transaction_count(account.address)

    tx = constructor_tx.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": gas_limit,
        "chainId": w3.eth.chain_id,
    })

    signed = account.sign_transaction(tx)
    print("Broadcasting ...")
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Tx hash: {tx_hash.hex()}")
    print(f"BaseScan: https://basescan.org/tx/0x{tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

    if receipt.status == 1:
        addr = receipt.contractAddress
        print(f"\n✅ ZSC Deployment SUCCESSFUL!")
        print(f"   Contract: {addr}")
        print(f"   Gas used: {receipt.gasUsed}")
        print(f"   BaseScan: https://basescan.org/address/{addr}")

        info = {
            "network": "base", "chainId": w3.eth.chain_id,
            "contract": addr, "deployer": account.address,
            "genesisWallet": GENESIS_WALLET,
            "txHash": tx_hash.hex(), "blockNumber": receipt.blockNumber,
            "gasUsed": receipt.gasUsed, "abi": abi,
        }
        out = os.path.join(os.path.dirname(__file__), "zsc_deployment.json")
        with open(out, "w") as f:
            json.dump(info, f, indent=2)
        print(f"   Saved to: {out}")
    else:
        print("\n❌ Deployment FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
