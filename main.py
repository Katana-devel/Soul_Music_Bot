import asyncio
import logging
import re
import sys
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

# Bot token can be obtained via https://t.me/BotFather
load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! \n\n  Sosal? \n\n Ponyal")


@dp.message(lambda message: message.text)
async def link_handler(message: Message) -> None:
    yt_link = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    sp_link = r'(https?://)?(open\.)?spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'

    # Ищем все ссылки в сообщении
    links = re.findall(r'https?://\S+', message.text)

    for link in links:
        if re.match(yt_link, link):
            platform, track_id = await extract_platform_and_id(link)
            await message.answer(f"Platform: {platform}\nTrack ID: {track_id}")
        elif re.match(sp_link, link):
            platform, track_id = await extract_platform_and_id(link)
            await message.answer(f"Platform: {platform}\nTrack ID: {track_id}")
        else:
            await message.answer(f"Unknown link format: {link}")


# @dp.message()
# async def echo_handler(message: Message) -> None:
#     """
#     Handler will forward receive a message back to the sender
#
#     By default, message handler will handle all message types (like a text, photo, sticker etc.)
#     """
#     try:
#         # Send a copy of the received message
#         await message.send_copy(chat_id=message.chat.id)
#     except TypeError:
#         # But not all the types is supported to be copied so need to handle it
#         await message.answer("Шо ты скинул? сломал(а) все, блин")


async def extract_platform_and_id(link_url):
    # Регулярные выражения
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)([a-zA-Z0-9_-]{11})'
    spotify_regex = r'(https?://)?(open\.)?spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'

    print(f"Checking URL: {link_url}")

    # Проверяем, является ли это YouTube ссылкой
    match_youtube = re.match(youtube_regex, link_url)
    match_spotify = re.match(spotify_regex, link_url)
    if match_youtube:
        return "youtube", match_youtube.group(5)  # Возвращаем платформу и ID для YouTube
    elif match_spotify:
        return "spotify", match_spotify.group(4)  # Возвращаем платформу и ID для Spotify
    else:
        raise ValueError("Bot works only with Spotify and YouTube links or invalid link format")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


# async def main():
#     link = r"https://open.spotify.com/playlist/6hBCqHpgVP6wWBvB2IavKe"
#     platform, track_id = await extract_platform_and_id(link)
#
#     print(platform)
#     print(track_id)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
