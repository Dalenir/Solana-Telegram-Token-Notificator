from ..keyboards.inline import get_user_main_btns, get_callback_btns


async def main_menu(level, menu_name):
    text = """
🤖 Solana Wallet Tracker Bot
🆙 For more features, you can upgrade to PRO, which allows tracking 50+ wallets.
    """
    kbds = get_user_main_btns(level=level)
    return text, kbds


async def add_wallet():
    text = """
Great! You can now add multiple wallets at once. 🚀

Simply send me each wallet address on a new line. If you'd like to assign a nickname (40 characters max) to any wallet, add it after a space following the wallet address. For example:

WalletAddress1 Name1
WalletAddress2 Name2
WalletAddress3 Name3

Tip: It might take up to 2 min to start receiving notifications for new wallets!
    """

    kbds = get_callback_btns(
        level=0,
        btns={"🔙 Back": "main"},
        sizes=(1, 1)
    )
    return text, kbds


async def get_menu_content(level, menu_name):
    if level == 0:
        return await main_menu(level, menu_name)
    elif level == 1 and menu_name == "add":
        return await add_wallet()
