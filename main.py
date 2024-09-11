from dataclasses import dataclass
import json
from typing import Callable, Dict, List, Optional
import asyncio
import os
import random
import logging
import sys
import time
import discord
from dotenv import load_dotenv
from threading import Timer
from pydub import AudioSegment
import subprocess
import re


load_dotenv()

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
SERVER_NAME = "הסלון"
# SERVER_NAME = 'bot test'
VOICE_CHANNEL_NAME = "לאומנות"
RANDOM_MEDIA_VOICELINES_PATH = "P:/Projects/discord-bot/media/random_voicelines"
LEAGUE_MEDIA_VOICELINES_PATH = "P:/Projects/discord-bot/media/lol_voicelines"
SUNO_MEDIA_VOICELINES_PATH = "P:/Projects/discord-bot/media/suno_songs"
YARON_MEDIA_VOICELINES_PATH = "P:/Projects/discord-bot/media/yaron"
GUY_MEDIA_VOICELINES_PATH = "P:/Projects/discord-bot/media/guy"
FARTS_PATH = "P:/Projects/discord-bot/media/farts"
RANDOM_MEDIA_VOICELINES_RANDOM_OFFSET = range(-300, 300)
RANDOM_MEDIA_VOICELINES_SLEEP_TIME_SECONDS = 6000 * 2  # 60 * 60
LOL_VOICE_QUIZ_MAX_GUESSES = 2
GENERAL_VOICE_CHANNEL_ID = "782317681973264419"
# GENERAL_VOICE_CHANNEL_ID = '947596574031220740' # BOT TEST


@dataclass
class VoiceQuiz:
    voiceline_path: str
    correct_answer: str
    answers: Dict[str, List[str]]


@dataclass
class RandomSongQuiz:
    song_path: str
    song_name: str
    start_time: int
    start_duration: int
    hints: int


