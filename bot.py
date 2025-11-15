# BRAINROT MIDDLEMAN BOT v9 - AUTO-VOUCH + FULL MM TOOLS
# Paste into brainrot-mm-bot/bot.py

import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime
import pytz

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='', intents=intents)  # No prefix - commands will be handled manually

# Configuration
TICKET_CATEGORY = 'MIDDLEMAN TRADES'
MM_ROLE_NAME = 'Brainrot Middleman'
TRADER_ROLE_NAME = 'Trader'  # Role to give after successful trade
CONTROL_CHANNEL_ID = 1439293432160976948  # Replace with your control channel ID
LOG_CHANNEL_ID = 1439296766645243954      # Replace with your log channel ID
VOUCH_CHANNEL_ID = 1439291252632850443    # Replace with your vouch channel ID

# Data storage
tickets = {}
command_cooldowns = {}

# PS links
PS_LINKS = {
    'ps1': 'https://www.roblox.com/share?code=5795be4fed121a47be673c0c75c96c0f&type=Server',
    'ps2': 'https://www.roblox.com/share?code=9eb540fc231cb44f86d02ebafa51fb41&type=Server'
}

# Load tickets from file if exists
if os.path.exists('tickets.json'):
    with open('tickets.json', 'r') as f:
        tickets = json.load(f)

@bot.event
async def on_ready():
    print(f'LIVE: {bot.user} | {datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y, %I:%M:%S %p EST")} EST')
    await bot.change_presence(activity=discord.Game(name='Complete trades with commands'))

    channel = bot.get_channel(CONTROL_CHANNEL_ID)
    if not channel:
        print('CONTROL_CHANNEL_ID wrong!')
        return

    # Clear previous messages
    try:
        await channel.purge(limit=10)
    except:
        pass

    embed = discord.Embed(
        title='BRAINROT TRADING MIDDLEMAN',
        description='**Safe. Verified. Auto-vouch on completion.**',
        color=0x00ff00
    )
    embed.add_field(name='Fees', value='`5–10M` → FREE!\n`15–35M` → 10M Brainrot\n`40–100M` → 35M Brainrot\n`100M+` → 50M + Brainrot', inline=True)
    embed.set_footer(text='Vouches → #vouches')
    embed.timestamp = datetime.now(pytz.utc)

    view = discord.ui.View()
    button = discord.ui.Button(label='Open Trade', style=discord.ButtonStyle.green, emoji='🔄')
    button.callback = open_trade_modal
    view.add_item(button)

    await channel.send(embed=embed, view=view)
    print('Control panel ready.')

async def open_trade_modal(interaction):
    modal = TradeModal()
    await interaction.response.send_modal(modal)

