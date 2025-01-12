import re
from datetime import datetime
from enum import Enum
from typing import List

from datetime import timedelta
from aiogram import Bot
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import SolanaNetworkMode
from core.models import Wallet, UserData
from core.services import WalletsService
from core.services.solana import SolanaTransactionData, SolanaTransfer, SolanaTokenTransfer
from core.services.solana.models import TransactionType, Token, NewSolanaTransactionData, SolanaAccountChangeData, \
    HeliusSolanaTransactionData, TokenChange
from telegram.utilts.text_utilts import ExplorerLinks, truncate_address
from telegram.utilts.texts import texts_en


class SpotlightTransaction(BaseModel):
    token: Token
    type: TransactionType
    source: str


class NotificationData(BaseModel):
    wallet: Wallet
    transfers: List[SolanaTransfer] | None = None
    description: str | None = None
    total_sol_value: float = 0
    biggest_market_cap: float = 0
    source: str | None = None
    type: TransactionType


class NewNotificationData(BaseModel):
    wallet: Wallet
    user: UserData
    helius_transaction_data: HeliusSolanaTransactionData


class WhatNotification(Enum):
    SWAP = "🔁 SWAP"
    TRANSFER_TO = "💸 TRANSFER"
    TRANSFER_FROM = "💸 TRANSFER"
    TRANSFER = "💸 TRANSFER"
    SELL = "🔴 SELL"
    BUY = "🟢 BUY"
    MINT = "🤌 MINT"


class WithWhatNotification(Enum):
    MULTIPLE_TOKENS = "MULTIPLE TOKENS"
    TOKEN = "TOKEN"
    SOL = "SOL"


class WhereNotification(Enum):
    RAYDIUM = 'RAYDIUM'
    PUMP_FUN = 'PUMP FUN'
    JUPITER = 'JUPITER'
    ORCA = 'ORCA'
    METEORA = 'METEORA'
    SYSTEM_PROGRAM = 'sytem program'


class NotificationEvent(BaseModel):
    what: WhatNotification
    where: WhereNotification | None
    with_what: WithWhatNotification


