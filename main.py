import discord
from discord import Webhook
import aiohttp
import asyncio
import config
import json
import os

class MirrorClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_id_file = "last_id.txt"
        self.map_file = "message_map.json"

    async def get_webhook(self, url, session):
        """Helper to create a webhook object compatible with different library versions."""
        try:
            # Try new version (discord.py 2.0+)
            return Webhook.from_url(url, session=session)
        except TypeError:
            try:
                # Try older version (discord.py 1.7.x)
                return Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(session))
            except:
                return Webhook.from_url(url)

    def load_map(self):
        if not os.path.exists(self.map_file):
            return {}
        try:
            with open(self.map_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def save_map(self, source_id, webhook_id):
        mapping = self.load_map()
        mapping[str(source_id)] = str(webhook_id)
        if len(mapping) > 1000:
            keys = sorted(mapping.keys())
            for k in keys[:-1000]:
                del mapping[k]
        try:
            with open(self.map_file, "w") as f:
                json.dump(mapping, f)
        except:
            pass

    def get_last_id(self):
        try:
            with open(self.last_id_file, "r") as f:
                return int(f.read().strip())
        except:
            return None

    def save_last_id(self, msg_id):
        try:
            with open(self.last_id_file, "w") as f:
                f.write(str(msg_id))
        except:
            pass

    async def on_ready(self):
        print(f'--- MIRROR BOT ACTIVE ---')
        print(f'Logged in as: {self.user.name} ({self.user.id})')
        
        # Verify source channel
        source_channel = self.get_channel(config.SOURCE_ID)
        if source_channel:
            print(f"✅ Source channel found: #{source_channel.name} (ID: {source_channel.id})")
        else:
            print(f"❌ Source channel NOT found! Check SOURCE_ID: {config.SOURCE_ID}")

        # Webhook Test
        print("🔍 Testing webhook visibility...")
        async with aiohttp.ClientSession() as session:
            try:
                webhook = await self.get_webhook(config.WEBHOOK_URL, session)
                # Use direct send for the test too
                payload = {"content": "🚀 **Bot jest online i nasłuchuje!** (Test połączenia)", "username": "Mirror Selfbot System"}
                async with session.post(f"{webhook.url}?wait=true", json=payload) as resp:
                    if resp.status < 300:
                        print("✅ Test message sent to webhook! If you don't see it, your WEBHOOK_URL is wrong.")
            except Exception as e:
                print(f"❌ Webhook test failed: {e}")

    async def _handle_webhook_resp(self, resp, message):
        if resp.status < 300:
            data = await resp.json()
            sent_id = data.get('id')
            if sent_id:
                self.save_last_id(message.id)
                self.save_map(message.id, sent_id)
                return sent_id
        else:
            txt = await resp.text()
            print(f"Direct Webhook Error {resp.status}: {txt}")
        return True

    async def forward_message(self, webhook, message, is_edit=False, webhook_msg_id=None):
        try:
            author = message.author
            author_name = author.display_name
            
            # Robust avatar handling
            author_avatar = None
            if hasattr(author, 'avatar') and author.avatar:
                author_avatar = author.avatar.url if hasattr(author.avatar, 'url') else str(author.avatar)
            
            if not author_avatar or not str(author_avatar).startswith("http"):
                if hasattr(author, 'default_avatar') and author.default_avatar:
                    author_avatar = author.default_avatar.url if hasattr(author.default_avatar, 'url') else str(author.default_avatar)
            
            if author_avatar and not str(author_avatar).startswith("http"):
                author_avatar = None
            
            # Generate Discord timestamp
            timestamp_unix = int(message.created_at.timestamp())
            discord_time = f"<t:{timestamp_unix}:t> (<t:{timestamp_unix}:R>)"
            
            content = message.content or ""
            
            # Handle reply references
            if message.reference and message.reference.message_id:
                try:
                    replied_msg = await message.channel.fetch_message(message.reference.message_id)
                    replied_content = replied_msg.content or ("[Załącznik]" if replied_msg.attachments else "[Treść]")
                    if len(replied_content) > 100:
                        replied_content = replied_content[:97] + "..."
                    content = f"> ↪️ *Odpowiedź dla: **{replied_msg.author.display_name}**: \"{replied_content}\"*\n" + content
                except:
                    content = f"> ↪️ *Odpowiedź dla: [Nieznany Użytkownik]*\n" + content

            # Append timestamp and edit status
            status_suffix = "\n\n" + f"🕒 *Sent: {discord_time}*"
            if is_edit:
                status_suffix += " • *(edited)*"
            content += status_suffix

            # Handle attachments
            files = []
            attachment_links = []
            for attachment in message.attachments:
                try:
                    if attachment.size < 8 * 1024 * 1024:
                        files.append(await attachment.to_file())
                    else:
                        attachment_links.append(attachment.url)
                except:
                    attachment_links.append(attachment.url)
            
            if attachment_links:
                content += "\n" + "\n".join([f"📎 **Załącznik:** {url}" for url in attachment_links])

            if not content.strip() and not files:
                content = "_[Wiadomość bez treści]_"

            # Direct Webhook Send via aiohttp
            session = getattr(webhook, '_session', None)
            url = f"{webhook.url}?wait=true"
            payload = {
                "content": content,
                "username": author_name,
                "avatar_url": author_avatar
            }

            if webhook_msg_id:
                # Edit
                edit_url = f"{webhook.url}/messages/{webhook_msg_id}"
                if session:
                    async with session.patch(edit_url, json={"content": content}) as resp:
                        if resp.status < 300: print(f"Updated: {author_name}")
                else:
                    async with aiohttp.ClientSession() as temp_session:
                        async with temp_session.patch(edit_url, json={"content": content}) as resp:
                            if resp.status < 300: print(f"Updated: {author_name}")
            else:
                # New Message
                async def send_req(sess):
                    if files:
                        form = aiohttp.FormData()
                        form.add_field('payload_json', json.dumps(payload))
                        for i, f in enumerate(files):
                            form.add_field(f'file{i}', f.fp, filename=f.filename)
                        return await sess.post(url, data=form)
                    else:
                        return await sess.post(url, json=payload)

                if session:
                    resp = await send_req(session)
                    return await self._handle_webhook_resp(resp, message)
                else:
                    async with aiohttp.ClientSession() as temp_session:
                        resp = await send_req(temp_session)
                        return await self._handle_webhook_resp(resp, message)
            return True
        except Exception as e:
            print(f"Forwarding Error: {e}")
            return False

    async def on_message(self, message):
        if message.webhook_id or (message.author.id == self.user.id and not message.content.startswith('!')):
            return
            
        is_from_source = message.channel.id == config.SOURCE_ID
        
        if is_from_source:
            async with aiohttp.ClientSession() as session:
                webhook = await self.get_webhook(config.WEBHOOK_URL, session)
                await self.forward_message(webhook, message)
                print(f"Forwarded: {message.author.display_name} at {message.created_at.strftime('%H:%M')}")

        # REPORT FEATURE
        if message.content.startswith('!report') and is_from_source:
            parts = message.content.split()
            if len(parts) >= 2:
                try:
                    report_id = int(parts[1])
                    target_msg = await message.channel.fetch_message(report_id)
                    embed = discord.Embed(title='Message Report', color=0xFF0000, timestamp=target_msg.created_at)
                    embed.add_field(name='Author', value=f"{target_msg.author.display_name} ({target_msg.author.id})")
                    embed.add_field(name='Content', value=target_msg.content or '[No Text]', inline=False)
                    if target_msg.attachments:
                        embed.add_field(name='Attachments', value='\n'.join([a.url for a in target_msg.attachments]))
                    
                    async with aiohttp.ClientSession() as sess:
                        report_webhook = await self.get_webhook(config.REPORT_WEBHOOK_URL, sess)
                        await report_webhook.send(embed=embed)
                        print(f"Report for {report_id} sent.")
                except Exception as e:
                    print(f"Report Error: {e}")

if __name__ == "__main__":
    if not config.TOKEN:
        print("Error: SECRET_TOKEN not found in config.txt file.")
    else:
        client = MirrorClient()
        client.run(config.TOKEN, bot=False)