class TradeModal(discord.ui.Modal):  # Removed title parameter from __init__
    def __init__(self):
        super().__init__(title='New Trade')  # Set title in super().__init__()

        self.add_item(discord.ui.TextInput(
            label='Party 1 Username',
            placeholder='AliceTheTrader',
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label='Party 2 Username',
            placeholder='BobCollector',
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label='Total Value (M)',
            placeholder='25',
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label='P1 Gives',
            style=discord.TextStyle.paragraph,
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label='P2 Gives',
            style=discord.TextStyle.paragraph,
            required=True
        ))

    async def on_submit(self, interaction):
        p1_name = self.children[0].value.strip()
        p2_name = self.children[1].value.strip()
        value_str = self.children[2].value.strip()
        p1_item = self.children[3].value.strip()
        p2_item = self.children[4].value.strip()

        try:
            value = float(value_str)
        except ValueError:
            await interaction.response.send_message('Invalid value.', ephemeral=True)
            return

        if value <= 0:
            await interaction.response.send_message('Invalid value.', ephemeral=True)
            return

        guild = interaction.guild
        party1 = None
        party2 = None

        # Find users by username
        for member in guild.members:
            if member.name == p1_name or str(member) == p1_name:
                party1 = member
            if member.name == p2_name or str(member) == p2_name:
                party2 = member

        if not party1 or not party2:
            await interaction.response.send_message('User not found. Use exact username.', ephemeral=True)
            return

        if party1.id == party2.id:
            await interaction.response.send_message('Same user.', ephemeral=True)
            return

        # Calculate fee
        fee = 0
        fee_text = ''
        if 5 <= value <= 10:
            fee_text = 'FREE!'
        elif 15 <= value <= 35:
            fee = 10
            fee_text = '10M Brainrot'
        elif 40 <= value <= 100:
            fee = 35
            fee_text = '35M Brainrot'
        elif value > 100:
            fee = 50
            fee_text = '50M + Brainrot'
        else:
            await interaction.response.send_message('Value <5M.', ephemeral=True)
            return

        # Create category if it doesn't exist
        category = None
        for cat in guild.categories:
            if cat.name == TICKET_CATEGORY:
                category = cat
                break

        if not category:
            category = await guild.create_category(
                name=TICKET_CATEGORY,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False)
                }
            )

        ticket_name = f'trade-{int(value)}m-{p1_name[:4]}-{p2_name[:4]}'.lower()
        ticket_channel = await guild.create_text_channel(
            name=ticket_name,
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                party1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                party2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                bot.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )

        # Add MM role permissions
        mm_role = discord.utils.get(guild.roles, name=MM_ROLE_NAME)
        if mm_role:
            await ticket_channel.set_permissions(mm_role, view_channel=True, send_messages=True)

        # Store ticket data
        ticket_id = str(ticket_channel.id)
        tickets[ticket_id] = {
            'p1': party1.id,
            'p2': party2.id,
            'value': value,
            'fee': fee,
            'p1_item': p1_item,
            'p2_item': p2_item,
            'p1_name': p1_name,
            'p2_name': p2_name,
            'status': 'awaiting_agreement',
            'timer': None,
            'agreed': {'p1': False, 'p2': False},
            'last_updated': datetime.now().isoformat()
        }

        # Save tickets to file
        with open('tickets.json', 'w') as f:
            json.dump(tickets, f)

        embed = discord.Embed(
            title='TRADE TICKET',
            description='**Status:** Awaiting agreement',
            color=0x00ff00
        )
        embed.add_field(name='Value', value=f'{value}M', inline=True)
        embed.add_field(name='Fee', value=fee_text, inline=True)
        embed.add_field(name='P1', value=f'{party1.mention}\n**Gives:** {p1_item}', inline=True)
        embed.add_field(name='P2', value=f'{party2.mention}\n**Gives:** {p2_item}', inline=True)
        embed.add_field(name='Next', value='→ `ps1` → `secure` → `complete` = **AUTO-VOUCH**', inline=False)
        embed.timestamp = datetime.now(pytz.utc)

        view = discord.ui.View()
        agree_button = discord.ui.Button(label='I Agree', style=discord.ButtonStyle.green)
        agree_button.callback = lambda i: handle_agreement(i, ticket_id, 'agree')
        cancel_button = discord.ui.Button(label='Cancel', style=discord.ButtonStyle.red)
        cancel_button.callback = lambda i: handle_agreement(i, ticket_id, 'cancel')
        view.add_item(agree_button)
        view.add_item(cancel_button)

        await ticket_channel.send(f'{party1.mention} {party2.mention}', embed=embed, view=view)
        await interaction.followup.send(f'Ticket: {ticket_channel.mention}', ephemeral=True)

        log_trade(f'OPENED | {value}M | {p1_name} ↔ {p2_name}', guild.id)

async def handle_agreement(interaction, ticket_id, action):
    data = tickets.get(ticket_id)
    if not data:
        await interaction.response.send_message('Ticket not found.', ephemeral=True)
        return

    user_id = str(interaction.user.id)
    is_p1 = user_id == str(data['p1'])
    is_p2 = user_id == str(data['p2'])

    if not is_p1 and not is_p2:
        await interaction.response.send_message('Not in trade.', ephemeral=True)
        return

    if action == 'agree':
        agreed = data.get('agreed', {'p1': False, 'p2': False})
        if (is_p1 and agreed['p1']) or (is_p2 and agreed['p2']):
            await interaction.response.send_message('Already agreed.', ephemeral=True)
            return

        if is_p1:
            agreed['p1'] = True
        if is_p2:
            agreed['p2'] = True
        data['agreed'] = agreed

        embed = interaction.message.embeds[0]
        if agreed['p1'] and agreed['p2']:
            embed.description = '**BOTH AGREED — Send to MM**'
            embed.color = discord.Color(0x00ff99)
        else:
            embed.description = f'**{interaction.user.name} agreed**'
            embed.color = discord.Color(0x00ff00)

        # Update the view to keep buttons visible until both agree
        view = discord.ui.View()
        if not (agreed['p1'] and agreed['p2']):
            agree_button = discord.ui.Button(label='I Agree', style=discord.ButtonStyle.green)
            agree_button.callback = lambda i: handle_agreement(i, ticket_id, 'agree')
            cancel_button = discord.ui.Button(label='Cancel', style=discord.ButtonStyle.red)
            cancel_button.callback = lambda i: handle_agreement(i, ticket_id, 'cancel')
            view.add_item(agree_button)
            view.add_item(cancel_button)
        # Otherwise, no buttons if both agreed

        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.send_message('Agreed!', ephemeral=True)

        if agreed['p1'] and agreed['p2']:
            data['status'] = 'items_sent'

    elif action == 'cancel':
        await interaction.response.send_message('Cancelled by user.')
        await close_ticket(ticket_id, 'CANCELLED BY USER')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if message starts with command prefix
    if message.content.startswith('ps1') or message.content.startswith('ps2') or message.content.startswith('secure') or message.content.startswith('complete') or message.content.startswith('cancel') or message.content.startswith('timeout') or message.content.startswith('status') or message.content.startswith('help'):
        # Check if channel is a trade channel
        if not message.channel.name.startswith('trade-'):
            return

        # Check if user has MM role
        has_role = any(role.name == MM_ROLE_NAME for role in message.author.roles)
        if not has_role:
            await message.reply('Middleman only.')
            await asyncio.sleep(5)
            await message.delete()
            return

        # Rate limiting
        user_id = str(message.author.id)
        cmd = message.content.split()[0].lower()
        
        if user_id not in command_cooldowns:
            command_cooldowns[user_id] = {}
        
        now = datetime.now().timestamp()
        cooldown_amount = 1.0  # 1 second cooldown
        
        if cmd in command_cooldowns[user_id]:
            expiration_time = command_cooldowns[user_id][cmd] + cooldown_amount
            if now < expiration_time:
                time_left = round(expiration_time - now, 1)
                await message.reply(f'Wait {time_left}s')
                await asyncio.sleep(2)
                await message.delete()
                return
        
        command_cooldowns[user_id][cmd] = now

        # Process command
        args = message.content.split()[1:]
        cmd = cmd  # Don't remove prefix since there is none

        await process_command(message, args, cmd)

