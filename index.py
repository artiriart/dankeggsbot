import discord
from datetime import datetime, timezone
import asyncio
import json

# CHANGE YOUR VARIABLES HERE:
main_guildid = 1349398262322429952
main_channelid = 1376603711891050619
main_pingroleid = 2
main_doublepingroleid = 1

# Load tokens from tokens.json
with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

# Dank Memer bot ID (hardcoded)
dank_userid = 270904126974590976

# Shared function to create a bot client with logic
def create_eggs_bot():
    # --- FIX: Intents setup clarified for better readability ---
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
        owner = guild.owner
        owner_username = owner.name if owner else "Unknown Owner"
        owner_id = owner.id if owner else "N/A"

        try:
            # Create an invite to the first available channel
            invite = await message.channel.create_invite(max_age=300, reason="Eggs Invitation", max_uses=1)
        except discord.Forbidden:
            return None, None  # Return None if bot can't create invite

        message_url = message.jump_url
        expiring_time = int(datetime.now(timezone.utc).timestamp() + 300)

        embed = discord.Embed(
            title="Eggs Event Spawned!",
            description=f"in {guild.name}, which is owned by `{owner_username}` ({owner_id})\n"
                        f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
            color=discord.Color.yellow(),
        )
        embed.set_thumbnail(url="https://i.imgur.com/g446CZj.gif")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Link", style=discord.ButtonStyle.url, url=invite.url))
        view.add_item(discord.ui.Button(label="Message Link", style=discord.ButtonStyle.url, url=message_url))

        return view, embed

    async def check_eggsevent(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                message.embeds[0].description and
                message.embeds[0].description.startswith("> Aw man, I dropped something in my eggs again.") and
                message.guild and message.guild.id != main_guildid
        ):
            channel_tosend = bot.get_channel(main_channelid)
            view, embed = await createinvite(message)

            if view and embed and channel_tosend:  # Check if invite/channel was found
                day = datetime.now(timezone.utc).weekday()
                ping_content = f"Eggs drop <@&{main_doublepingroleid}>" if day in [2,
                                                                                   6] else f"Eggs drop <@&{main_pingroleid}>"
                await channel_tosend.send(embed=embed, view=view, content=ping_content)

    async def check_bossevent(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                message.embeds[0].description and
                message.embeds[0].description.startswith("> OH SHIT A BOSS SPAWNED!") and
                message.guild and message.guild.id != main_guildid
        ):
            guild = message.guild
            owner = guild.owner
            owner_username = owner.name if owner else "Unknown Owner"
            owner_id = owner.id if owner else "N/A"
            expiring_time = int(datetime.now(timezone.utc).timestamp() + 300)
            channel_tosend = bot.get_channel(main_channelid)

            # --- FIX: Create a View instance before adding items ---
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Generate Invite", custom_id=f"geninv-{message.guild.id}",
                                            style=discord.ButtonStyle.success))

            embed = discord.Embed(
                title="Boss Event",
                description=f"in {guild.name}, which is owned by `{owner_username}` ({owner_id})\n"
                            f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
                color=discord.Color.default(),
            ).set_thumbnail(url="https://cdn.discordapp.com/emojis/1101064546812178506.png")

            day = datetime.now(timezone.utc).weekday()
            ping_content = "Boss drop on Double XP day" if day in [2, 6] else "Boss drop"
            if channel_tosend:
                await channel_tosend.send(embed=embed, view=view, content=ping_content)

    async def handle_bossend(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                message.embeds[0].description and
                message.embeds[0].description.endswith("has been defeated!") and
                message.guild and message.guild.id != main_guildid
        ):
            rewards = message.embeds[0].fields[0].value.splitlines()
            if rewards:
                for reward in rewards:
                    winner_id=reward[reward.find("<@")+2 : reward.find(">")]
                    user=bot.get_user(winner_id)
                    channel=user.dm_channel
                    embed = discord.Embed(
                        title="Boss Event",
                        description="## Rewards:\n"+
                                    reward
                    )
                    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/987157087693975612.png")
                    await channel.send(embed=embed)

    @bot.event
    async def on_message(message):
        if message.guild:
            await check_eggsevent(message)
            await check_bossevent(message)
            await handle_bossend(message)

    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("geninv-"):
                await interaction.response.defer(ephermal=True)  # Acknowledge the interaction immediately
                try:
                    guild_id = int(custom_id.split("-")[1])
                    guild = bot.get_guild(guild_id)
                    if guild:
                        # Find a channel where the bot can create an invite
                        invite_channel = None
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).create_instant_invite:
                                invite_channel = channel
                                break

                        if invite_channel:
                            invite = await invite_channel.create_invite(max_age=600, max_uses=5,
                                                                        reason="Boss Event Invite")
                            message = interaction.message

                            view = discord.ui.View()
                            view.add_item(
                                discord.ui.Button(style=discord.ButtonStyle.url, url=invite.url, label="Join Server"))

                            await message.edit(view=view)
                            await interaction.followup.send("Generated Invite.", ephemeral=True)
                        else:
                            await interaction.followup.send(
                                "I don't have permission to create an invite in that server.", ephemeral=True)
                    else:
                        await interaction.followup.send("Guild not found or I am no longer in that server.",
                                                        ephemeral=True)
                except Exception as e:
                    print(f"Error handling interaction: {e}")
                    await interaction.followup.send("An error occurred while creating the invite.", ephemeral=True)

    return bot


# Main async launcher for all bots
async def main():
    # Use a list of tokens directly, assuming tokens.json contains a list of strings
    bots = [create_eggs_bot() for _ in TOKENS]
    await asyncio.gather(*(bot.start(token.strip()) for bot, token in zip(bots, TOKENS)))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down bots.")