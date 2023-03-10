import disnake
import asyncio
import config
from yt_dlp import YoutubeDL
from disnake.ext import commands


YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True,
                'simulate': True, 'key': 'FFmpegExtractAudio', 'forceduration': True}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

queue = []
temp_context = None
skip_flag = False
repeat_flag = False
playing_flag = False

categories_ids = {'Nazarick': '1012127570260668416',
                  'Testing': '1079060596667973642'}

vcs = {}
bot = commands.Bot(command_prefix="?", intents=disnake.Intents.all(
), activity=disnake.Game(name="/help"))

voice = None


@bot.event
async def on_ready():
    print("Bot is turned on")


@bot.event
async def on_voice_state_update(member, before: disnake.VoiceState, after: disnake.VoiceState):
    global categories_names
    member_nick = ((str)(member))[slice(0, -5)]
    possible_channel_name = f"{member_nick}'s private"
    if after.channel and after.channel.name == "Создать приват":
        guild = member.guild
        category = disnake.utils.get(
            guild.categories, name="Приваты")

        tmp_channel = await category.create_voice_channel(name=possible_channel_name)
        perms = tmp_channel.overwrites_for(member.guild.default_role)
        perms.view_channel = False
        await tmp_channel.set_permissions(member.guild.default_role, overwrite=perms)
        try:
            perms = tmp_channel.overwrites_for(member)
        except:
            pass
        await tmp_channel.edit(bitrate=384000)
        perms.view_channel = True
        perms.manage_permissions = True
        perms.manage_channels = True
        await tmp_channel.set_permissions(member, overwrite=perms)
        await member.move_to(tmp_channel)

    if before.channel:
        if before.channel.name == possible_channel_name:
            if len(before.channel.members) == 0:
                await before.channel.delete()


@bot.remove_command('help')
@bot.command()
async def help(ctx):
    await ctx.send("Тебе уже ничего не поможет")


# @bot.slash_command(description="Test slash-command")
# async def test(interaction: disnake.AppCmdInter, num: int):
#     await interaction.send(f"test {num}")


@bot.slash_command(description="Plays a song from youtube (paste URL or type a query)", aliases="p")
async def play(ctx, url: str):
    global voice, temp_context
    temp_context = ctx
    voice = disnake.utils.get(bot.voice_clients, guild=temp_context.guild)
    channel = temp_context.author.voice.channel
    if voice and vcs[voice.guild.id].channel and channel != vcs[voice.guild.id].channel:
        await temp_context.response.send_message("I'm already playing in another channel D:")
        return
    if channel:
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            if not voice and not voice.is_connected():
                return await temp_context.response.send_message('Seems like your channel is unavailable :c')

        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if "https://" in url:
                info = ytdl.extract_info(url, download=False)
            else:
                info = ytdl.extract_info(f"ytsearch:{url}", download=False)[
                    'entries'][0]
        title = info['title']
        queue.append(info)
        await temp_context.response.send_message(f"{title} was added to queue!")
        global playing_flag, skip_flag, repeat_flag
        vcs[voice.guild.id] = voice
        if not playing_flag:
            try:
                playing_flag = True
                while True:
                    if len(queue) == 0:
                        repeat_flag = False
                        playing_flag = False
                        skip_flag = False
                        await vcs[temp_context.guild.id].disconnect()
                        await temp_context.channel.send_message("Finished playing music!")
                        break

                    link = queue[0].get("url", None)
                    title = queue[0]['title']

                    vcs[temp_context.guild.id].play(disnake.FFmpegPCMAudio(
                        executable="E:\\Study\\discord\\bot_script\\ffmpeg\\ffmpeg.exe", source=link, **FFMPEG_OPTIONS))
                    await temp_context.channel.send(f"Now playing: {title}")
                    while ((voice.is_playing() or voice.is_paused()) and not skip_flag):
                        await asyncio.sleep(1)

                    if skip_flag:
                        vcs[temp_context.guild.id].stop()
                        skip_flag = False
                    if repeat_flag:
                        queue.insert(0, queue[0])
                    queue.pop(0)
            except:
                pass
    else:
        await temp_context.send(f"Please, connect a voice channel")


@bot.slash_command(description="Pauses current song")
async def pause(ctx: disnake.AppCmdInter):
    try:
        vcs[ctx.guild.id].pause()
        await ctx.send("Player paused!")
    except Exception as err:
        await ctx.send("I am not playing anything!")


@bot.slash_command(description="Resumes current song")
async def resume(ctx: disnake.AppCmdInter):
    try:
        vcs[ctx.guild.id].resume()
        await ctx.send("Player resumed!")
    except Exception as err:
        await ctx.send("There's nothing to play!")


