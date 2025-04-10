import logging
from app.core.config import get_settings

print("Importing bittensor")

# import bittensor as bt
from bittensor_wallet.wallet import Wallet

print("bittensor imported")

from typing import Dict, Any, Optional


settings = get_settings()

# Configure logging
logger = logging.getLogger(__name__)

class StakeService:
    def __init__(self):
        self.wallet = None
        self.subtensor = None
        self.testnet_wallet_mnemonic = settings.WALLET_SEED
        self.datura_api_key = settings.DATURA_API_KEY
        self.chutes_api_key = settings.CHUTES_API_KEY
        self.wallet_name = settings.WALLET_NAME
        self.wallet_hotkey = settings.WALLET_HOTKEY
        self.wallet_path = settings.WALLET_PATH

    def _get_subtensor(self):
        """Lazy load subtensor instance."""
        if self.subtensor is None:
            from bittensor import AsyncSubtensor
            self.subtensor = AsyncSubtensor(network="test")
        return self.subtensor

    async def initialize_wallet(self) -> None:
        """Initialize the wallet using the testnet mnemonic."""
        try:
            if self.wallet is None:
                # Create wallet using btwallet SDK
                self.wallet = Wallet(
                    name=self.wallet_name,
                    hotkey=self.wallet_hotkey,
                    path=self.wallet_path
                )
                logger.info("Wallet initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {str(e)}")
            raise

    async def ensure_testnet_balance(self) -> None:
        """Ensure the wallet has sufficient testnet tokens."""
        try:
            if not self.wallet:
                await self.initialize_wallet()

            subtensor = self._get_subtensor()
            balance = await subtensor.get_balance(self.wallet.coldkeypub.ss58_address)
            if balance < 40:  # If balance is less than 40 tao
                logger.info("Transferring testnet tokens...")
                # Transfer tokens from the test wallet
                await subtensor.transfer(
                    wallet=self.wallet,
                    dest=self.wallet.coldkeypub.ss58_address,
                    amount=40,
                    wait_for_inclusion=True
                )
                logger.info("Testnet tokens transferred successfully")
        except Exception as e:
            logger.error(f"Failed to ensure testnet balance: {str(e)}")
            raise

    async def add_stake(self, netuid: int, hotkey: str, amount: float) -> Dict[str, Any]:
        print("Adding stake netuid: ", netuid, " hotkey: ", hotkey, " amount: ", amount)
        """
        Add stake to a hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            amount: Amount of TAO to stake
            
        Returns:
            Dict containing operation results
        """
        try:
            if not self.wallet:
                await self.initialize_wallet()
            
            print("Ensuring testnet balance")

            await self.ensure_testnet_balance()

            print(f"Adding stake of {amount} TAO to hotkey {hotkey} on netuid {netuid}")

            logger.info(f"Adding stake of {amount} TAO to hotkey {hotkey} on netuid {netuid}")
            
            # Add stake using AsyncSubtensor
            subtensor = self._get_subtensor()
            result = await subtensor.add_stake(
                wallet=self.wallet,
                hotkey_ss58=hotkey,
                amount=amount,
                wait_for_inclusion=True
            )

            logger.info(f"Stake added successfully: {result}")
            return {
                "success": True,
                "operation": "add_stake",
                "amount": amount,
                "hotkey": hotkey,
                "netuid": netuid,
                "result": result
            }

        except Exception as e:
            logger.error(f"Failed to add stake: {str(e)}")
            return {
                "success": False,
                "operation": "add_stake",
                "error": str(e)
            }

    async def remove_stake(self, netuid: int, hotkey: str, amount: float) -> Dict[str, Any]:
        """
        Remove stake from a hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            amount: Amount of TAO to unstake
            
        Returns:
            Dict containing operation results
        """
        try:
            if not self.wallet:
                await self.initialize_wallet()

            logger.info(f"Removing stake of {amount} TAO from hotkey {hotkey} on netuid {netuid}")
            
            # Remove stake using AsyncSubtensor
            subtensor = self._get_subtensor()
            result = await subtensor.unstake(
                wallet=self.wallet,
                hotkey_ss58=hotkey,
                amount=amount,
                wait_for_inclusion=True
            )

            logger.info(f"Stake removed successfully: {result}")
            return {
                "success": True,
                "operation": "remove_stake",
                "amount": amount,
                "hotkey": hotkey,
                "netuid": netuid,
                "result": result
            }

        except Exception as e:
            logger.error(f"Failed to remove stake: {str(e)}")
            return {
                "success": False,
                "operation": "remove_stake",
                "error": str(e)
            }

    async def get_stake_info(self, netuid: int, hotkey: str) -> Dict[str, Any]:
        """
        Get stake information for a hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            
        Returns:
            Dict containing stake information
        """
        try:
            if not self.wallet:
                await self.initialize_wallet()

            # Get stake information
            subtensor = self._get_subtensor()
            stake = await subtensor.get_stake_for_coldkey_and_hotkey(
                hotkey_ss58=hotkey,
                coldkey_ss58=self.wallet.coldkeypub.ss58_address
            )

            return {
                "success": True,
                "stake": stake,
                "hotkey": hotkey,
                "netuid": netuid
            }

        except Exception as e:
            logger.error(f"Failed to get stake info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }