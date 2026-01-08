import discord
from discord import Webhook
import aiohttp
import asyncio
import config

class MirrorClient(discord.Client):
    async def on_ready(self):
        print(f'--- MIRROR BOT ACTIVE ---')
        print(f'Logged in as: {self.user.name}')

    async def on_message(self, message):
        # Ignore messages from self or other webhooks to prevent loops
        if message.author.id == self.user.id or message.webhook_id:
            return

        # Check if the message is from the source channel
        if message.channel.id == config.SOURCE_ID:
            async with aiohttp.ClientSession() as session:
                try:
                    webhook = Webhook.from_url(config.WEBHOOK_URL, session=session)
                    
                    # Get user's preferred display name (nick or global name)
                    author_name = message.author.display_name
                    author_avatar = message.author.avatar.url if message.author.avatar else None
                    
                    # Generate Discord timestamp
                    timestamp_unix = int(message.created_at.timestamp())
                    discord_time = f"<t:{timestamp_unix}:t> (<t:{timestamp_unix}:R>)"
                    
                    content = message.content or ""
                    
                    # Handle reply references
                    if message.reference and message.reference.message_id:
                        try:
                            replied_msg = await message.channel.fetch_message(message.reference.message_id)
                            content = f"> ↪️ *Replying to: {replied_msg.author.display_name}*\n" + content
                        except:
                            content = f"> ↪️ *Replying to: [Unknown User]*\n" + content
    
                    # Append timestamp to the message content
                    if content:
                        content += f"\n\n🕒 *Sent: {discord_time}*"
                    else:
                        content = f"🕒 *Sent: {discord_time}*"
    
                    # Handle message attachments
                    files = []
                    for attachment in message.attachments:
                        try:
                            files.append(await attachment.to_file())
                        except:
                            pass
    
                    await webhook.send(
                        content=content,
                        username=author_name,
                        avatar_url=author_avatar,
                        files=files
                    )
                    print(f"Forwarded: {author_name} at {message.created_at.strftime('%H:%M')}")
                except Exception as e:
                    print(f"Webhook Error: {e}")

        # --- REPORT FEATURE ---
        if message.content.startswith('!report') and message.channel.id == config.SOURCE_ID:
            parts = message.content.split()
            if len(parts) >= 2:
                try:
                    report_id = int(parts[1])
                    target_msg = await message.channel.fetch_message(report_id)
                    
                    embed = discord.Embed(
                        title='Message Report', 
                        description='A message has been reported for review.',
                        color=0xFF0000, 
                        timestamp=target_msg.created_at
                    )
                    embed.add_field(name='Author', value=f"{target_msg.author.display_name} ({target_msg.author.id})", inline=True)
                    embed.add_field(name='Content', value=target_msg.content or '[No Text]', inline=False)
                    embed.add_field(name='Message ID', value=str(target_msg.id), inline=True)
                    
                    if target_msg.attachments:
                        urls = '\n'.join([a.url for a in target_msg.attachments])
                        embed.add_field(name='Attachments', value=urls, inline=False)
                    
                    async with aiohttp.ClientSession() as report_session:
                        report_webhook = Webhook.from_url(config.REPORT_WEBHOOK_URL, session=report_session)
                        await report_webhook.send(embed=embed)
                        print(f"Report for message {report_id} sent successfully.")
                except Exception as e:
                    print(f"Reporting Error: {e}")

if __name__ == "__main__":
    if not config.TOKEN:
        print("Error: SECRET_TOKEN not found in .env file.")
    else:
        client = MirrorClient()
        client.run(config.TOKEN)