class TransactionNotificator:
    bot: Bot
    mode: SolanaNetworkMode
    sessionmaker: async_sessionmaker

    def __init__(self, bot: Bot,
                 mode: SolanaNetworkMode,
                 sessionmaker: async_sessionmaker):
        self.bot = bot
        self.mode = mode
        self.sessionmaker = sessionmaker

    async def notify_wallet_owners(self, transaction):
        prepared_sending_data = await self.filter_and_prepare(transaction)
        for sending_target in prepared_sending_data:
            await self.new_send_notification(sending_target)

    async def filter_and_prepare(self, transaction: HeliusSolanaTransactionData) -> list[NewNotificationData]:

        wallets_with_users_list = await (WalletsService(self.sessionmaker)
                                         .get_wallets_with_users(addresses=list(transaction.accounts_changes.keys())))
        return_list: list[NewNotificationData] = list()

        for wallet, user in wallets_with_users_list:
            # Filtering will happen here

            account_changes_wallet = transaction.accounts_changes.get(wallet.address)

            # We are dropping a very small transactions in SOL (gas)
            if abs(account_changes_wallet.native_change) < 100000 and not account_changes_wallet.token_changes:
                continue

            # Also we must share only the one account change, but right now let it be all changes, just in case.
            return_list.append(NewNotificationData(
                wallet=wallet,
                user=user,
                helius_transaction_data=transaction
            ))
        return return_list

    @staticmethod
    def format_large_number(number):
        if number >= 1e9:  # Billions
            billions = int(number // 1e9)
            millions = int((number % 1e9) // 1e6)
            return f"{billions}b {millions}m" if millions else f"{billions}b"
        elif number >= 1e6:  # Millions
            millions = int(number // 1e6)
            thousands = int((number % 1e6) // 1e3)
            return f"{millions}m {thousands}k" if thousands else f"{millions}m"
        elif number >= 1e3:  # Thousands
            thousands = int(number // 1e3)
            return f"{thousands}k"
        else:  # Less than a thousand
            return str(int(number))

    @staticmethod
    def format_token_lifetime(td: timedelta):
        total_seconds = td.total_seconds()

        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        # Build parts list
        parts = []

        if days > 0:
            parts.append(f"{days}d.")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h.")
        if minutes > 0 and days == 0:
            parts.append(f"{minutes}m.")
        if seconds > 0 and (days == 0 or minutes == 0):
            parts.append(f"{seconds}s.")

        return " ".join(parts)

    async def new_send_notification(self, sending_data: NewNotificationData):
        notification_text = texts_en.get("note_transaction_second")
        link_utilts = ExplorerLinks(mode=self.mode)

        token_info_text_line = ""

        account_changes = (sending_data.helius_transaction_data.accounts_changes
                           .get(sending_data.wallet.address))

        event: NotificationEvent = self._decide_event(
            account_changes,
            sending_data.helius_transaction_data.source,
            sending_data.helius_transaction_data.description
        )

        transaction_link = link_utilts.get_transaction_link(sending_data.helius_transaction_data.hash)
        info_line = self._form_info_line(event, account_changes, transaction_link=transaction_link)

        wallet_section = texts_en.get('notification_wallet_section')
        wallet_name = truncate_address(sending_data.wallet.name)
        wallet_section = wallet_section.format(
            WALLET_LINK=link_utilts.get_address_link(sending_data.wallet.address),
            WALLET_NAME=wallet_name,
            WALLET_ADDRESS=sending_data.wallet.address
        )

        transaction_section = texts_en.get("notification_transaction_section")
        description = sending_data.helius_transaction_data.description

        # Hijack helius description or try to form own if only one token change

        wallet_name_with_link_str = texts_en.get("wallet_name_with_link").format(
            WALLET_LINK=link_utilts.get_address_link(sending_data.wallet.address),
            WALLET_NAME=wallet_name,
        )

        if ((description and event.where != WhereNotification.PUMP_FUN)
                or (description and event.what in {
                    WhatNotification.TRANSFER, WhatNotification.TRANSFER_TO, WhatNotification.TRANSFER_FROM
                })):
            print("Helius transaction")
            description = description.replace(sending_data.wallet.address, wallet_name_with_link_str)
            if account_changes.token_changes:
                for change in account_changes.token_changes[:1]:
                    # Round numbers from the description to .2f
                    def round_numbers(match):
                        num = float(match.group())
                        return f"{num:.2f}"

                    description = re.sub(r'((?<=(swapped)\s)|(?<=(transferred\s)))[\d\.]+', round_numbers, description)
                    description = re.sub(r'(?<=for )\d+\.\d+', round_numbers, description)

                    if change.token.symbol:
                        description = description.replace(
                            change.token.address,
                            f'<a href="{link_utilts.get_address_link(change.token.address)}">{change.token.symbol}</a>'
                        )

                    if change.token.price_usd:
                        full_price_string = f"${abs(float(change.token.price_usd * change.amount)):.2f}"
                        description = re.sub(
                            r'(.*swapped\s[\d.]+)\s',
                            rf'\1 ({full_price_string}) ',
                            description
                        )
                        one_token_price_string = f"@${change.token.price_usd:2f}"
                        print(one_token_price_string)
                        description = description + ' ' + one_token_price_string
                    bolder = r'(?<=[\s\(\)$])(\d+(\.\d+)?)(?=[\s\(\)$]|$)'
                    # Replace matched numbers with <b> tags
                    description = re.sub(bolder, r'<b>\1</b>', description)

        elif len(account_changes.token_changes) == 1 and event.where == WhereNotification.PUMP_FUN:
            # If event is from pumpfun and helius is not knowing about it, we will try to form our own description
            # Also if it is only one account change, because it is very specific client-related thing
            change = account_changes.token_changes[0]
            token_display_name = change.token.symbol or change.token.address
            token_link_str = f'<a href="{link_utilts.get_address_link(change.token.address)}">{truncate_address(token_display_name)}</a>'
            description = self._form_local_description(
                sol_price=sending_data.helius_transaction_data.sol_price_usd,
                event=event,
                wallet_name_with_link=wallet_name_with_link_str,
                token_link_str=token_link_str,
                changes=account_changes)
        else:
            # If description is absent, we just give user transaction link
            description = (f'<a href="{transaction_link}">'
                           f'Transaction'
                           f'</a>')

        transaction_section = transaction_section.format(
            TRANSACTION_LINK=link_utilts.get_transaction_link(sending_data.helius_transaction_data.hash),
            DESCRIPTION=description,
        )

        if account_changes.token_changes:
            for change in account_changes.token_changes:
                # We are very not interested in market data of wSOL right now.
                if change.token.address == "So11111111111111111111111111111111111111112":
                    continue
                token_market_data = texts_en.get("markets_links")

                token_life: str = "??"
                if change.token.created_timestamp:
                    token_life: str = self.format_token_lifetime(
                        datetime.now() - datetime.fromtimestamp(change.token.created_timestamp)
                    )

                token_market_data = token_market_data.format(
                    TOKEN_ADDRESS=change.token.address,
                    TOKEN_LIFESPAN=token_life
                )

                token_info_text_line = texts_en.get("token_info_text")
                # token_name = self.guess_token_name(change.token)
                token_info_text_line = token_info_text_line.format(
                    TOKEN_SYMBOL=change.token.symbol or change.token.address,
                    TOKEN_MARKET_CAP=f"MC ${self.format_large_number(change.token.market_cap)}" if
                    change.token.market_cap else "",
                    TOKEN_ADDRESS=change.token.address,
                    COIN_DATA_LINE=token_market_data + '\n' if token_market_data else ""
                )

        notification_text = notification_text.format(
            INFO_LINE=info_line,
            WALLET_SECTION=wallet_section,
            TRANSACTION_SECTION=transaction_section,
            TOKEN_INFO_SECTION=token_info_text_line,
        )

        try:
            await self.bot.send_message(
                chat_id=sending_data.wallet.user_id,
                text=notification_text,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(e)

    @staticmethod
    def _form_info_line(event: NotificationEvent, account_change: SolanaAccountChangeData, transaction_link: str):
        line_text = texts_en.get("notification_info_line")

        if event.with_what == WithWhatNotification.TOKEN:
            entity = truncate_address(account_change.token_changes[0].token.symbol or account_change.token_changes[0].token.address)
        else:
            entity = event.with_what.value
        print(event)
        return line_text.format(
            TRANSACTION_LINK=transaction_link,
            EVENT=event.what.value,
            ENTITY_NAME=entity,
            WHERE=f"on {event.where.value}" if event.where else ""
        )

    @staticmethod
    def _decide_event(account_change: SolanaAccountChangeData,
                      source: str | None = None,
                      helius_description: str | None = None):

        what_happened: WhatNotification
        with_what_happened: WithWhatNotification
        where_happened: WhereNotification | None = None

        if not account_change.native_change:
            what_happened = WhatNotification.SWAP
            with_what_happened = WithWhatNotification.TOKEN
        else:
            if not account_change.token_changes:
                if account_change.native_change > 0:
                    what_happened = WhatNotification.TRANSFER_TO
                else:
                    what_happened = WhatNotification.TRANSFER_FROM
                with_what_happened = WithWhatNotification.SOL
            elif len(account_change.token_changes) > 1:
                what_happened = WhatNotification.SWAP
                with_what_happened = WithWhatNotification.MULTIPLE_TOKENS
            else:
                if account_change.native_change > 0:
                    what_happened = WhatNotification.SELL
                else:
                    what_happened = WhatNotification.BUY

                with_what_happened = WithWhatNotification.TOKEN

        if source:
            if source == "SYSTEM_PROGRAM":
                where_happened = WhereNotification.SYSTEM_PROGRAM
            else:
                try:
                    where_happened = WhereNotification[source]
                    print(where_happened)
                except KeyError:
                    print('something wrong with source', source)
                    where_happened = None

        # Dirty patching based on helius data
        if helius_description:
            if 'mint' in helius_description.lower():
                what_happened = WhatNotification.MINT
            elif 'transfer' in helius_description.lower() and not source:
                what_happened = WhatNotification.TRANSFER_TO

        return NotificationEvent(what=what_happened, with_what=with_what_happened, where=where_happened)

    @staticmethod
    def _form_local_description(
            event: NotificationEvent,
            token_link_str: str,
            wallet_name_with_link: str,
            changes: SolanaAccountChangeData,
            sol_price: float
    ):
        """
        DO NOT USE IT IF HELIUS DESCRIPTION IS PRESENT
        """

        if len(changes.token_changes) != 1:
            raise Exception("This method can't be used for more than one token changes")

        # Determine action and preposition
        action = "swapped"

        if event.what == WhatNotification.SELL:
            action = "sold"
        elif event.what == WhatNotification.BUY:
            action = "bought"
        elif event.what == WhatNotification.TRANSFER_TO:
            action = "sent"
        elif event.what == WhatNotification.TRANSFER_FROM:
            action = "received"
        elif event.what == WhatNotification.MINT:
            action = "minted"

        single_token_change = changes.token_changes[0]

        token_display = f"<b>{abs(single_token_change.amount):,.3f}</b> {token_link_str}"

        # Handle price-related data
        price_display = ""
        usd_display = ""

        native_change_line = ""
        if single_token_change.token.price_usd is not None:
            usd_value = abs(float(single_token_change.token.price_usd * single_token_change.amount))
            usd_display = f"(${usd_value:,.3f})"
            price_display = f"@${single_token_change.token.price_usd:.7f}"

        if changes.native_change:
            sol_real = abs(changes.native_change / 1_000_000_000)
            native_change_line = f" for <b>{sol_real:,.3f}</b> SOL "
            if not price_display:
                native_change_line += f"(<b>{sol_real * sol_price:,.3f}$</b>)"

        # Build description string
        description = f"{wallet_name_with_link} {action} {token_display}"
        if usd_display:
            description += f" {usd_display}"
        description += native_change_line
        if price_display:
            description += f" {price_display}"

        return description
