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

async def reload_buttons(messages_to_keep = {}):
    with open("./storage/tickets.json", "r") as tickets_file:
        ticket_data = json.load(tickets_file)
    with open("./storage/channels.json", "r") as channels_file:
        channel_data = json.load(channels_file)
    
    for message_id in ticket_data:
        for channel_id in channel_data:
            try:
                channel = await bot.fetch_channel(int(channel_id))
            except discord.errors.NotFound:
                print(f"[-] Channel {channel_id} not found")
                delete_entry_from_json("./storage/channels.json", channel_id)
                continue

            try:
                message = await channel.fetch_message(int(message_id))
                button = Create_Ticket_Button()
                await message.edit(view=discord.ui.View().add_item(button))
                messages_to_keep[message_id]=ticket_data[message_id]
            except:
                pass

    with open("./storage/tickets.json", "w") as tickets_file:
        json.dump(messages_to_keep, tickets_file, indent=4)
        print("[+] Successfully updated tickets JSON.")

def delete_entry_from_json(file_path, entry_id):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
    if entry_id in data:
        del data[entry_id]
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
            print("[+] Entry deleted from JSON successfully.")
    else:
        print("[-] Entry not found in JSON.")


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
        if category_name is None: category_name = ""
        if ticket_title is None: ticket_title = "Welcome"
        if ticket_description is None: ticket_description = "Wait until you recive suport from our staff"
        if ticket_message is None: ticket_message = ""
        create_ticket = Create_Ticket_Button()

        new_embed = discord.Embed(title=title, description=description)
        message = await ctx.channel.send(embed=new_embed, view=discord.ui.View().add_item(item=create_ticket))
        with open("./storage/channels.json", "r+") as channels_file:
            channels_data = json.load(channels_file)
            try:
                channels_data[str(ctx.channel.id)]
            except: 
                channels_data[str(ctx.channel.id)] = ctx.channel.name
                channels_file.seek(0)
                json.dump(channels_data, channels_file, indent=4)
                channels_file.truncate()

        data = {
        "category_name": category_name,
        "title": ticket_title,
        "description": ticket_description,
        "ticket_message": ticket_message,
        "number_of_tickets": 0,
        "opened_tickets": {
        }
}
        with open("./storage/tickets.json", "r+") as ticket_file:
            ticket_data = json.load(ticket_file)
            ticket_data[str(message.id)] = data
            ticket_file.seek(0)
            json.dump(ticket_data, ticket_file, indent=4)
            ticket_file.truncate()



bot.run(os.getenv("TOKEN"))
