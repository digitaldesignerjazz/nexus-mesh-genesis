#!/usr/bin/env python3
"""
Minimal Genesis Blockchain for Nexus Mesh Network
=================================================

A minimal but functional implementation of the genesis blockchain layer
for the Nexus Mesh Network.

Features:
- Genesis block creation with defined allocations (matching GENESIS_BLOCK_CONCEPT.md)
- Basic block structure with SHA-256 hashing
- Simple chain validation
- Balance tracking (XCoin)
- Support for simple transactions
- Error handling consistent with GrokNexusActivator
- Hooks for future integration with xMesh routing and Grok AI agent swarms
- Persistence (optional JSON state)

This serves as the foundational prototype for the Nexus blockchain.
It can later be extended with:
- Proof-of-Mesh-Stake consensus
- Reputation-weighted validation
- Native mesh service transactions
- Integration with Grok AI agents for intelligent block proposal/validation

Part of: nexus-mesh-genesis
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path

# =============================================================================
# EXCEPTIONS (consistent style with GrokNexusActivator)
# =============================================================================
class BlockchainError(Exception):
    """Base exception for Nexus blockchain operations."""
    pass

class InvalidBlockError(BlockchainError):
    """Raised when a block fails validation."""
    pass

class GenesisError(BlockchainError):
    """Raised when genesis block creation or validation fails."""
    pass

class TransactionError(BlockchainError):
    """Raised for invalid transactions."""
    pass


# =============================================================================
# DATA STRUCTURES
# =============================================================================
@dataclass
class Transaction:
    """Simple transaction structure."""
    sender: str
    recipient: str
    amount: float
    timestamp: float = field(default_factory=time.time)
    mesh_metadata: Dict[str, Any] = field(default_factory=dict)  # e.g. routing info, service type

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Block:
    """Block in the Nexus blockchain."""
    index: int
    timestamp: float
    previous_hash: str
    transactions: List[Transaction]
    nonce: int = 0
    hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block contents."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "hash": self.hash
        }


# =============================================================================
# MINIMAL GENESIS BLOCKCHAIN
# =============================================================================
class MinimalGenesisBlockchain:
    """
    Minimal implementation of the Nexus Mesh genesis blockchain.

    Creates the genesis block according to the defined economic parameters
    and allows adding subsequent blocks with basic validation.
    """

    # Genesis parameters (from GENESIS_BLOCK_CONCEPT.md)
    GENESIS_SUPPLY = 21_000_000
    GENESIS_ALLOCATIONS = {
        "infrastructure": 8_400_000,
        "founding": 5_250_000,
        "early_participants": 4_200_000,
        "ai_swarm_fund": 2_100_000,
        "privacy_reserve": 1_050_000,
    }

    def __init__(self, persistence_path: Optional[str] = None):
        self.chain: List[Block] = []
        self.balances: Dict[str, float] = {}
        self.persistence_path = Path(persistence_path) if persistence_path else None

        # Create genesis block on initialization
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Create and add the genesis block with initial allocations."""
        genesis_transactions = []

        # Create allocation transactions from "genesis" source
        for recipient, amount in self.GENESIS_ALLOCATIONS.items():
            tx = Transaction(
                sender="genesis",
                recipient=recipient,
                amount=amount,
                mesh_metadata={"type": "genesis_allocation", "category": recipient}
            )
            genesis_transactions.append(tx)
            self.balances[recipient] = amount

        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            previous_hash="0" * 64,  # Genesis has no previous
            transactions=genesis_transactions,
            nonce=0
        )
        genesis_block.hash = genesis_block.calculate_hash()

        self.chain.append(genesis_block)
        print(f"[Genesis] Created genesis block with hash: {genesis_block.hash[:16]}...")

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, transactions: List[Transaction]) -> Block:
        """
        Add a new block to the chain after validation.
        For minimal version: simple previous_hash check + balance validation.
        """
        if not transactions:
            raise TransactionError("Cannot add empty block")

        # Basic validation: check balances (prevent overspending in this minimal model)
        temp_balances = self.balances.copy()
        for tx in transactions:
            if tx.sender != "genesis" and temp_balances.get(tx.sender, 0) < tx.amount:
                raise TransactionError(f"Insufficient balance for {tx.sender}")
            if tx.sender != "genesis":
                temp_balances[tx.sender] -= tx.amount
            temp_balances[tx.recipient] = temp_balances.get(tx.recipient, 0) + tx.amount

        previous_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            previous_hash=previous_block.hash,
            transactions=transactions
        )
        new_block.hash = new_block.calculate_hash()

        # Mine a simple nonce (proof-of-work simulation for minimal version)
        new_block = self._simple_mine(new_block)

        self.chain.append(new_block)
        self.balances = temp_balances  # Commit balances

        if self.persistence_path:
            self._save_state()

        return new_block

    def _simple_mine(self, block: Block, difficulty: int = 2) -> Block:
        """Very simple proof-of-work simulation (for demo purposes)."""
        prefix = "0" * difficulty
        while not block.hash.startswith(prefix):
            block.nonce += 1
            block.hash = block.calculate_hash()
        return block

    def is_chain_valid(self) -> bool:
        """Validate the entire chain integrity."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.calculate_hash():
                return False
        return True

    def get_balance(self, address: str) -> float:
        return self.balances.get(address, 0.0)

    def get_chain_summary(self) -> Dict[str, Any]:
        """Return a summary of the current chain state."""
        return {
            "length": len(self.chain),
            "latest_hash": self.get_latest_block().hash[:16] + "...",
            "is_valid": self.is_chain_valid(),
            "total_supply": sum(self.balances.values()),
            "balances": self.balances,
            "genesis_timestamp": self.chain[0].timestamp
        }

    def _save_state(self):
        """Persist chain and balances to JSON (optional)."""
        if not self.persistence_path:
            return
        state = {
            "chain": [block.to_dict() for block in self.chain],
            "balances": self.balances
        }
        with open(self.persistence_path, "w") as f:
            json.dump(state, f, indent=2)

    # =========================================================================
    # INTEGRATION HOOKS (for Grok AI agents and xMesh)
    # =========================================================================
    def propose_block_via_agent(self, agent_role: str, transactions: List[Transaction]) -> Optional[Block]:
        """
        Hook for Grok Nexus agents to propose blocks.
        In a full implementation, this would involve agent consensus / validation.
        """
        print(f"[Agent Hook] {agent_role} proposing block with {len(transactions)} transaction(s)")
        try:
            return self.add_block(transactions)
        except Exception as e:
            print(f"[Agent Hook] Block proposal failed: {e}")
            return None


# =============================================================================
# DEMO / STANDALONE USAGE
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("NEXUS MESH NETWORK — MINIMAL GENESIS BLOCKCHAIN DEMO")
    print("=" * 70)

    # Initialize blockchain (creates genesis automatically)
    nexus_chain = MinimalGenesisBlockchain()

    print("\n--- Genesis State ---")
    summary = nexus_chain.get_chain_summary()
    print(json.dumps(summary, indent=2, default=str))

    # Example: Simulate some activity (e.g. infrastructure node spending)
    print("\n--- Adding sample transactions ---")
    try:
        tx1 = Transaction(
            sender="infrastructure",
            recipient="early_participants",
            amount=500_000,
            mesh_metadata={"type": "mesh_service_payment", "service": "routing_credits"}
        )
        tx2 = Transaction(
            sender="ai_swarm_fund",
            recipient="Coordinator",
            amount=100_000,
            mesh_metadata={"type": "ai_agent_incentive", "agent_role": "Coordinator"}
        )

        new_block = nexus_chain.add_block([tx1, tx2])
        print(f"New block added: index={new_block.index}, hash={new_block.hash[:16]}...")
    except TransactionError as e:
        print(f"Transaction failed: {e}")

    print("\n--- Updated Chain Summary ---")
    updated_summary = nexus_chain.get_chain_summary()
    print(json.dumps(updated_summary, indent=2, default=str))

    print("\n--- Chain Validation ---")
    print(f"Chain valid: {nexus_chain.is_chain_valid()}")

    print("\n" + "=" * 70)
    print("Minimal Genesis Blockchain ready for Nexus Mesh integration.")
    print("=" * 70)