class MyClient(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.voice_quiz: VoiceQuiz = None
        self.suno_quiz: RandomSongQuiz = None
        self.yaron_entered_today = False
        self.edan_entered_today = False
        self.guy_entered_today = False
        self.yaron_user_id = "117352629121712134"
        self.edan_user_id = "366252229822251009"
        self.shai_user_ud = "116912999242924038"
        self.guy_user_id = "98354630139863040"

    def get_voice_channel(self) -> discord.VoiceChannel:
        for channel in self.get_all_channels():
            if (
                channel.guild.name == SERVER_NAME
                and channel.name == VOICE_CHANNEL_NAME
                and channel.type == discord.ChannelType.voice
            ):
                return channel
        logging.error("Voice channel not found")
        raise ValueError()

    async def play_audio(
        self,
        voice_channel: discord.VoiceChannel,
        audio_path: str,
        after: Callable[[], None] = None,
        start_at: int = 0,
        duration: Optional[int] = None,
    ):
        voice_client: discord.VoiceClient = await voice_channel.connect()

        def after_callback(e):
            self.loop.create_task(voice_client.disconnect())
            if after:
                after()

        if not duration:
            duration = 10000000
        if start_at < 0:
            start_at = 0
        voice_client.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    executable="P:/Programs/ffmpeg/ffmpeg-4.4.1-essentials_build/bin/ffmpeg.exe",
                    source=audio_path.encode("utf-8"),
                    before_options=f"-ss {start_at} -t {duration}",
                ),
                volume=0.1,
            ),
            after=after_callback,
        )
        logging.info(f"Playing {audio_path}")

    async def on_ready(self):
        voice_channel = self.get_voice_channel()
        while True:
            try:
                sleep_random_offset = random.choice(
                    RANDOM_MEDIA_VOICELINES_RANDOM_OFFSET
                )
                await asyncio.sleep(
                    RANDOM_MEDIA_VOICELINES_SLEEP_TIME_SECONDS + sleep_random_offset
                )
                random_file = f"{RANDOM_MEDIA_VOICELINES_PATH}/{random.choice([x for x in os.listdir(RANDOM_MEDIA_VOICELINES_PATH)])}"
                await self.play_audio(voice_channel, random_file)
            except Exception as e:
                pass

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        if message.guild.name == SERVER_NAME:
            if message.content.startswith("!timer"):
                if len(message.content.split(" ")) == 2:
                    timer_seconds = message.content.split(" ")[1]
                    if timer_seconds.isdigit():
                        await message.channel.send(
                            f"{message.author.display_name} your {timer_seconds} seconds timer is starting!"
                        )
                        await asyncio.sleep(int(timer_seconds))
                        await message.channel.send(
                            f"{message.author.display_name} your {timer_seconds} seconds timer is up!"
                        )
            if message.channel.name == "top" and message.content == "!zdayen":
                voice_channel = self.get_voice_channel()
                voice_client = discord.utils.get(self.voice_clients, guild=voice_channel.guild)
                if voice_client:
                    self.loop.create_task(voice_client.disconnect())

            if message.channel.name == "top" and message.content == "!lol":
                if self.voice_quiz:
                    await message.channel.send(
                        "LOL voice challenge already in progress"
                    )
                    return
                channel: discord.TextChannel = message.channel
                message = await channel.send(
                    f"You each have {LOL_VOICE_QUIZ_MAX_GUESSES} attempts to guess the champion's name! (!giveup, !replay)"
                )
                random_voiceline = f"{LEAGUE_MEDIA_VOICELINES_PATH}/{random.choice([x for x in os.listdir(LEAGUE_MEDIA_VOICELINES_PATH)])}"
                correct_answer = random_voiceline.split("/")[-1].split("_")[0]
                self.voice_quiz = VoiceQuiz(
                    voiceline_path=random_voiceline,
                    correct_answer=correct_answer,
                    answers={},
                )
                voice_channel = self.get_voice_channel()
                await self.play_audio(voice_channel, self.voice_quiz.voiceline_path)
                logging.info(
                    f"Started voice quiz with voiceline: {self.voice_quiz.voiceline_path}"
                )
            elif self.voice_quiz and message.channel.name == "top":
                author = message.author
                guess = message.content
                if guess == "!replay":
                    voice_channel = self.get_voice_channel()
                    await self.play_audio(voice_channel, self.voice_quiz.voiceline_path)
                elif guess == "!giveup":
                    await message.channel.send(
                        f"The correct answer was {self.voice_quiz.correct_answer}"
                    )
                    self.voice_quiz = None
                elif (
                    author in self.voice_quiz.answers
                    and len(self.voice_quiz.answers[author])
                    >= LOL_VOICE_QUIZ_MAX_GUESSES
                ):
                    await message.channel.send(
                        f"{author.mention} you already answered {LOL_VOICE_QUIZ_MAX_GUESSES} times, don't spoil the game for others!"
                    )
                elif guess.lower() == self.voice_quiz.correct_answer.lower():
                    await message.channel.send(f"{author.mention} You are correct!")
                    self.voice_quiz = None
                else:
                    if author in self.voice_quiz.answers:
                        self.voice_quiz.answers[author].append(guess)
                    else:
                        self.voice_quiz.answers[author] = [guess]

            elif message.content == "!randomsong" and message.channel.name == "top":
                random_suno_song = f"{SUNO_MEDIA_VOICELINES_PATH}/{random.choice([x for x in os.listdir(SUNO_MEDIA_VOICELINES_PATH)])}"
                voice_channel = self.get_voice_channel()
                await self.play_audio(voice_channel, random_suno_song)

            elif message.channel.name == "top" and message.content == "!sunoquiz":
                if self.suno_quiz:
                    await message.channel.send("Suno voice quiz already in progress")
                    return
                song_name = random.choice(
                    [x for x in os.listdir(SUNO_MEDIA_VOICELINES_PATH)]
                )
                random_suno_song = f"{SUNO_MEDIA_VOICELINES_PATH}/{song_name}"
                audio_length = AudioSegment.from_file(random_suno_song).duration_seconds
                random_starting_time = random.randint(10, int(audio_length) - 10)
                self.suno_quiz = RandomSongQuiz(
                    song_path=random_suno_song,
                    start_time=random_starting_time,
                    start_duration=2,
                    song_name=song_name,
                    hints=0
                )
                channel: discord.TextChannel = message.channel
                voice_channel = self.get_voice_channel()
                await self.play_audio(
                    voice_channel,
                    self.suno_quiz.song_path,
                    start_at=self.suno_quiz.start_time,
                    duration=self.suno_quiz.start_duration,
                )
                logging.info(
                    f"Started suno voice quiz with voiceline: {self.suno_quiz.song_path}. The commands are: !skip, !replay, !giveup"
                )
            elif self.suno_quiz and message.channel.name == "top":
                voice_channel = self.get_voice_channel()
                if message.content == "!replay":
                    await self.play_audio(
                        voice_channel,
                        self.suno_quiz.song_path,
                        start_at=self.suno_quiz.start_time,
                        duration=self.suno_quiz.start_duration,
                    )
                elif message.content == "!skip":
                    self.suno_quiz.start_duration += 1
                    self.suno_quiz.start_time -= 1
                    self.suno_quiz.hints += 1
                    await self.play_audio(voice_channel, self.suno_quiz.song_path, start_at=self.suno_quiz.start_time, duration=self.suno_quiz.start_duration)
                elif message.content == "!giveup":
                    await message.channel.send(
                        f"The correct answer was {self.suno_quiz.song_name}. You used {self.suno_quiz.hints} hints"
                    )
                    await self.play_audio(voice_channel, self.suno_quiz.song_path)
                    self.suno_quiz = None

    async def on_socket_raw_receive(self, msg: str):
        try:
            event = json.loads(msg)
            current_hour = time.localtime()[3]
            if self.yaron_entered_today and (current_hour <= 14 and current_hour >= 3):
                self.yaron_entered_today = False
            if self.edan_entered_today and (current_hour <= 14 and current_hour >= 3):
                self.edan_entered_today = False
            if self.guy_entered_today and (current_hour <= 14 and current_hour >= 3):
                self.guy_entered_today = False
            if "t" not in event or event["t"] != "VOICE_STATE_UPDATE":
                return
            if (
                "d" not in event
                or "channel_id" not in event["d"]
                or event["d"]["channel_id"] == None
                or "member" not in event["d"]
                or "user" not in event["d"]["member"]
            ):
                return
            if not event["d"]["channel_id"] == GENERAL_VOICE_CHANNEL_ID:
                return
            entered_user_id = event["d"]["member"]["user"]["id"]
            if entered_user_id == self.yaron_user_id:
                if len(self.get_voice_channel().members) < 1:
                    return
                if current_hour <= 14 and current_hour >= 3:
                    return
                if not self.yaron_entered_today:
                    self.yaron_entered_today = True
                    await asyncio.sleep(3)
                    await self.play_audio(
                        self.get_voice_channel(),
                        f"{YARON_MEDIA_VOICELINES_PATH}/homo.mp3",
                    )

            elif entered_user_id == self.edan_user_id:
                if len(self.get_voice_channel().members) < 1:
                    return
                if current_hour <= 14 and current_hour >= 3:
                    return
                if not self.edan_entered_today:
                    self.edan_entered_today = True
                    await asyncio.sleep(3)
                    random_fart = f"{FARTS_PATH}/{random.choice([x for x in os.listdir(FARTS_PATH)])}"
                    await self.play_audio(self.get_voice_channel(), random_fart)
            elif entered_user_id == self.guy_user_id:
                if len(self.get_voice_channel().members) < 1:
                    return
                if current_hour <= 14 and current_hour >= 3:
                    return
                if not self.guy_entered_today:
                    self.guy_entered_today = True
                    await asyncio.sleep(3)
                    await self.play_audio(
                        self.get_voice_channel(),
                        f"{GUY_MEDIA_VOICELINES_PATH}/not_guy_gay.mp3",
                    )
        except:
            pass


def main():
    intents = discord.Intents()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    intents.members = True
    intents.voice_states = True
    client = MyClient(intents=intents, enable_debug_events=True)
    api_key = os.environ.get('DISCORD_TOKEN')
    client.run(api_key)


# https://discordapp.com/oauth2/authorize?client_id=907702415648751648&scope=bot
if __name__ == "__main__":
    main()
