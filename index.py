import discord
from datetime import datetime, timezone
import asyncio
import json

# CHANGE YOUR VARIABLES HERE:
main_guildid = 1349398262322429952
eggs_channelid = 1376603711891050619
boss_channelid = 1376603711891050619
main_pingroleid = "Test: Normal Day"
main_doublepingroleid = "Test: Double XP"

# Load tokens from tokens.json
with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

# Dank Memer bot ID (hardcoded)
dank_userid = 270904126974590976


# Shared function to create a bot client with logic
def create_eggs_bot():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True

    bot = discord.Client(intents=intents, max_messages=0)

    @bot.event
    async def on_ready():
        print(f'Bot up. Name: {bot.user}\n---')
        await bot.loop.create_task(update_presence())

    async def update_presence():
        """Update bot presence every hour"""
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                server_amount = len(bot.guilds)
                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.playing,
                        name=f"with {server_amount} Servers"
                    )
                )
            except Exception as e:
                print(f"Error updating presence: {e}")
            finally:
                await asyncio.sleep(3600)

    async def createinvite(message):
        guild = message.guild
        ownerid = guild.owner_id if guild.owner_id else "Owner ID Empty, couldnt fetch Owner"

        try:
            invite = await message.channel.create_invite(max_age=300, reason="Eggs Invitation", max_uses=1)
            message_url = message.jump_url
            expiring_time = int(datetime.now(timezone.utc).timestamp() + 300)

            embed = discord.Embed(
                title="Eggs Event Spawned!",
                description=f"in {guild.name}, which is owned by <@{ownerid}>\n"
                            f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
                color=discord.Color.yellow(),
            )
            embed.set_thumbnail(url="https://i.imgur.com/g446CZj.gif")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Invite Link", style=discord.ButtonStyle.url, url=invite.url))
            view.add_item(discord.ui.Button(label="Message Link", style=discord.ButtonStyle.url, url=message_url))

            return view, embed
        except discord.Forbidden:
            return None, None
        except Exception:
            return None, None

    async def check_eggsevent(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                len(message.embeds) > 0 and
                message.embeds[0].description and
                message.embeds[0].description.startswith("> Aw man, I dropped something in my eggs again.") and
                message.guild
        ):
            channel_tosend = bot.get_channel(eggs_channelid)
            if channel_tosend:
                view, embed = await createinvite(message)
                if view and embed:
                    day = datetime.now(timezone.utc).weekday()
                    ping_content = f"Eggs drop <@&{main_doublepingroleid}>" if day in [2,
                                                                                       6] else f"Eggs drop <@&{main_pingroleid}>"
                    await channel_tosend.send(embed=embed, view=view, content=ping_content)

    async def check_bossevent(message):
        if (
                (message.author.id == dank_userid and
                 message.embeds and
                 len(message.embeds) > 0 and
                 message.embeds[0].description and
                 message.embeds[0].description.startswith("> OH SHIT A BOSS SPAWNED!") and
                 message.guild and message.guild.id != main_guildid)
        ):
            guild = message.guild
            ownerid = guild.owner_id if guild.owner_id else "Owner ID Empty, couldnt fetch Owner"
            expiring_time = int(datetime.now(timezone.utc).timestamp() + 600)
            channel_tosend = bot.get_channel(boss_channelid)

            if channel_tosend:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Generate Invite", custom_id=f"geninv-{message.channel.id}",
                                                style=discord.ButtonStyle.success))

                embed = discord.Embed(
                    title="Boss Event",
                    description=f"in {guild.name}, which is owned by <@{ownerid}>\n"
                                f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
                    color=discord.Color.default(),
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1101064546812178506.png")

                day = datetime.now(timezone.utc).weekday()
                ping_content = "Boss drop on Double XP day" if day in [2, 6] else "Boss drop"
                await channel_tosend.send(embed=embed, view=view, content=ping_content)

    async def handle_bossend(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                len(message.embeds) > 0 and
                message.embeds[0].description and
                message.embeds[0].description.endswith("has been defeated!") and
                message.guild
        ):
            if len(message.embeds[0].fields) > 0:
                rewards = message.embeds[0].fields[0].value.splitlines()
                if rewards:
                    for reward in rewards:
                        try:
                            winner_id_start = reward.find("<@") + 2
                            winner_id_end = reward.find(">")
                            if winner_id_start > 1 and winner_id_end > winner_id_start:
                                winner_id = int(reward[winner_id_start:winner_id_end])
                                user = bot.get_user(winner_id)
                                if user:
                                    if user.dm_channel is None:
                                        await user.create_dm()
                                    channel = user.dm_channel

                                    embed = discord.Embed(
                                        title="Boss Event",
                                        description="## Rewards:\n" + reward
                                    )
                                    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/987157087693975612.png")
                                    await channel.send(embed=embed)
                        except (ValueError, discord.Forbidden, discord.HTTPException):
                            continue

    @bot.event
    async def on_message(message):
        if message.guild:
            if message.guild.id != main_guildid:
                await check_eggsevent(message)
                await check_bossevent(message)
                await handle_bossend(message)

    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("geninv-"):
                await interaction.response.defer()
                try:
                    channel_id = int(custom_id.split("-")[1])
                    channel = bot.get_channel(channel_id)
                    message = interaction.message

                    if message.embeds and len(message.embeds) > 0:
                        data = message.embeds[0].description
                        timestamp = int(data[data.find("<t:") + 3:data.find(":R>")])
                        current_time = int(datetime.now(timezone.utc).timestamp())

                        if timestamp < current_time:
                            await interaction.followup.send("Outdated Event.", ephemeral=True)
                            return

                        time_dif = timestamp - current_time

                        if channel:
                            invite = await channel.create_invite(max_age=time_dif, max_uses=5,
                                                                 reason="Boss Event Invite")
                            view = discord.ui.View()
                            view.add_item(
                                discord.ui.Button(style=discord.ButtonStyle.url, url=invite.url, label="Join Server"))

                            await message.edit(view=view)
                            await interaction.followup.send("Generated Invite.", ephemeral=True)
                        else:
                            await interaction.followup.send("Guild not found or I am no longer in that server.",
                                                            ephemeral=True)
                except Exception as e:
                    print(f"Error handling interaction: {e}")
                    await interaction.followup.send("An error occurred while creating the invite.", ephemeral=True)

    return bot


# Main async launcher for all bots
async def main():
    bots = [create_eggs_bot() for _ in TOKENS]
    await asyncio.gather(*(bot.start(token.strip()) for bot, token in zip(bots, TOKENS)))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down bots.")