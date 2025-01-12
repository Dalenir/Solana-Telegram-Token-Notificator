from config import SolanaNetworkMode
from core.models import Wallet


def wallet_list_text(wallets: list[Wallet]):
    wallets_listed_text = ""

    for i, wallet in enumerate(wallets):
        wallets_listed_text += f"{i}: ✅ {wallet.name} <code>{wallet.address}</code>\n"

    return wallets_listed_text


class ExplorerLinks:
    _explorer_url = "https://solscan.io"
    mode = SolanaNetworkMode

    def __init__(self, mode: SolanaNetworkMode):
        self.mode = mode

    def get_address_link(self, address: str):
        return self._add_mode(f"{self._explorer_url}/account/{address}")

    def get_transaction_link(self, transaction_hash: str):
        return self._add_mode(f"{self._explorer_url}/tx/{transaction_hash}")

    def _add_mode(self, link: str):
        if self.mode == SolanaNetworkMode.DEV:
            return link + f"?cluster=devnet"
        else:
            return link


def truncate_address(address: str):
    if len(address) > 11:
        address = address[0:4] + "..." + address[-4:]
    return address
