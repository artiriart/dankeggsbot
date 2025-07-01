import discord
from datetime import datetime, timezone
import asyncio
import json
import aiosqlite
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
try:
    with open("config.json", "r") as data:
        config = json.load(data)
except FileNotFoundError:
    logger.error("config.json not found!")
    exit(1)

main_guildid = config.get("main_guildid")
eggs_channelid = config.get("eggs_channelid")
boss_channelid = config.get("boss_channelid")
main_pingroleid = config.get("main_pingroleid")
main_doublepingroleid = config.get("main_doublepingroleid")
main_bossdoublepingroleid = config.get("main_bossdoublepingroleid")
main_bosspingroleid = config.get("main_bosspingroleid")
eggs_blacklistrole = config.get("eggs_blacklistrole")

try:
    with open("tokens.json", "r") as f:
        TOKENS = json.load(f)
except FileNotFoundError:
    logger.error("tokens.json not found!")
    exit(1)

dank_userid = 270904126974590976
database_path = "database.db"


def create_eggs_bot():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True
    intents.members = True

    bot = discord.Client(intents=intents, max_messages=0)

    # noinspection PyAsyncCall
    @bot.event
    async def on_ready():
        print(f'Bot up. Name: {bot.user}\n---')
        await db_setup()
        bot.loop.create_task(check_db())
        bot.loop.create_task(update_presence())

    async def db_setup():
        try:
            async with aiosqlite.connect("database.db") as db:
                await db.execute("""
                CREATE TABLE IF NOT EXISTS msg_guild (
                    guild_id TEXT PRIMARY KEY,
                    message_id TEXT
                );
                """)

                await db.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    user_id TEXT PRIMARY KEY,
                    amount INTEGER
                );
                """)

                await db.execute("""
                CREATE TABLE IF NOT EXISTS user_links (
                    main_user_id TEXT PRIMARY KEY,
                    alt_user_id TEXT
                );
                """)

                await db.execute("""
                CREATE TABLE IF NOT EXISTS user_cooldown (
                    user_id TEXT PRIMARY KEY,
                    unix_end TEXT
                );
                """)

                await db.execute("DELETE FROM msg_guild")
                await db.commit()
        except Exception as e:
            logger.error(f"Database setup error: {e}")

    async def check_db():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await asyncio.sleep(30)
                timestamp = int(datetime.now(timezone.utc).timestamp())
                async with aiosqlite.connect(database_path) as db:
                    async with db.execute(
                            "SELECT user_id FROM user_cooldown WHERE unix_end <= ?", (str(timestamp),)) as cursor:
                        rows = await cursor.fetchall()
                        if rows:
                            for row in rows:
                                user_id = row[0]
                                try:
                                    guild = await bot.fetch_guild(main_guildid)
                                    member = await guild.fetch_member(user_id)
                                    role = guild.get_role(eggs_blacklistrole)
                                    if role:
                                        await member.remove_roles(role)
                                    # Remove from cooldown table
                                    await db.execute("DELETE FROM user_cooldown WHERE user_id = ?", (user_id,))
                                    await db.commit()
                                except Exception as e:
                                    logger.error(f"Error removing role from user {user_id}: {e}")
            except Exception as e:
                logger.error(f"Error in check_db: {e}")

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
                logger.error(f"Error updating presence: {e}")
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
        except Exception as e:
            logger.error(f"Error creating invite: {e}")
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
            channel_tosendafter = bot.get_channel(eggs_channelid)
            view, embed = await createinvite(message)
            if view and embed:
                day = datetime.now(timezone.utc).weekday()
                ping_content = f"Eggs drop <@&{main_doublepingroleid}>" if day in [2,
                                                                                   6] else f"Eggs drop <@&{main_pingroleid}>"
                try:
                    eggs_message_final = await channel_tosendafter.send(embed=embed, view=view,
                                                                        content=ping_content)
                    async with aiosqlite.connect(database_path) as db:
                        await db.execute("INSERT OR REPLACE INTO msg_guild (guild_id, message_id) VALUES (?, ?)",
                                         (str(message.guild.id), str(eggs_message_final.id)))
                        await db.commit()
                except Exception as e:
                    logger.error(f"Error sending eggs event message: {e}")

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
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(label="Leave Server", style=discord.ButtonStyle.danger, custom_id="kick_member"))
                view.add_item(discord.ui.Button(label="Back to Boss Events Channel", style=discord.ButtonStyle.url,
                                                url=f"https://discord.com/channels/{main_guildid}/{boss_channelid}"))
                try:
                    await message.reply(embed=embed, view=view)
                except Exception as e:
                    logger.error(f"Error sending leave server message: {e}")

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
                ping_content = f"Boss Event <@&{main_bossdoublepingroleid}>" if day in [2,
                                                                                        6] else f"Boss Event <@&{main_bosspingroleid}>"
                try:
                    new_message = await channel_tosend.send(embed=embed, view=view, content=ping_content)
                    async with aiosqlite.connect(database_path) as db:
                        await db.execute("INSERT OR REPLACE INTO msg_guild (guild_id, message_id) VALUES (?, ?)",
                                         (str(message.guild.id), str(new_message.id)))
                        await db.commit()
                except Exception as e:
                    logger.error(f"Error sending boss event message: {e}")

    async def eggs_end(message):
        if (message.embeds and message.author.id == dank_userid and
                message.embeds[0].description and
                message.embeds[0].description.startswith("> You typed") and
                message.reference):

            try:
                claim_user = message.reference.resolved.author.id if message.reference.resolved else "No User!"
                async with aiosqlite.connect(database_path) as db:
                    async with db.execute("SELECT message_id FROM msg_guild WHERE guild_id = ?",
                                          (str(message.guild.id),)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            main_message_id = row[0]
                            channel = bot.get_channel(eggs_channelid)
                            if channel and main_message_id:
                                try:
                                    main_message = await channel.fetch_message(main_message_id)
                                    embed = discord.Embed(
                                        description=f"# Egg Claimed by <@{claim_user}>",
                                        color=discord.Color.dark_blue(),
                                    )
                                    await main_message.edit(content="", embed=embed, view=None)
                                except Exception as e:
                                    logger.error(f"Error editing eggs end message: {e}")
            except Exception as e:
                logger.error(f"Error in eggs_end: {e}")

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
                            if 1 < winner_id_start < winner_id_end:
                                winner_id = int(reward[winner_id_start:winner_id_end])
                                user = await bot.fetch_user(winner_id)
                                if user:
                                    try:
                                        embed = discord.Embed(
                                            title="Boss Event",
                                            description=f"## Rewards:\n{reward}\n-# in `{message.guild.name}`",
                                            color=discord.Color.green(),
                                        )
                                        embed.set_thumbnail(
                                            url="https://cdn.discordapp.com/emojis/987157087693975612.png")
                                        await user.send(embed=embed)
                                    except discord.Forbidden:
                                        logger.warning(f"Could not DM user {winner_id}")
                        except (ValueError, discord.HTTPException) as e:
                            logger.error(f"Error handling boss reward: {e}")
                            continue

    async def handle_eggs_xp(message):
        if (
                message.author.id == dank_userid and
                message.embeds and
                len(message.embeds) > 0 and
                message.embeds[0].fields and
                len(message.embeds[0].fields) > 0 and
                message.embeds[0].fields[0].value == "- 2.00x XP Multiplier for 1h" and
                message.guild and
                message.reference
        ):
            try:
                winner = message.reference.resolved.author.id if message.reference.resolved else None
                if winner:
                    expiring_time = int(datetime.now(timezone.utc).timestamp() + 3600)
                    async with aiosqlite.connect(database_path) as db:
                        await db.execute("INSERT OR REPLACE INTO user_cooldown (user_id, unix_end) VALUES (?, ?)",
                                         (str(winner), str(expiring_time)))
                        await db.commit()

                    guild = bot.get_guild(main_guildid)
                    if guild:
                        try:
                            member = await guild.fetch_member(winner)
                            role = guild.get_role(eggs_blacklistrole)
                            if role:
                                await member.add_roles(role)
                        except Exception as e:
                            logger.error(f"Error adding blacklist role: {e}")
            except Exception as e:
                logger.error(f"Error in handle_eggs_xp: {e}")

    @bot.event
    async def on_message(message):
        if message.guild and message.guild.id != main_guildid:
            await check_eggsevent(message)
            await check_bossevent(message)
            await handle_bossend(message)
            await eggs_end(message)
            await handle_eggs_xp(message)

            if message.embeds and message.author.id == dank_userid:
                desc = message.embeds[0].description or ""
                if (desc == "Not enough people joined the boss battle..." or
                        desc.endswith("has been defeated!") or
                        desc.startswith("The correct answer was") or
                        desc.startswith("> You typed")):

                    try:
                        async with aiosqlite.connect(database_path) as db:
                            await db.execute("DELETE FROM msg_guild WHERE guild_id = ?", (str(message.guild.id),))
                            await db.commit()
                    except Exception as e:
                        logger.error(f"Error deleting from msg_guild: {e}")

    @bot.event
    async def on_reaction_add(reaction, user):
        user=reaction.message.author.id
        if getattr(reaction.emoji, "id", None) == 1071484103762915348:
            try:
                channel = bot.get_channel(boss_channelid)
                async with aiosqlite.connect(database_path) as db:
                    async with db.execute("SELECT message_id FROM msg_guild WHERE guild_id = ?",
                                          (str(reaction.message.guild.id),)) as cursor:
                        row = await cursor.fetchone()
                        message_id = row[0] if row else None

                if not message_id or not channel:
                    return

                message = await channel.fetch_message(message_id)
                try:
                    players = int(message.components[0].children[1].custom_id) + 1
                except (IndexError, AttributeError, ValueError):
                    players = 1

                if players >= 5:
                    view = discord.ui.View()
                    embed = discord.Embed(
                        description="# Boss Event over!",
                        color=discord.Color.default(),
                    )
                    await message.edit(view=view, embed=embed, content="")
                else:
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Invite Link", style=discord.ButtonStyle.url,
                                                    url=message.components[0].children[0].url))
                    view.add_item(discord.ui.Button(label=f"Players: {players}/5", style=discord.ButtonStyle.gray,
                                                    disabled=True, custom_id=str(players)))
                    embed = message.embeds[0]
                    old_desc = message.embeds[0].description or "Error."
                    embed.description = f"{old_desc}\n`#{players}` <@{user.id}>"
                    await message.edit(view=view, embed=embed)
            except Exception as e:
                logger.error(f"Error in on_reaction_add: {e}")

    @bot.event
    async def on_guild_join(guild):
        try:
            owner = guild.owner_id
            async with aiosqlite.connect(database_path) as db:
                async with db.execute("SELECT main_user_id FROM user_links WHERE alt_user_id = ?",
                                      (str(owner),)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        owner = row[0]

                await db.execute("""INSERT INTO user_scores (user_id, amount) VALUES (?, 1) 
                                   ON CONFLICT(user_id) DO UPDATE SET amount = amount + 1""", (str(owner),))
                await db.commit()
        except Exception as e:
            logger.error(f"Error in on_guild_join: {e}")

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
                        timestamp_start = data_two.find("<t:") + 3
                        timestamp_end = data_two.find(":R>")
                        timestamp = int(data_two[timestamp_start:timestamp_end])
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
                            view.add_item(discord.ui.Button(label=f"Players: 0/5", style=discord.ButtonStyle.gray,
                                                            disabled=True, custom_id="0"))
                            embed = message.embeds[0]
                            embed.description = f"{message.embeds[0].description or 'Error.'}\n## Joined Players:"
                            await message.edit(view=view, embed=embed)
                            await interaction.followup.send("Generated Invite.", ephemeral=True)
                        else:
                            await interaction.followup.send("Guild not found or I am no longer in that server.",
                                                            ephemeral=True)
                except Exception as e:
                    logger.error(f"Error handling geninv interaction: {e}")
                    await interaction.followup.send("An error occurred while creating the invite.", ephemeral=True)

            elif custom_id == "kick_member":
                perms = interaction.channel.permissions_for(interaction.guild.me)
                if perms.kick_members:
                    try:
                        embed = discord.Embed(description="## You will leave this Server in 3 seconds...")
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        await asyncio.sleep(3)
                        await interaction.guild.kick(interaction.user, reason="Tapped leave Button for Boss Events")
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            content="# Something went wrong!\n-# That means you are above me.", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        content="# Something went wrong!\n-# That means I dont have the required (kick_members) permissions.",
                        ephemeral=True)

    return bot


# Main async launcher for all bots
async def main():
    if not TOKENS:
        logger.error("No tokens found in tokens.json")
        return

    bots = [create_eggs_bot() for _ in TOKENS]
    tasks = []

    for bot, token in zip(bots, TOKENS):
        if token.strip():
            tasks.append(bot.start(token.strip()))

    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.error("No valid tokens found")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down bots.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")