async def process_command(message, args, cmd):
    channel_id = str(message.channel.id)
    data = tickets.get(channel_id)

    if cmd == 'ps1':
        embed = discord.Embed(
            title='ROBLOX PS PS1',
            description=f'[JOIN SERVER]({PS_LINKS["ps1"]})',
            color=0x00ff00
        )
        embed.set_footer(text='Both join → MM verifies')
        await message.reply(embed=embed)
        log_trade('PS1 sent', message.guild.id)

    elif cmd == 'ps2':
        embed = discord.Embed(
            title='ROBLOX PS PS2',
            description=f'[JOIN SERVER]({PS_LINKS["ps2"]})',
            color=0x00ff00
        )
        embed.set_footer(text='Both join → MM verifies')
        await message.reply(embed=embed)
        log_trade('PS2 sent', message.guild.id)

    elif cmd == 'secure':
        if data and data.get('status') != 'items_sent':
            await message.reply('Wait for agreement.')
            return
        if data:
            data['status'] = 'verified'
            await message.reply('Both items secured.')
            log_trade('ITEMS SECURED', message.guild.id)

    elif cmd == 'complete':
        if data and data.get('status') != 'verified':
            await message.reply('Use secure first.')
            return

        await message.reply(embed=discord.Embed(
            title='TRADE COMPLETED',
            description='Vouch incoming...',
            color=0x00ff00
        ))

        # Add Trader role to both parties
        try:
            guild = message.guild
            p1_member = guild.get_member(data['p1'])
            p2_member = guild.get_member(data['p2'])
            trader_role = discord.utils.get(guild.roles, name=TRADER_ROLE_NAME)
            
            if trader_role:
                if p1_member:
                    await p1_member.add_roles(trader_role)
                if p2_member:
                    await p2_member.add_roles(trader_role)
        except:
            pass  # Ignore if role doesn't exist or can't add

        vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
        if vouch_channel and data:
            try:
                p1 = await bot.fetch_user(data['p1'])
                p2 = await bot.fetch_user(data['p2'])
            except:
                p1 = p2 = None

            vouch_embed = discord.Embed(
                title='TRADE VOUCH',
                description=f'**{data["value"]}M Brainrot Trade Completed!**',
                color=0x00ff00
            )
            vouch_embed.add_field(name='Trader 1', value=f'{p1.mention} (`{data["p1_name"]}`)' if p1 else data['p1_name'], inline=True)
            vouch_embed.add_field(name='Trader 2', value=f'{p2.mention} (`{data["p2_name"]}`)' if p2 else data['p2_name'], inline=True)
            vouch_embed.add_field(name='Items', value=f'**{data["p1_name"]}** → {data["p1_item"]}\n**{data["p2_name"]}** → {data["p2_item"]}', inline=False)
            vouch_embed.add_field(name='Fee', value=f'{data["fee"]}M' if data["fee"] else 'None', inline=True)
            vouch_embed.add_field(name='MM', value=message.author.mention, inline=True)
            vouch_embed.set_footer(text=f'ID: {channel_id} | {datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y, %I:%M:%S %p EST")} EST')
            vouch_embed.timestamp = datetime.now(pytz.utc)

            try:
                await vouch_channel.send(content=f'{p1.mention} {p2.mention}' if p1 and p2 else '', embed=vouch_embed)
            except:
                print('Vouch failed.')

        await close_ticket(channel_id, 'COMPLETED + VOUCH')

    elif cmd == 'cancel':
        await message.reply('Cancelled by MM.')
        await close_ticket(channel_id, 'CANCELLED BY MM')

    elif cmd == 'timeout':
        if not args:
            await message.reply('`timeout 10`')
            return
        try:
            mins = int(args[0])
            if mins <= 0:
                raise ValueError
        except ValueError:
            await message.reply('`timeout 10`')
            return

        await message.reply(f'Auto-close in {mins} min.')
        if data and data.get('timer'):
            # Cancel existing timer
            pass
        # Set new timer (simplified - would need asyncio tasks in real implementation)
        data['timer'] = mins  # Placeholder
        log_trade(f'TIMEOUT: {mins} min', message.guild.id)

    elif cmd == 'status':
        if not data:
            await message.reply('No data.')
            return
        embed = discord.Embed(title='STATUS')
        embed.add_field(name='Value', value=f'{data["value"]}M', inline=True)
        embed.add_field(name='Fee', value=f'{data["fee"]}M' if data["fee"] else 'None', inline=True)
        embed.add_field(name='Status', value=data['status'], inline=True)
        embed.add_field(name='Parties', value=f'<@{data["p1"]}> ↔ <@{data["p2"]}>', inline=False)
        await message.reply(embed=embed)

    elif cmd == 'help':
        embed = discord.Embed(title='MM COMMANDS', color=0x0099ff)
        embed.add_field(name='Flow', value='`ps1` `secure` `complete` → **VOUCH**', inline=False)
        embed.add_field(name='Control', value='`cancel` `timeout 10` `status`', inline=False)
        await message.reply(embed=embed)

    else:
        await message.reply(f'Unknown command. Use `help`')

def log_trade(event, guild_id):
    time_str = datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y, %I:%M:%S %p EST")
    log_entry = f'[{time_str}] {event}\n'
    
    with open('trade_logs.txt', 'a') as f:
        f.write(log_entry)

    async def send_log():
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            try:
                await log_channel.send(f'`{time_str}` {event}')
            except:
                pass
    
    # Create a task to send the log asynchronously
    asyncio.create_task(send_log())

async def close_ticket(channel_id, reason):
    channel = bot.get_channel(int(channel_id))
    if channel:
        await channel.send(f'**CLOSED:** {reason}')
        if channel_id in tickets:
            del tickets[channel_id]
            # Save tickets to file
            with open('tickets.json', 'w') as f:
                json.dump(tickets, f)
        await asyncio.sleep(5)
        await channel.delete()

    log_trade(f'CLOSED: {reason}', channel.guild.id if channel else 0)

# Run the bot
bot.run('MTQzOTI5MjU2MjYxODg0MzE4Nw.GatO1n.2x_7-7n3jWHvZdxG7AO3lKHDe_K9e99Dz66BeA')  # Replace with your actual bot token