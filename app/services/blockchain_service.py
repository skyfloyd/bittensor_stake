from typing import Optional, Dict, Any, List, Union, Tuple
import os
from datetime import datetime
import asyncio
from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.settings import SS58_FORMAT
from ..core.config import get_settings
from .redis_service import redis_service

settings = get_settings()

class BlockchainError(Exception):
    """Base exception for blockchain service errors."""
    pass

class ConnectionError(BlockchainError):
    """Raised when there are connection issues with the blockchain."""
    pass

class QueryError(BlockchainError):
    """Raised when there are issues with blockchain queries."""
    pass

class DecodingError(BlockchainError):
    """Raised when there are issues decoding blockchain data."""
    pass

class BlockchainService:
    def __init__(self):
        """Initialize the authentication manager."""
        self.default_hotkey = settings.DEFAULT_HOTKEY
        self.default_netuid = settings.DEFAULT_NETUID
        self.substrate_url = f"wss://entrypoint-{settings.BITTENSOR_NETWORK}.opentensor.ai:443"
        
    async def _get_substrate(self):
        """Get an AsyncSubstrateInterface instance."""
        try:
            return AsyncSubstrateInterface(
                self.substrate_url,
                ss58_format=SS58_FORMAT
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create substrate interface: {str(e)}")

    async def _exhaust_query_map(self, query_map):
        """Exhaust a query_map iterator."""
        try:
            results = []
            async for k, v in await query_map:
                results.append((k, v))
            return results
        except Exception as e:
            raise QueryError(f"Failed to exhaust query map: {str(e)}")

    async def get_tao_dividends(
        self,
        netuid: Optional[int] = None,
        hotkey: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query Tao dividends from the Bittensor blockchain.
        If netuid is None, returns data for all netuids.
        If hotkey is None, returns data for all hotkeys on the specified netuid.
        """
        try:
            # Try to get cached data first
            cached_data = await redis_service.get_cached_dividends(netuid, hotkey)
            if cached_data:
                cached_data["cached"] = True
                return cached_data

            # If netuid is not provided, get data for all netuids
            if netuid is None:
                all_netuids = await self.get_all_netuids()
                if isinstance(all_netuids, dict) and "error" in all_netuids:
                    return all_netuids

                results = []
                for netuid in all_netuids:
                    netuid_data = await self._get_netuid_dividends(netuid, hotkey)
                    if "error" not in netuid_data:
                        results.append(netuid_data)
                
                return {
                    "all_netuids": results,
                    "cached": False,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            # If hotkey is not provided, get data for all hotkeys in the netuid
            if hotkey is None:
                return await self._get_netuid_dividends(netuid)

            # Get specific hotkey data
            return await self._get_specific_dividend(netuid, hotkey)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividend": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cached": False,
                "error": error_msg
            }

    async def _get_netuid_dividends(self, netuid: int, hotkey: Optional[str] = None) -> Dict[str, Any]:
        """Get dividends data for a specific netuid."""
        try:
            async with await self._get_substrate() as substrate:
                block_hash = await substrate.get_chain_head()
                query_map = substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    [netuid],
                    block_hash=block_hash
                )
                
                results = await self._exhaust_query_map(query_map)
                
                # Find the specific hotkey result if provided
                if hotkey:
                    for k, v in results:
                        if decode_account_id(k) == hotkey:
                            dividend_value = float(v.value) / 1e9  # Convert from raw to TAO
                            result_data = {
                                "netuid": netuid,
                                "hotkey": hotkey,
                                "dividend": dividend_value,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "cached": False
                            }
                            # Cache the result
                            await redis_service.cache_dividends(netuid, result_data, hotkey)
                            return result_data
                    return {
                        "netuid": netuid,
                        "hotkey": hotkey,
                        "dividend": 0.0,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "cached": False,
                        "error": "No dividend data found for this hotkey"
                    }
                
                # Return all hotkeys for the netuid
                result_data = {
                    "netuid": netuid,
                    "results": [
                        {
                            "hotkey": decode_account_id(k),
                            "dividend": float(v.value) / 1e9,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                        for k, v in results
                    ],
                    "cached": False,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                # Cache the results
                await redis_service.cache_dividends(netuid, result_data)
                return result_data

        except Exception as e:
            error_msg = f"Error getting netuid dividends: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividend": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cached": False,
                "error": error_msg
            }

    async def _get_specific_dividend(self, netuid: int, hotkey: str) -> Dict[str, Any]:
        """Get specific dividend data for a netuid and hotkey."""
        try:
            async with await self._get_substrate() as substrate:
                block_hash = await substrate.get_chain_head()
                query_map = substrate.query_map(
                    "SubtensorModule",
                    "TaoDividendsPerSubnet",
                    [netuid],
                    block_hash=block_hash
                )
                
                results = await self._exhaust_query_map(query_map)
                
                for k, v in results:
                    if decode_account_id(k) == hotkey:
                        dividend_value = float(v.value) / 1e9
                        result_data = {
                            "netuid": netuid,
                            "hotkey": hotkey,
                            "dividend": dividend_value,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "cached": False
                        }
                        await redis_service.cache_dividends(netuid, result_data, hotkey)
                        return result_data
                
                return {
                    "netuid": netuid,
                    "hotkey": hotkey,
                    "dividend": 0.0,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "cached": False,
                    "error": "No dividend data found for this hotkey"
                }

        except Exception as e:
            error_msg = f"Error getting specific dividend: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {
                "netuid": netuid,
                "hotkey": hotkey,
                "dividend": 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cached": False,
                "error": error_msg
            }

    
    async def get_all_netuids(self) -> Union[List[int], Dict[str, Any]]:
        """
        Get a list of all available netuids.
        """
        try:
            async with await self._get_substrate() as substrate:
                block_hash = await substrate.get_chain_head()
                result = await substrate.query(
                    "SubtensorModule",
                    "NetworksAdded",
                    block_hash=block_hash
                )
                if result and hasattr(result, 'value'):
                    return list(range(1, result.value + 1))
                return []
        except ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "netuids": []}
        except QueryError as e:
            error_msg = f"Query error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "netuids": []}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "netuids": []}

    async def get_hotkeys_for_netuid(self, netuid: int) -> Union[List[str], Dict[str, Any]]:
        """
        Get all hotkeys registered on a specific netuid.
        """
        try:
            async with await self._get_substrate() as substrate:
                block_hash = await substrate.get_chain_head()
                query_map = substrate.query_map(
                    "SubtensorModule",
                    "Stake",
                    [netuid],
                    block_hash=block_hash
                )
                results = await self._exhaust_query_map(query_map)
                hotkeys = [decode_account_id(k) for k, _ in results]
                print("Hotkeys found:", hotkeys)  # Print the results
                return hotkeys
        except ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "hotkeys": []}
        except QueryError as e:
            error_msg = f"Query error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "hotkeys": []}
        except DecodingError as e:
            error_msg = f"Decoding error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "hotkeys": []}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"error": error_msg, "hotkeys": []} 