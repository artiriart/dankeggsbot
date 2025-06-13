import discord
from os import getenv
import dotenv
from datetime import datetime, timezone
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'You are ready {client.user}')

dank_userid=270904126974590976

async def createinvite(message):
    guild = message.guild
    owner = guild.owner_id
    owner_user = await client.fetch_user(owner)
    owner_username = owner_user.name
    invite = await message.channel.create_invite(max_age=300, reason="Eggs Invitation")
    message_url = message.jump_url
    expiring_time = int(datetime.now(timezone.utc).timestamp()+300)
    embed = discord.Embed(
        title="Eggs Event Spawned!",
        description= f"in {guild.name}, which is owned by `{owner_username}` ({owner})\n**Expires: <t:{expiring_time}:R>**\n-# Invalid Invite = Event over",
        color = discord.Color.blurple(),
    )
    embed = embed.set_thumbnail(url="https://i.imgur.com/g446CZj.gif")
    invite_button = discord.ui.Button(label="Invite Link", style= discord.ButtonStyle.url, url=invite.url)
    message_button = discord.ui.Button(label="Message Link", style= discord.ButtonStyle.url, url=message_url)
    actionrow = discord.ui.View()
    actionrow.add_item(invite_button)
    actionrow.add_item(message_button)
    return actionrow, embed

async def check_eggsevent(message):
    if message.author.id == dank_userid and message.embeds[0].description.startswith("> Aw man, I dropped something in my eggs again.") and message.guild.id != 1349398262322429952:
        channel_tosend = client.get_channel(1376603711891050619)
        actionrow, embed = await createinvite(message)
        await channel_tosend.send(embed=embed, view=actionrow)

async def check_eggseventdone(message):
    if message.author.id == dank_userid and message.embeds[0].description.startswith("> You typed") and message.guild.id != 1349398262322429952:
        invites = await message.channel.invites()
        for invite in invites:
            if invite.inviter.id == client.user.id:
                await invite.delete(reason="Eggs Event over!")



@client.event
async def on_message(message):
    await check_eggsevent(message)
    await check_eggseventdone(message)

client.run(getenv("TOKEN"))
