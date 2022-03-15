import asyncio
import os

import disnake

from disnake.ext import commands
from yahoo_fin import stock_info as si
from millify import millify


class GmeTickerBot(commands.Bot):
    previous_high = 0
    task = None

    async def on_ready(self):
        if self.task is None:
            self.task = self.loop.create_task(self.update())

    async def update(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.change_name_to_market_data()
            except Exception as e:
                print(e)
            await asyncio.sleep(10)

    async def change_name_to_market_data(self):
        change = si.get_quote_data("gme")
        market_state = change['marketState']
        if market_state == "PRE":
            price = change['preMarketPrice']
            activity = f"PM: ${millify(change['preMarketChange'], 2)} " \
                       f"{millify(change['preMarketChangePercent'], 2)}% "
        elif market_state == "REGULAR":
            price = si.get_live_price("gme")
            activity = f"${millify(change['regularMarketChange'], 2)} " \
                   f"{millify(change['regularMarketChangePercent'], 2)}% " \
                   f"{millify(change['regularMarketVolume'], 2)}"
        elif market_state == "POST":
            price = change['postMarketPrice']
            activity = f"AH: ${millify(change['postMarketChange'], 2)} " \
                       f"{millify(change['postMarketChangePercent'], 2)}% "
        else:
            price = change['postMarketPrice']
            activity = f"Closed: ${millify(change['postMarketPrice'], 2)}"

        live_price = str(round(price, 2))
        high = round(change['regularMarketDayHigh'])

        if market_state == "OPEN":
            if high > self.previous_high:
                self.previous_high = high
                print(f'New High: {high}')
        else:
            self.previous_high = 0
        name = f"GME: ${live_price}"
        for guild in self.guilds:
            if guild:
                await guild.me.edit(nick=name)
        await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching,
                                                            name=activity))


bot = GmeTickerBot(command_prefix='!',
                   sync_commands_debug=True)
bot.run(os.environ["discord_bot_token"])
