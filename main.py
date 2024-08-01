from discord.ext import commands
from colorama import Fore, Style
import discord.ext.commands
import discord.ext
import datetime
import discord
import asyncio
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
        tickets = json.load(open("./storage/tickets.json", "r"))
        servers = json.load(open("./storage/servers.json", "r"))
        data = tickets[str(interaction.message.id)]
        valid_category = False
        if str(interaction.user.id) in data["opened_tickets"].keys():
            await interaction.response.send_message("Ya tienes un ticket abierto pendiente", ephemeral=True)
        else:
            try:
                server = interaction.guild
                admin_role_id = servers[str(server.id)]
                TICKET_NAME = f'ticket-{data["number_of_tickets"]:04d}'
            except:
                await interaction.response.send_message("You need to specify the admin role (use: setadmin command)", ephemeral=True)
                return

            overwrites = {
    server.default_role: discord.PermissionOverwrite(read_messages=False),
    server.get_role(int(admin_role_id)): discord.PermissionOverwrite(read_messages=True),
    interaction.user: discord.PermissionOverwrite(read_messages=True)
}
            
            if data["category_name"] == "":
                channel = await server.create_text_channel(name=TICKET_NAME, overwrites=overwrites)
            else: 
                for i in server.categories: 
                    if i.name == data["category_name"]:
                        channel = await i.create_text_channel(name=TICKET_NAME, overwrites=overwrites)
                        valid_category = True
                if valid_category == False: return await interaction.response.send_message(
                    "No se encuentra la caterogría especificada", ephemeral=True)

            embed = discord.Embed(
                title=data["ticket_title"],
                description=data["ticket_description"]
            )

            await channel.send(data["ticket_message"], embed=embed)

            data["number_of_tickets"]+=1
            data["opened_tickets"][str(interaction.user.id)] = channel.id
            tickets[str(interaction.message.id)] = data
            await interaction.response.send_message(f"Ticket created, check {channel.mention}", ephemeral=True, delete_after=15.00)
            with open("./storage/tickets.json", "w") as tickets_file:
                json.dump(tickets, tickets_file, indent=4)
        
async def printf(text, level="INFO"):
    date = datetime.datetime.now()
    formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
    current_datetime = (f"{Fore.BLACK}{Style.BRIGHT}{formatted_date[:10]}{Style.RESET_ALL}"f" {Fore.BLACK}{Style.BRIGHT}{formatted_date[11:19]}{Style.RESET_ALL}")
    msg = (f"{current_datetime} "f"{Fore.BLUE}{Style.BRIGHT}{level:<8}{Style.RESET_ALL} "f"{text}")
    print(msg)

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
                await printf(f"[-] Channel {channel_id} not found")
                await delete_entry_from_json("./storage/channels.json", channel_id)
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
        await printf("[+] Successfully updated tickets JSON.")

async def delete_entry_from_json(file_path, entry_id):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
    if entry_id in data:
        del data[entry_id]
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
            await printf("[+] Entry deleted from JSON successfully.")
    else:
        await printf("[-] Entry not found in JSON.")


@bot.event
async def on_ready():
    await printf(f'We have logged in as {bot.user}')
    await printf('Loading slash commands...')
    await bot.tree.sync()
    await printf("Loadding all the tickets...")
    await reload_buttons()
    await printf("All the tickets have been loaded!")
    await asyncio.sleep(3.0)
    await printf(f"{Fore.LIGHTGREEN_EX}All the bot have been loaded successfully"+Style.RESET_ALL)

@bot.command(name="setadmin", description="Set the ticket admin role for the server")
async def execute_setadmin(ctx: discord.Interaction, role: discord.Role):
    if ctx.author.guild_permissions.administrator: 
        try:
            with open('./storage/servers.json', 'r+') as servers_file:
                servers_data = json.load(servers_file)
                servers_data[str(ctx.guild.id)] = str(role.id) 
                servers_file.seek(0)
                json.dump(servers_data, servers_file, indent=4)
                await ctx.reply("Se ha actualizado el rol de administrador correctamente!", ephemeral=True)
        except Exception as e:
            await ctx.reply(f"Se ha producido un error {e}")
    else:
        await ctx.reply("You are not allowed to do this.", ephemeral=True)

