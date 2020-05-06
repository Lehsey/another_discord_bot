import asyncio
import discord
from data import db_session
from data.get_video import Yutube_api
from discord.ext import commands
from data.Favorite import Favorite

TOKEN = '*'


class Charr(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.yt = Yutube_api()
        self.song_queue = {}

    @commands.command(name='help')
    async def help_info(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Help", description="Commands that you shall know", color=0x57189c)
        embed.add_field(name="common commands list:",
                        value="just type it", inline=False)
        embed.add_field(
            name="join", value="join to your voicechat", inline=True)
        embed.add_field(
            name="leave", value="disconnect from voicechat", inline=True)
        embed.add_field(
            name="play  <url>", value="add video\playlist to you player queue", inline=True)
        embed.add_field(
            name="stop", value="stop playing and clear queue", inline=True)
        embed.add_field(
            name="skip", value="skip song currently playing", inline=True)
        embed.add_field(name=" playlist subcommand",
                        value="(should start with playlist <subcommand>)", inline=False)
        embed.add_field(name="add <url>/now",
                        value="add song from url or currently playing to your playlist", inline=True)
        embed.add_field(
            name="play", value="add your playlist to your queue", inline=True)
        embed.add_field(name="del <url>/now/all",
                        value="delete song from your playlist from url/song playing now/delete whole playlist", inline=True)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = [[], asyncio.Event()]
        print('Bot is ready')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.song_queue[guild.id] = [[], asyncio.Event()]

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        print(type(error))
        print(error)
        if type(error) == discord.ext.commands.errors.CommandNotFound or error == 'wrong command':
            await ctx.send('unknowon command, type "!>help" for viewing all commands')
        elif error.args[0] == 'user not in voice channel':
            await ctx.send("I can't hear you")
        else:
            print("error:\n", error)
            await ctx.send('bot is curently broken, try to do it later')

    @commands.command(name='join')
    async def join_chan(self, ctx: commands.Context):
        channel = ctx.message.author.voice
        if not channel:
            return await ctx.send("I can't hear you")
        if ctx.voice_client:
            return await ctx.voice_client.move_to(channel.channel)
        await channel.channel.connect()

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        await ctx.voice_client.disconnect()

    @commands.command(name='play')
    async def add_music(self, ctx: commands.Context, url, from_playlist=False):
        async with ctx.typing():
            if from_playlist:
                player = [await self.yt.from_url(el, loop=self.bot.loop) for el in url]
            else:
                player = await self.yt.from_url(url, loop=self.bot.loop)
            if type(player) == list:
                self.song_queue[ctx.guild.id][0].extend(player)
                await ctx.send('Playlist has been added to queue')
            else:
                self.song_queue[ctx.guild.id][0].append(player)
                await ctx.send(f'Song *{player.title}* hase been added to queue')
        if not ctx.voice_client.is_playing():
            await self.play_next_song(ctx)

    @commands.group(name='playlist')
    async def playlist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self.on_command_error(ctx, 'wrong command')

    @playlist.command(name="play")
    async def _play_plalist(self, ctx: commands.context):
        session = db_session.create_session()
        data = session.query(Favorite).filter(
            Favorite.user == ctx.author.id).first()
        await self.add_music(ctx, data.videos.split(), from_playlist=True)

    @playlist.command(name='del')
    async def _del_music(self, ctx, command_url):
        user = ctx.author.id
        session = db_session.create_session()
        data = session.query(Favorite).filter(
            Favorite.user == user).first()
        if not data:
            await ctx.send('you dont have your playlist')
        else:
            if command_url == "now":
                if ctx.voice_client:
                    if ctx.voice_client.is_playing():
                        song_id = ctx.voice_client.source.data['id']
                        if song_id in data.videos.split():
                            data.videos = ' '.join(i for i in filter(
                                lambda x: x != song_id, data.videos.split()))
                            await ctx.send('song has been deleted')
                        else:
                            return await ctx.send('song not in your playlist')
                    else:
                        return await ctx.send('song must be playing to use this command')
                else:
                    return await ctx.send('song must be playing to use this command')
            elif command_url == "all":
                session.delete(data)
                await ctx.send('your playlist was destroyed')
            else:
                player = await self.yt.from_url(command_url, loop=self.bot.loop)
                if player.data['id'] in data.videos.split():
                    data.videos = ' '.join(i for i in filter(
                        lambda x: x != player.data['id'], data.videos.split()))
                    await ctx.send('song has been deleted')
                else:
                    return await ctx.send('song not in your playlist')
        session.commit()

    @playlist.command(name='add')
    async def _add_music(self, ctx: commands.Context, command_url):
        user = ctx.author.id
        session = db_session.create_session()
        data = session.query(Favorite).filter(
            Favorite.user == user).first()
        if command_url == 'now':
            if ctx.voice_client:
                if ctx.voice_client.is_playing():
                    song_id = ctx.voice_client.source.data['id']
                    if data:
                        if song_id in data.videos.split():
                            return await ctx.send('song already in your playlist')
                        else:
                            data.videos = data.videos + ' ' + song_id
                    else:
                        data = Favorite(user=user, videos=song_id)
                        session.add(data)
            else:
                return await ctx.send('song must be playing to use this command')
        else:
            player = await self.yt.from_url(command_url, loop=self.bot.loop)
            if data:
                if type(player) == list:
                    old_data = data.videos.split()
                    new_data = filter(
                        lambda x: x.data['id'] not in old_data, player)
                    new_data = ' '.join(el.data['id'] for el in new_data)
                    data.videos = data.videos + ' ' + new_data
                else:
                    if player.data['id'] in data.videos.split():
                        return await ctx.send('song already in your playlist')
                    else:
                        data.videos = data.videos + ' ' + player.data['id']
            else:
                if type(player) == list:
                    data = Favorite(user=user, videos=' '.join(
                        el.data['id'] for el in player))
                else:
                    data = Favorite(user=user, videos=player.data['id'])
        session.commit()
        await ctx.send('song(s) successfully added')

    async def play_next_song(self, ctx: commands.Context):
        while True:
            self.song_queue[ctx.guild.id][1].clear()
            if not self.song_queue[ctx.guild.id][0]:
                break
            player = self.song_queue[ctx.guild.id][0].pop(0)
            ctx.voice_client.play(player, after=lambda e: print(
                'Player error: %s' % e) if e else self.music_help(ctx))
            await asyncio.sleep(2)
            if ctx.voice_client.is_playing():
                embed = discord.Embed(
                    title="Now playing", url=player.data['webpage_url'], description=player.title, color=0x8402c1)
                embed.set_image(url=player.data['thumbnail'])
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Can't play *({player.title})*, try to add this song later")
                continue
            await self.song_queue[ctx.guild.id][1].wait()

    def music_help(self, ctx):
        self.bot.loop.call_soon_threadsafe(
            self.song_queue[ctx.guild.id][1].set)

    @_play_plalist.before_invoke
    @add_music.before_invoke
    async def voice_chek(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                raise commands.CommandError('user not in voice channel')

    @commands.command(name='stop')
    async def stop_play(self, ctx):
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                self.song_queue[ctx.guild.id][0].clear()

    @commands.command(name='skip')
    async def skip_music(self, ctx):
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()


if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!>')
    bot.remove_command('help')
    bot.add_cog(Charr(bot))
    db_session.global_init(f"db/favorite.sqlite")
    bot.run(TOKEN)
