from typing import Optional, TYPE_CHECKING

import discord
from discord.ext import commands, tasks
from asyncio import get_event_loop, sleep
from Weverse import WeverseClientAsync, models
from os import getenv
from aiohttp import ClientSession
from models import TextChannel
from random import randint
import aiofiles

if TYPE_CHECKING:
    from ..run import WeverseBot


class Weverse(commands.Cog):
    def __init__(self, bot):
        self.bot: WeverseBot = bot
        self._channels = {}  # Community Name : { channel_id: models.TextChannel }
        loop = get_event_loop()
        loop.create_task(self.fetch_channels())
        self._web_session = ClientSession()
        client_kwargs = {
            "verbose": True,  # Will print warning messages for links that have failed to connect or were not found.
            "web_session": self._web_session,  # Existing web session
            "authorization": getenv("WEVERSE_TOKEN"),  # Auth Token to connect to Weverse
            "loop": loop  # current event loop
        }

        self._translate_headers = {"Authorization": getenv("TRANSLATION_KEY")}
        self._translate_endpoint = getenv("TRANSLATION_URL")
        self._weverse_image_folder = getenv("WEVERSE_FOLDER_LOCATION")
        self._upload_from_host = getenv("UPLOAD_FROM_HOST")

        self.weverse_client = WeverseClientAsync(**client_kwargs)
        loop.create_task(self.weverse_client.start(create_old_posts=False))

        self.weverse_updates.start()

    async def cog_check(self, ctx):
        """A local check for this cog. Checks if the user is a data mod."""
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("This command can not be used in DMs.")
            return False
        return True

    async def translate(self, text) -> Optional[str]:
        """Sends a request to translating endpoint from KR to EN and returns the translated string."""
        try:
            data = {
                'text': text,
                'src_lang': "KR",
                'target_lang': "EN",
            }
            async with self._web_session.post(self._translate_endpoint, headers=self._translate_headers, data=data) \
                    as r:
                if r.status == 200:
                    body = await r.json()
                    if body.get("code") == 0:
                        return body.get("text")
        except Exception as e:
            print(f"{e} - (Exception)")

    async def fetch_channels(self):
        """Fetch the channels from DB and add them to cache."""
        while not self.bot.conn.pool:
            await sleep(1)  # give time for DataBase connection to establish
        for channel_id, community_name, role_id, media_enabled, comments_enabled \
                in await self.bot.conn.fetch_channels():
            self.add_to_cache(community_name, channel_id, role_id, media_enabled, comments_enabled)

    def is_following(self, community_name, channel_id):
        """Check if a channel is following a community."""
        community_name = community_name.lower()
        followed_channels = self._channels.get(community_name)
        if not followed_channels:
            return False

        return channel_id in followed_channels.keys()

    def check_community_exists(self, community_name):
        """Check if a community name exists."""
        if not community_name:
            return False

        return community_name.lower() in self.get_community_names()

    def get_community_names(self) -> list:
        """Returns a list of all available community names."""
        return [t_community.name.lower() for t_community in self.weverse_client.all_communities.values()]

    def get_channel(self, community_name, channel_id) -> Optional[TextChannel]:
        """Get a models.TextChannel object from a community"""
        channels = self._channels.get(community_name)
        if channels:
            return channels.get(channel_id)

    def add_to_cache(self, community_name, channel_id, role_id, media_enabled, comments_enabled):
        """Add a channel to cache."""
        community_name = community_name.lower()
        channels = self._channels.get(community_name)
        this_channel = TextChannel(channel_id, role_id, media_enabled, comments_enabled)
        if not channels:
            self._channels[community_name] = {channel_id: this_channel}
        else:
            channels[channel_id] = this_channel

    async def send_communities_available(self, ctx):
        """Send the available communites to a text channel."""
        community_names = ', '.join(self.get_community_names())

        return await ctx.send(f"The communities available are: ``{community_names}``.")

    async def delete_channel(self, channel_id, community_name):
        """Deletes a channel from a community in the cache and db."""
        channels = self._channels.get(community_name.lower())
        try:
            channels.pop(channel_id)
        except AttributeError or KeyError:
            pass
        await self.bot.conn.delete_weverse_channel(channel_id, community_name)

    @commands.command(aliases=["updates"])
    async def weverse(self, ctx, *, community_name: str = None):
        """Follow or Unfollow a Weverse Community."""
        community_names = ', '.join(self.get_community_names())
        if not community_name:
            return await self.send_communities_available(ctx)

        community_name = community_name.lower()

        community: Optional[models.Community] = None
        for t_community in self.weverse_client.all_communities.values():
            if t_community.name.lower() == community_name:
                community = t_community

        if not community:
            return await ctx.send(f"The Weverse Community Name you have entered does not exist. Your options are "
                                  f"``{community_names}``.")

        if self.is_following(community.name, ctx.channel.id):
            await self.delete_channel(ctx.channel.id, community.name)
            await ctx.send(f"You are no longer following {community_name}.")
        else:
            self.add_to_cache(community_name, ctx.channel.id, None, True, True)
            await self.bot.conn.insert_weverse_channel(ctx.channel.id, community_name)
            await ctx.send(f"You are now following {community.name}.")

    @commands.command()
    async def media(self, ctx, *, community_name):
        """Toggle Media Status for a Community."""
        community_name = community_name.lower()
        if not self.check_community_exists(community_name):
            return await self.send_communities_available(ctx)

        text_channel = self.get_channel(community_name, ctx.channel.id)
        await self.bot.conn.toggle_media(ctx.channel.id, community_name, text_channel.media_enabled)
        text_channel.media_enabled = not text_channel.media_enabled
        return await ctx.send(f"You will now {'no longer' if not text_channel.media_enabled else ''} receive "
                              f"media posts for this community.")

    @commands.command()
    async def comments(self, ctx, *, community_name):
        """Toggle Comments Status for a Community."""
        community_name = community_name.lower()
        if not self.check_community_exists(community_name):
            return await self.send_communities_available(ctx)

        text_channel = self.get_channel(community_name, ctx.channel.id)
        await self.bot.conn.toggle_comments(ctx.channel.id, community_name, text_channel.comments_enabled)
        text_channel.comments_enabled = not text_channel.comments_enabled
        return await ctx.send(f"You will now {'no longer' if not text_channel.media_enabled else ''} receive "
                              f"comments posts for this community.")

    @commands.command()
    async def role(self, ctx, role: discord.Role, *, community_name: str):
        """Add a role to be notified when a community posts."""
        community_name = community_name.lower()
        if not self.check_community_exists(community_name):
            return await self.send_communities_available(ctx)

        text_channel = self.get_channel(community_name, ctx.channel.id)
        if text_channel.role_id and text_channel.role_id == role.id:
            text_channel.role_id = None
            await self.bot.conn.update_role(ctx.channel.id, community_name, None)
            return await ctx.send("This role will no longer be mentioned.")
        await self.bot.conn.update_role(ctx.channel.id, community_name, role.id)
        text_channel.role_id = role.id
        return await ctx.send("That role will now receive notifications.")

    @staticmethod
    def get_random_color():
        """Retrieves a random hex color."""
        r = lambda: randint(0, 255)
        return int(('%02X%02X%02X' % (r(), r(), r())), 16)  # must be specified to base 16 since 0x is not present

    async def create_embed(self, title="Weverse", color=None, title_desc=None,
                           footer_desc="Thanks for using WeverseBot!", icon_url=None, footer_url=None, title_url=None):
        """Create a discord Embed."""
        from discord.embeds import EmptyEmbed
        icon_url = icon_url
        footer_url = footer_url
        color = self.get_random_color() if not color else color

        embed = discord.Embed(title=title, color=color, description=title_desc or EmptyEmbed,
                              url=title_url or EmptyEmbed)

        embed.set_author(name="Weverse", url="https://www.patreon.com/mujykun?fan_landing=true",
                         icon_url=icon_url)
        embed.set_footer(text=footer_desc, icon_url=footer_url)
        return embed

    async def set_comment_embed(self, notification, embed_title):
        """Set Comment Embed for Weverse."""
        comment_body = await self.weverse_client.fetch_comment_body(notification.community_id,
                                                                    notification.contents_id)
        if not comment_body:
            artist_comments = await self.weverse_client.fetch_artist_comments(notification.community_id,
                                                                              notification.contents_id)
            if artist_comments:
                comment_body = (artist_comments[0]).body
            else:
                return
        translation = await self.weverse_client.translate(
            notification.contents_id, is_comment=True,
            community_id=notification.community_id) or await self.translate(comment_body)

        embed_description = f"**{notification.message}**\n\n" \
                            f"Content: **{comment_body}**\n" \
                            f"Translated Content: **{translation}**"

        embed = await self.create_embed(title=embed_title, title_desc=embed_description)
        return embed

    async def download_weverse_post(self, url, file_name):
        """Downloads an image url and returns image host url.

        If we are to upload from host, it will return the folder location instead (Unless the file is more than 8mb).


        :returns: (photos/videos)/image links and whether it is from the host.
        """
        from_host = False
        async with self._web_session.get(url) as resp:
            async with aiofiles.open(self._weverse_image_folder + file_name, mode='wb') as fd:
                data = await resp.read()
                await fd.write(data)
                print(f"{len(data)} - Length of Weverse File - {file_name}")
                if len(data) >= 8000000:  # 8 mb
                    return [f"https://images.irenebot.com/weverse/{file_name}", from_host]

        if self._upload_from_host:
            from_host = True
            return [f"{self._weverse_image_folder}{file_name}", from_host]
        return [f"https://images.irenebot.com/weverse/{file_name}", from_host]

    async def set_post_embed(self, notification, embed_title):
        """Set Post Embed for Weverse.

        :returns: Embed, file locations, and image urls.
        """
        post = self.weverse_client.get_post_by_id(notification.contents_id)
        if post:
            translation = await self.weverse_client.translate(
                post.id, is_post=True, p_obj=post,
                community_id=notification.community_id) or await self.translate(post.body)

            embed_description = f"**{notification.message}**\n\n" \
                                f"Artist: **{post.artist.name} ({post.artist.list_name[0]})**\n" \
                                f"Content: **{post.body}**\n" \
                                f"Translated Content: **{translation}**"
            embed = await self.create_embed(title=embed_title, title_desc=embed_description)

            # will either be file locations or image links.
            photos = [await self.download_weverse_post(photo.original_img_url, photo.file_name) for photo in
                      post.photos]

            videos = []
            for video in post.videos:
                start_loc = video.video_url.find("/video/") + 7
                if start_loc == -1:
                    file_name = f"{post.id}_{randint(1, 50000000)}.mp4"
                else:
                    file_name = video.video_url[start_loc: len(video.video_url)]
                videos.append(await self.download_weverse_post(video.video_url, file_name))

            media_files = []  # can be photos or videos
            file_urls = []  # urls of photos or videos
            for file in photos + videos:  # a list of lists containing the image
                media = file[0]
                from_host = file[1]

                if from_host:
                    # file locations
                    media_files.append(media)
                else:
                    file_urls.append(media)

            message = "\n".join(file_urls)
            return embed, media_files, message
        return None, None, None

    async def set_media_embed(self, notification, embed_title):
        """Set Media Embed for Weverse."""
        media = self.weverse_client.get_media_by_id(notification.contents_id)
        if media:
            embed_description = f"**{notification.message}**\n\n" \
                                f"Title: **{media.title}**\n" \
                                f"Content: **{media.body}**\n"
            embed = await self.create_embed(title=embed_title, title_desc=embed_description)
            message = media.video_link
            return embed, message
        return None, None

    async def send_weverse_to_channel(self, channel_info: TextChannel, message_text, embed, is_comment, is_media,
                                      community_name, media=None):
        """Send a weverse post to a channel."""
        if (is_comment and not channel_info.comments_enabled) or (is_media and not channel_info.media_enabled):
            return  # if the user has the post disabled, we should not post it.

        try:
            channel = self.bot.get_channel(channel_info.id)
            if not channel:
                # fetch channel instead (assuming discord.py cache did not load)
                channel = await self.bot.fetch_channel(channel_info.id)
        except:
            # remove the channel from future updates as it cannot be found.
            return await self.delete_channel(channel_info.id, community_name.lower())

        msg_list = []
        file_list = []

        try:
            mention_role = f"<@&{channel_info.role_id}>" if channel_info.role_id else None
            msg_list.append(await channel.send(mention_role, embed=embed))
            if message_text or media:
                # Since an embed already exists, any individual content will not load
                # as an embed -> Make it it's own message.
                if media:
                    # a list of file locations
                    for photo_location in media:
                        file_list.append(discord.File(photo_location))

                msg_list.append(await channel.send(message_text if message_text else None, files=file_list or None))
                print(f"Weverse Post for {community_name} sent to {channel_info.id}.")
        except discord.Forbidden as e:
            # no permission to post
            print(f"{e} (discord.Forbidden) - Weverse Post Failed to {channel_info.id} for {community_name}")

            # remove the channel from future updates as we do not want it to clog our rate-limits.
            return await self.delete_channel(channel_info.id, community_name.lower())
        except Exception as e:
            print(f"{e} (Exception) - Weverse Post Failed to {channel_info.id} for {community_name}")
            return

    async def send_notification(self, notification: models.Notification):
        """Manages a notification to be sent to a text channel."""
        is_comment = False
        is_media = False
        media = None
        community_name = notification.community_name or notification.bold_element

        if not community_name:
            return

        channels = self._channels.get(community_name.lower()).values()
        if not channels:
            print("WARNING: There were no channels to post the Weverse notification to.")
            return
        channels = channels.values()

        noti_type = self.weverse_client.determine_notification_type(notification.message)
        embed_title = f"New {community_name} Notification!"
        message_text = None
        if noti_type == 'comment':
            is_comment = True
            embed = await self.set_comment_embed(notification, embed_title)
        elif noti_type == 'post':
            is_media = True
            embed, media, message_text = await self.set_post_embed(notification, embed_title)
        elif noti_type == 'media':
            is_media = True
            embed, message_text = await self.set_media_embed(notification, embed_title)
        elif noti_type == 'announcement':
            return None  # not keeping track of announcements ATM
        else:
            return None

        if not embed:
            print(f"WARNING: Could not receive Weverse information for {community_name}. "
                  f"Noti ID:{notification.id} - "
                  f"Contents ID: {notification.contents_id} - "
                  f"Noti Type: {notification.contents_type}")
            return  # we do not want constant attempts to send a message.

        for channel_info in channels:
            channel_info: TextChannel = channel_info  # for typing
            await sleep(2)

            if notification.id in channel_info.already_posted:
                continue

            channel_info.already_posted.append(notification.id)

            await self.send_weverse_to_channel(channel_info, message_text, embed, is_comment, is_media, community_name,
                                               media=media)

    @tasks.loop(seconds=45, minutes=0, hours=0, reconnect=True)
    async def weverse_updates(self):
        if not self.weverse_client.cache_loaded:
            return

        if not await self.weverse_client.check_new_user_notifications():
            return

        user_notifications = self.weverse_client.user_notifications
        if not user_notifications:
            return

        new_notifications = self.weverse_client.get_new_notifications()

        for notification in new_notifications:
            await self.send_notification(notification)


def setup(bot: commands.AutoShardedBot):
    bot.add_cog(Weverse(bot))