async def is_admin(ctx: discord.ext.commands.Context) -> bool:
    if ctx.guild.get_role(
        int(json.load(open('./storage/servers.json', 'r'))[str(ctx.guild.id)])
      ) in ctx.author.roles:
        return True
    elif ctx.author.guild_permissions.administrator:
        return True
    else: return False
        
async def is_ticket(ctx: discord.ext.commands.Context) -> bool:
    tickets = json.load(open('./storage/tickets.json', 'r'))
    for ticket in tickets:
        for channel_id in tickets[ticket]['opened_tickets']:
            if tickets[ticket]['opened_tickets'][channel_id] == ctx.channel.id:
                return True, ticket, channel_id
    return False, None, None

@bot.tree.command(name="close", description="Close the current ticket")
async def execute_close_slash(ctx: discord.ext.commands.Context, reason: str | None):
    ticket, ticket_id, user_id = await is_ticket(ctx)
    if await is_admin(ctx):
        if ticket:
            await ctx.send(f"{ctx.user.mention} Ha cerrado el ticket, borrando en 5s")
            await asyncio.sleep(5)
            await ctx.channel.delete()
            with open('./storage/tickets.json', 'r+') as tickets_file:
                data = json.load(tickets_file)
                data[ticket_id]['opened_tickets'].pop(user_id)
                tickets_file.seek(0)
                tickets_file.truncate()
                json.dump(data, tickets_file, indent=4)
        else:
            await ctx.interaction.response.send_message("Este no es un ticket :/", ephemeral=True)
    else:
        await ctx.interaction.response.send_message(f"No tienes permisos para hacer esto", ephemeral=True)

@bot.command(name="close", description="Close the current ticket")
async def excecute_close(ctx: discord.ext.commands.Context, reason: str | None):
    ticket, ticket_id, user_id = await is_ticket(ctx)
    if await is_admin(ctx): 
        if ticket:
            await ctx.send(f"{ctx.author.mention} Ha cerrado el ticket, borrando en 5s")
            await asyncio.sleep(5)
            await ctx.channel.delete()
            with open('./storage/tickets.json', 'r+') as tickets_file:
                data = json.load(tickets_file)
                data[ticket_id]['opened_tickets'].pop(user_id)
                tickets_file.seek(0)
                tickets_file.truncate()
                json.dump(data, tickets_file, indent=4)
        else:
            await ctx.message.reply("Este no es un ticket :/")
    else:
        await ctx.message.reply(f"No tienes permisos para hacer esto {ctx.author.mention}")

@bot.tree.command(name='setup', description="Create a new ticket systen and send the ticket message")
async def execute_setup_slash(ctx: discord.Interaction,
                              title: str | None,
                              description: str | None,
                              category_name: str | None,
                              ticket_title: str | None,
                              ticket_description: str | None,
                              ticket_message: str | None):
        
    if title is None: title = "Welcome to the ticket system"
    if description is None: description = "Click on the button below to create a ticket!"
    if category_name is None: category_name = ""
    if ticket_title is None: ticket_title = "Welcome"
    if ticket_description is None: ticket_description = "Wait until you recive suport from our staff"
    if ticket_message is None: ticket_message = ""
    create_ticket = Create_Ticket_Button()

    new_embed = discord.Embed(title=title, description=description)
    message = await ctx.channel.send(embed=new_embed, view=discord.ui.View().add_item(item=create_ticket))
    await ctx.response.send_message("Done!", ephemeral=True, delete_after=3.0)
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
    "ticket_title": ticket_title,
    "ticket_description": ticket_description,
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
        "ticket_title": ticket_title,
        "ticket_description": ticket_description,
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
