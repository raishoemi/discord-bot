from dataclasses import dataclass
import json
from typing import Callable, Dict, List
import asyncio
import os
import random
import logging
import sys
import time
import discord
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
SERVER_NAME = 'הסלון'
# SERVER_NAME = 'bot test'
CHANNELS = ['General']
RANDOM_MEDIA_VOICELINES_PATH = 'P:/Projects/discord-bot/media/random_voicelines'
LEAGUE_MEDIA_VOICELINES_PATH = 'P:/Projects/discord-bot/media/lol_voicelines'
YARON_MEDIA_VOICELINES_PATH = 'P:/Projects/discord-bot/media/yaron'
FARTS_PATH = 'P:/Projects/discord-bot/media/farts'
RANDOM_MEDIA_VOICELINES_RANDOM_OFFSET = range(-300, 300)
RANDOM_MEDIA_VOICELINES_SLEEP_TIME_SECONDS = 6000 * 2  # 60 * 60
LOL_VOICE_QUIZ_MAX_GUESSES = 2
GENERAL_VOICE_CHANNEL_ID = '782317681973264419'
# GENERAL_VOICE_CHANNEL_ID = '947596574031220740' # BOT TEST


@dataclass
class VoiceQuiz():
    voiceline_path: str
    correct_answer: str
    answers: Dict[str, List[str]]


class MyClient(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.voice_quiz: VoiceQuiz = None
        self.yaron_entered_today = False
        self.yaron_user_id = '117352629121712134'
        self.edan_entered_today = False
        self.edan_user_id = '366252229822251009'
        self.shai_user_ud = '116912999242924038'

    def get_voice_channel(self) -> discord.VoiceChannel:
        for channel in self.get_all_channels():
            if channel.guild.name == SERVER_NAME and channel.name == 'General' and channel.type == discord.ChannelType.voice:
                return channel
        logging.error('Voice channel not found')
        raise ValueError()

    async def play_audio(self, voice_channel: discord.VoiceChannel, audio_path: str, after: Callable[[], None] = None):
        voice_client: discord.VoiceClient = await voice_channel.connect()

        def after_callback(e):
            self.loop.create_task(voice_client.disconnect())
            if after:
                after()
        voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            executable='P:/Programs/ffmpeg/ffmpeg-4.4.1-essentials_build/bin/ffmpeg.exe',
            source=audio_path.encode('utf-8')
        ), volume=0.1), after=after_callback)
        logging.info(f'Playing {audio_path}')

    async def on_ready(self):
        voice_channel = self.get_voice_channel()
        while True:
            try:
                sleep_random_offset = random.choice(
                    RANDOM_MEDIA_VOICELINES_RANDOM_OFFSET)
                await asyncio.sleep(RANDOM_MEDIA_VOICELINES_SLEEP_TIME_SECONDS + sleep_random_offset)
                random_file = f"{RANDOM_MEDIA_VOICELINES_PATH}/{random.choice([x for x in os.listdir(RANDOM_MEDIA_VOICELINES_PATH)])}"
                await self.play_audio(voice_channel, random_file)
            except Exception as e:
                pass

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        if message.guild.name == SERVER_NAME:
            if message.channel.name == 'top' and message.content == '!lol':
                if self.voice_quiz:
                    await message.channel.send('LOL voice challenge already in progress')
                    return
                channel: discord.TextChannel = message.channel
                message = await channel.send(f'You each have {LOL_VOICE_QUIZ_MAX_GUESSES} attempts to guess the champion\'s name! (!giveup, !replay)')
                random_voiceline = f"{LEAGUE_MEDIA_VOICELINES_PATH}/{random.choice([x for x in os.listdir(LEAGUE_MEDIA_VOICELINES_PATH)])}"
                correct_answer = random_voiceline.split("/")[-1].split("_")[0]
                self.voice_quiz = VoiceQuiz(
                    voiceline_path=random_voiceline, correct_answer=correct_answer, answers={})
                voice_channel = self.get_voice_channel()
                await self.play_audio(voice_channel, self.voice_quiz.voiceline_path)
                logging.info(
                    f'Started voice quiz with voiceline: {self.voice_quiz.voiceline_path}')
            elif self.voice_quiz and message.channel.name == 'top':
                author = message.author
                guess = message.content
                if guess == '!replay':
                    voice_channel = self.get_voice_channel()
                    await self.play_audio(
                        voice_channel, self.voice_quiz.voiceline_path)
                elif guess == '!giveup':
                    await message.channel.send(
                        f'The correct answer was {self.voice_quiz.correct_answer}')
                    self.voice_quiz = None
                elif author in self.voice_quiz.answers and len(self.voice_quiz.answers[author]) >= LOL_VOICE_QUIZ_MAX_GUESSES:
                    await message.channel.send(f'{author.mention} you already answered {LOL_VOICE_QUIZ_MAX_GUESSES} times, don\'t spoil the game for others!')
                elif guess.lower() == self.voice_quiz.correct_answer.lower():
                    await message.channel.send(f'{author.mention} You are correct!')
                    self.voice_quiz = None
                else:
                    if author in self.voice_quiz.answers:
                        self.voice_quiz.answers[author].append(guess)
                    else:
                        self.voice_quiz.answers[author] = [guess]

    async def on_socket_raw_receive(self, msg: str):
        try:
            event = json.loads(msg)
            current_hour = time.localtime()[3]
            if self.yaron_entered_today and (current_hour <= 14 and current_hour >= 3):
                self.yaron_entered_today = False
            if self.edan_entered_today and (current_hour <= 14 and current_hour >= 3):
                self.edan_entered_today = False
            if 't' not in event or event['t'] != 'VOICE_STATE_UPDATE':
                return
            if 'd' not in event or 'channel_id' not in event['d'] or event['d']['channel_id'] == None or 'member' not in event['d'] or 'user' not in event['d']['member']:
                return
            if not event['d']['channel_id'] == GENERAL_VOICE_CHANNEL_ID:
                return
            entered_user_id = event['d']['member']['user']['id']
            if entered_user_id == self.yaron_user_id:
                if len(self.get_voice_channel().members) < 1:
                    return
                if (current_hour <= 14 and current_hour >= 3):
                    return
                if not self.yaron_entered_today:
                    self.yaron_entered_today = True
                    await asyncio.sleep(3)
                    await self.play_audio(self.get_voice_channel(), f'{YARON_MEDIA_VOICELINES_PATH}/homo.mp3')

            elif entered_user_id == self.edan_user_id:
                if len(self.get_voice_channel().members) < 1:
                    return
                if (current_hour <= 14 and current_hour >= 3):
                    return
                if not self.edan_entered_today:
                    self.edan_entered_today = True
                    await asyncio.sleep(3)
                    random_fart = f"{FARTS_PATH}/{random.choice([x for x in os.listdir(FARTS_PATH)])}"
                    await self.play_audio(self.get_voice_channel(), random_fart)
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
    api_key = os.environ.get('API_KEY')
    client.run(api_key)


# https://discordapp.com/oauth2/authorize?client_id=907702415648751648&scope=bot
if __name__ == '__main__':
    main()
