import discord
from datetime import datetime, timezone
import asyncio
import json

with open ("config.json", "r") as data:
    config = json.load(data)

main_guildid = config.get("main_guildid")
eggs_channelid = config.get("eggs_channelid")
eggs_adminchannelid = config.get("eggs_adminchannelid")
boss_channelid = config.get("boss_channelid")
main_pingroleid = config.get("main_pingroleid")
main_doublepingroleid = config.get("main_doublepingroleid")
main_bossdoublepingroleid = config.get("main_bossdoublepingroleid")
main_bosspingroleid = config.get("main_bosspingroleid")

with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

dank_userid = 270904126974590976
message_guild_storage = {}

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
        except Exception as a:
            print(a)
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
            channel_tosend = bot.get_channel(eggs_adminchannelid)
            channel_tosendafter = bot.get_channel(eggs_channelid)
            if channel_tosend:
                view, embed = await createinvite(message)
                if view and embed:
                    day = datetime.now(timezone.utc).weekday()
                    ping_content = f"Eggs drop <@&{main_doublepingroleid}>" if day in [2,
                                                                                       6] else f"Eggs drop <@&{main_pingroleid}>"
                    await channel_tosend.send(embed=embed, view=view, content=ping_content)
                    await asyncio.sleep(5)
                    await channel_tosendafter.send(embed=embed, view=view, content=ping_content)

    async def check_bossevent(message):
        if (
            message.author.id == dank_userid and
            message.embeds and
            message.embeds[0].description and
            message.embeds[0].description.startswith("> OH SHIT A BOSS SPAWNED!") and
            message.guild and message.guild.id != main_guildid
        ):
            guild = message.guild
            ownerid = guild.owner_id if guild.owner_id else "Owner ID Empty, couldnt fetch Owner"
            expiring_time = int(datetime.now(timezone.utc).timestamp() + 600)
            channel_tosend = bot.get_channel(boss_channelid)
            perms = message.channel.permissions_for(message.guild.me)
            if perms.kick_members:
                embed = discord.Embed(
                    title="Leave Server",
                    description="The boss event has started in this server. Good luck!\n**If you'd like to automatically leave this server, you can press the button below now. You can always rejoin later if needed.**",
                    color=discord.Color.random(),
                )
                view=discord.ui.View()
                view = view.add_item(discord.ui.Button(label="Leave Server", style=discord.ButtonStyle.danger, custom_id="kick_member"))
                view = view.add_item(
                    discord.ui.Button(label="Back to Boss Events Channel", style=discord.ButtonStyle.url, url=f"https://discord.com/channels/{main_guildid}/{boss_channelid}"))
                await message.reply(embed=embed, view=view)

            if channel_tosend:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Generate Invite", custom_id=f"geninv-{message.channel.id}",
                                                style=discord.ButtonStyle.success))
                embed = discord.Embed(
                    title="Boss Event",
                    description=f"in {guild.name}, which is owned by <@{ownerid}>\n"
                                f"**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
                    color=discord.Color.yellow(),
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1101064546812178506.png")

                day = datetime.now(timezone.utc).weekday()
                ping_content = f"Boss Event <@&{main_bossdoublepingroleid}>" if day in [2, 6] else f"Boss Event <@&{main_bosspingroleid}>"
                new_message = await channel_tosend.send(embed=embed, view=view, content=ping_content)
                message_guild_storage[message.guild.id] = new_message.id

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
                                user = await bot.fetch_user(winner_id)
                                if user:
                                    if user.dm_channel is None:
                                        await user.create_dm()
                                    channel = user.dm_channel

                                    embed = discord.Embed(
                                        title="Boss Event",
                                        description=f"## Rewards:\n{reward}\n-# in `{message.guild.name}`",
                                        color=discord.Color.green(),
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
                if message.embeds and message.author.id == dank_userid:
                    desc = message.embeds[0].description or ""
                    if desc == "Not enough people joined the boss battle..." or desc.endswith("has been defeated!"):
                        message_guild_storage.pop(message.guild.id, None)

    @bot.event
    async def on_reaction_add(reaction, user):
        if getattr(reaction.emoji, "id", None) == 1071484103762915348:
            guild_id = reaction.message.guild.id
            channel = await bot.fetch_channel(boss_channelid)
            message_id = message_guild_storage.get(guild_id)
            if not message_id:
                return
            message = await channel.fetch_message(message_id)
            try:
                players = message.components[0].children[1].custom_id
            except (IndexError, AttributeError):
                players = 1
            try:
                players = int(players)+1
            except Exception as e:
                print(e)

            if players == 5:
                view = discord.ui.View()
                embed = discord.Embed(
                    description="# Boss Event over!",
                    color=discord.Color.default(),
                )
                await message.edit(view=view, embed=embed, content="")
            else:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Invite Link", style=discord.ButtonStyle.url, url=message.components[0].children[0].url))
                view.add_item(discord.ui.Button(label=f"Players: {players}/5", style=discord.ButtonStyle.gray, disabled=True, custom_id=str(players)))
                embed = message.embeds[0]
                old_desc = message.embeds[0].description or "Error."
                embed.description = f"{old_desc}\n`#{players}` <@{reaction.message.author.id}>"
                await message.edit(view=view, embed=embed)

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
                        data_two = message.embeds[0].description
                        timestamp = int(data_two[data_two.find("<t:") + 3:data_two.find(":R>")])
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
                            view.add_item(
                                discord.ui.Button(label=f"Players: 0/5", style=discord.ButtonStyle.gray, disabled=True,
                                                  custom_id="0"))
                            embed = message.embeds[0]
                            embed.description = f"{message.embeds[0].description if message.embeds[0].description else 'Error.'}\n## Joined Players:"
                            await message.edit(view=view, embed=embed)
                            await interaction.followup.send("Generated Invite.", ephemeral=True)
                        else:
                            await interaction.followup.send("Guild not found or I am no longer in that server.",
                                                            ephemeral=True)
                except Exception as e:
                    print(f"Error handling interaction: {e}")
                    await interaction.followup.send("An error occurred while creating the invite.", ephemeral=True)
            elif custom_id=="kick_member":
                perms = interaction.channel.permissions_for(interaction.guild.me)
                if perms.kick_members:
                    try:
                        embed = discord.Embed(
                            description="## You will leave this Server in 3 seconds...",
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        await asyncio.sleep(3)
                        await interaction.guild.kick(interaction.user, reason="Tapped leave Button for Boss Events")
                    except discord.Forbidden:
                        await interaction.response.send_message(content="# Something went wrong!\n-# That means you are above me.", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        content="# Something went wrong!\n-# That means I dont have the required (kick_members) permissions.", ephemeral=True)

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