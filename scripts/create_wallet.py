from bittensor_wallet import Wallet

def create_wallet():
    """Create a new bittensor wallet."""
    wallet = Wallet()
    wallet.create()
    print(f"Wallet created successfully!")
    print(f"Name: {wallet.name}")
    print(f"Hotkey: {wallet.hotkey}")
    print(f"Path: {wallet.path}")

if __name__ == "__main__":
    create_wallet() 