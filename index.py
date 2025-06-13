from http.cookiejar import UTC_ZONES

import discord
from datetime import datetime, timezone
import asyncio
import json

# CHANGE YOUR VARIABLES HERE:
main_guildid=1349398262322429952
main_channelid=1376603711891050619
main_pingroleid=2
main_doublepingroleid=1

# Load tokens from tokens.json
with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

# Dank Memer bot ID (hardcoded)
dank_userid = 270904126974590976

# Shared function to create a bot client with logic
def create_eggs_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=discord.Intents(33344), max_messages=0)

    @bot.event
    async def on_ready():
        print(f'Your Eggs bot is up for egg hunting! Name: {bot.user}')

    async def createinvite(message):
        guild = message.guild
        owner = guild.owner_id
        owner_user = await bot.fetch_user(owner)
        owner_username = owner_user.name
        invite = await message.channel.create_invite(max_age=300, reason="Eggs Invitation")
        message_url = message.jump_url
        expiring_time = int(datetime.now(timezone.utc).timestamp() + 300)

        embed = discord.Embed(
            title="Eggs Event Spawned!",
            description=f"in {guild.name}, which is owned by `{owner_username}` ({owner})\n"
                        f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url="https://i.imgur.com/g446CZj.gif")

        invite_button = discord.ui.Button(label="Invite Link", style=discord.ButtonStyle.url, url=invite.url)
        message_button = discord.ui.Button(label="Message Link", style=discord.ButtonStyle.url, url=message_url)

        actionrow = discord.ui.View()
        actionrow.add_item(invite_button)
        actionrow.add_item(message_button)

        return actionrow, embed

    async def check_eggsevent(message):
        if (
            message.author.id == dank_userid and
            message.embeds and
            message.embeds[0].description and
            message.embeds[0].description.startswith("> Aw man, I dropped something in my eggs again.") and
            message.guild and message.guild.id != main_guildid
        ):
            channel_tosend = bot.get_channel(main_channelid)
            actionrow, embed = await createinvite(message)
            if datetime.now(timezone.utc).weekday() == 2 or 6:
                ping_content=f"Eggs drop <@&{main_doublepingroleid}>"
            else:
                ping_content=f"Eggs drop <@&{main_pingroleid}>"
            await channel_tosend.send(embed=embed, view=actionrow, content=ping_content)

    async def check_eggseventdone(message):
        if (
            message.author.id == dank_userid and
            message.embeds and
            message.embeds[0].description and
            message.embeds[0].description.startswith("> You typed") and
            message.guild and message.guild.id != main_guildid
        ):
            invites = await message.channel.invites()
            for invite in invites:
                if invite.inviter.id == bot.user.id:
                    await invite.delete(reason="Eggs Event over!")

    @bot.event
    async def on_message(message):
        await check_eggsevent(message)
        await check_eggseventdone(message)

    return bot

# Main async launcher for all bots
async def main():
    bots = [create_eggs_bot() for _ in TOKENS]
    await asyncio.gather(*(bot.start(token.strip()) for bot, token in zip(bots, TOKENS)))

if __name__ == "__main__":
    asyncio.run(main())
