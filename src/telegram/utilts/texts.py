# More sane way is to store and manage all this in database/json, but we don't really have a bunch of texts

texts_en = {
    "main_menu": "\b🤖 Solana Wallet Tracker Bot\b\n🆙 For more features, you can upgrade to PRO, which allows tracking 50+ wallets.",
    "add_wallets": "Great! You can now add multiple wallets at once. 🚀\n\nSimply send me each wallet address on a new line. If you'd like to assign a nickname (40 characters max) to any wallet, add it after a space following the wallet address. For example:\n\nWalletAddress1 Name1\nWalletAddress2 Name2\nWalletAddress3 Name3\nTip: It might take up to 2 min to start receiving notifications for new wallets!",
    "manage_wallets": "<b>Total SOL wallets: {USER_WALLETS} / {LIMIT}</b>\n✅ - Wallet is active\n⏸️ - You paused this wallet\n⏳ - Wallet was sending too many txs and is paused\n🛑 - Renew PRO to continue tracking this wallet\n<code>-------------------------------------------</code>\n<code>               YOUR WALLETS:               </code>\n<code>-------------------------------------------</code>\n\n{WALLETS_LIST}",
    "delete_wallets": "You can now delete multiple wallets at once. 🚀\nSimply send me each wallet address on a new line 🧹For example:\n\nWalletAddress1\nWalletAddress2\nWalletAddress3\n\nOr click DELETE ALL button below to delete all wallets",
    "add_wallets_message_succ": "✅ Wallet(s) successfully added! Your current wallets:\n\n",
    "add_wallets_message_fail": "✖️ These wallet(s) were not added:\n\n{BAD_WALLETS_LIST}\n\nBecause they are alredy exist or you reached limit of your wallets.\n\nYour current limit: {USER_LIMIT} wallets'",
    "transfer_text": '<a href="{SENDER_WALLET_LINK}">{SENDER_WALLET_NAME}</a>\n{AMOUNT}\n{CURRENCY}\n<a href="{TARGET_WALLET_LINK}">{TARGET_WALLET_NAME}</a>',
    "note_transaction": '<a href="{TRANSACTION_LINK}">Transaction</a> Update for \n\n<b>{WALLET_NAME}</b>\n|<code>{WALLET_ADDRESS}</code>|\n{DESCRIPTION}\n{VALUE_INFO}\nRelated Transfers:{TRANSFERS_LIST}',
    "admin_start": "Welcome to the admin mode. Here you can change bot settings and manage bot users.\n\nTo find user simply send me any username, phone number or user_id.",
    "account_settings": "Transaction Filters\n\nNow you can select which transactions to receive! Include or exclude NFT, swap, transfer, or other transactions by simply clicking on the corresponding buttons!",
    "change_trade_settings": "Send me new value for this settings. Example: 0",
    "note_transaction_second": '{INFO_LINE}\n\n{WALLET_SECTION}\n\n{TRANSACTION_SECTION}\n\n{TOKEN_INFO_SECTION}',
    "token_info_text": "🔗 <b>#{TOKEN_SYMBOL} | {TOKEN_MARKET_CAP}</b>\n{COIN_DATA_LINE}<code>{TOKEN_ADDRESS}</code>",
    "notification_info_line": '<a href="{TRANSACTION_LINK}">{EVENT} {ENTITY_NAME}</a> {WHERE}',
    "notification_wallet_section": '<a href="{WALLET_LINK}">🔹</a> {WALLET_NAME}',
    "wallet_name_with_link": '<a href="{WALLET_LINK}">{WALLET_NAME}</a>',
    "notification_transaction_section": '<a href="{TRANSACTION_LINK}">🔹</a> {DESCRIPTION}',
    "markets_links": 'Seen: {TOKEN_LIFESPAN}: <a href="https://birdeye.so/token/{TOKEN_ADDRESS}?chain=solana">BE</a> | <a href="https://dexscreener.com/solana/{TOKEN_ADDRESS}">DS</a> | <a href="https://www.dextools.io/app/en/solana/pair-explorer/{TOKEN_ADDRESS}">DT</a> | <a href="https://photon-sol.tinyastro.io/en/lp/{TOKEN_ADDRESS}">PH</a> | <a href="https://neo.bullx.io/terminal?chainId=1399811149&address={TOKEN_ADDRESS}">Bullx</a> | <a href="https://www.pump.fun/{TOKEN_ADDRESS}">Pump</a>'
}

# Keys can be used as callback data
keys_en = {
    "add_wallets": "✨ Add",
    "delete_all_wallets": "🛑 DELETE ALL",
    "delete_wallets": "🗑 Delete",
    "back": "🔙 Back"
}