@bot.slash_command(description="Repeats current song")
async def repeat(ctx: disnake.AppCmdInter):
    global repeat_flag, playing_flag
    if not playing_flag:
        await ctx.send("I am not playing anything!")
        return
    if repeat_flag:
        repeat_flag = False
        await ctx.send("Repeat mode is off!")
    else:
        repeat_flag = True
        await ctx.send("Repeat mode is on!")


@bot.slash_command(description="Clears queue and disconnects bot")
async def stop(ctx: disnake.AppCmdInter):
    try:
        global repeat_flag, playing_flag, skip_flag
        queue.clear()
        repeat_flag = False
        playing_flag = False
        skip_flag = False
        vcs[ctx.guild.id].stop()
        await vcs[ctx.guild.id].disconnect()
        await ctx.send("DJ decided to stop!")
    except Exception as err:
        await ctx.send("I am not playing anything!")


@bot.slash_command(description="Skips current song")
async def skip(ctx: disnake.AppCmdInter):
    global skip_flag
    if len(queue) > 0:
        skip_flag = True
        await ctx.send("Skipped current track!")
    else:
        await ctx.send("I am not playing anything!")


@bot.slash_command(description="Reviews list of commands")
async def help(ctx: disnake.AppCmdInter):
    await ctx.send(embed=disnake.Embed(color=0, description="Type /play to order a song (use URL from YT or just type the song's name)\nType /stop to stop playback\nType /pause to pause playback\nType /resume to resume playback\nType /repeat to repeat current track"))


# @bot.command()
# async def clear(ctx, amount: int):
#     await ctx.channel.purge(limit=amount+1)
#     await ctx.send(f"Deleted {amount} messages")

@bot.command(aliases=["p"])
async def play(ctx, url: str):
    global voice, temp_context
    temp_context = ctx
    voice = disnake.utils.get(bot.voice_clients, guild=temp_context.guild)
    channel = temp_context.author.voice.channel
    if voice and vcs[voice.guild.id].channel and channel != vcs[voice.guild.id].channel:
        await temp_context.send("I'm already playing in another channel D:")
        return
    if channel:
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            if not voice and not voice.is_connected():
                return await temp_context.send('Seems like your channel is unavailable :c')

        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if "https://" in url:
                info = ytdl.extract_info(url, download=False)
            else:
                info = ytdl.extract_info(f"ytsearch:{url}", download=False)[
                    'entries'][0]
        title = info['title']
        queue.append(info)
        await temp_context.send(f"{title} was added to queue!")
        global playing_flag, skip_flag, repeat_flag
        vcs[voice.guild.id] = voice
        if not playing_flag:
            try:
                playing_flag = True
                while True:
                    if len(queue) == 0:
                        repeat_flag = False
                        playing_flag = False
                        skip_flag = False
                        await vcs[temp_context.guild.id].disconnect()
                        await temp_context.channel.send_message("Finished playing music!")
                        break

                    link = queue[0].get("url", None)
                    title = queue[0]['title']

                    vcs[temp_context.guild.id].play(disnake.FFmpegPCMAudio(
                        executable="E:\\Study\\discord\\bot_script\\ffmpeg\\ffmpeg.exe", source=link, **FFMPEG_OPTIONS))
                    await temp_context.channel.send(f"Now playing: {title}")
                    while ((voice.is_playing() or voice.is_paused()) and not skip_flag):
                        await asyncio.sleep(1)

                    if skip_flag:
                        vcs[temp_context.guild.id].stop()
                        skip_flag = False
                    if repeat_flag:
                        queue.insert(0, queue[0])
                    queue.pop(0)
            except:
                pass
    else:
        await temp_context.send(f"Please, connect a voice channel")


@bot.command()
async def pause(ctx):
    try:
        vcs[ctx.guild.id].pause()
        await ctx.send("Player paused!")
    except Exception as error:
        print(error)
        await ctx.send("I am not playing anything!")


@bot.command()
async def resume(ctx):
    try:
        vcs[ctx.guild.id].resume()
        await ctx.send("Player resumed!")
    except Exception as error:
        print(error)
        await ctx.send("There's nothing to play!")


@bot.command()
async def stop(ctx):
    try:
        global repeat_flag, playing_flag, skip_flag
        queue.clear()
        repeat_flag = False
        playing_flag = False
        skip_flag = False
        vcs[ctx.guild.id].stop()
        await vcs[ctx.guild.id].disconnect()
        await ctx.send("DJ decided to stop!")
    except Exception as err:
        await ctx.send("I am not playing anything!")


@bot.command()
async def skip(ctx):
    global skip_flag
    if len(queue) > 0:
        skip_flag = True
        await ctx.send("Skipped current track!")
    else:
        await ctx.send("I am not playing anything!")

bot.run(config.token)
