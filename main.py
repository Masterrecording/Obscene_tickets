from discord.ext import commands
import discord.ext
import discord
import dotenv
import json
import os

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix='$', intents=intents)

class Create_Ticket_Button(discord.ui.Button):
    def __init__(self, label="Create Ticket ", *, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        data = json.load(open("./storage/tickets.json", "r"))[str(interaction.message.id)]
        print(data)

async def reload_buttons():
    for message_id in json.load(open("./storage/tickets.json", "r")):
        for channel_id in json.load(open("./storage/channels.json", "r")):
            message = await bot.fetch_channel(int(channel_id)).fetch_message(int(message_id))
            button = Create_Ticket_Button()
            await message.edit(view=discord.ui.View().add_item(button))

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print("Loadding all the tickets...")
    await reload_buttons()
    print("All the tickets have been loaded!")


@bot.command(name="setup", description="Create a new ticket system and send the ticket message")
async def execute_setup(ctx: commands.Context,
                        title: str | None,
                        description: str | None,
                        category_name: str | None,
                        ticket_title: str | None,
                        ticket_description: str | None,
                        ticket_message: str | None):

    if ctx.author.guild_permissions.administrator:
        if title is None: title = "Welcome to the ticket system"
        if description is None: description = "Click on the button below to create a ticket!"
        if category_name is None: category_name = "",
        if ticket_title is None: ticket_title = "Welcome"
        if ticket_description is None: ticket_description = "Wait until you recive suport from our staff"
        if ticket_message is None: ticket_message = "",

        create_ticket = Create_Ticket_Button()

        new_embed = discord.Embed(title=title, description=description)
        message = await ctx.channel.send(embed=new_embed, view=discord.ui.View().add_item(item=create_ticket))
        with open("./storage/channels.json", "r+") as channels_file:
            channels_data = json.load(channels_file)
            if channels_data[str(ctx.channel.id)]:
                pass
            else: 
                data[str(ctx.channel.id)] = ctx.channel.name
                channels_file.seek(0)
                json.dump(channels_data, channels_file, indent=4)
                channels_file.truncate()

        data = {
        "category_name": category_name,
        "title": ticket_title,
        "description": ticket_description,
        "ticket_message": ticket_message
}
        with open("./storage/tickets.json", "r+") as ticket_file:
            ticket_data = json.load(ticket_file)
            ticket_data[str(message.id)] = data
            ticket_file.seek(0)
            json.dump(ticket_data, ticket_file, indent=4)
            ticket_file.truncate()

bot.run(os.getenv("TOKEN"))
