import asyncio
import logging
import re
import sys
from os import getenv

from aiogram.client.session import aiohttp
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
YT_API_KEY = getenv("YT_API_KEY")
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

dp = Dispatcher()
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! 👋\n\n"
        "Я помогу тебе получить информацию о песнях с YouTube и Spotify. "
        "Просто отправь ссылку, и я обработаю её.\n\n"
        "Примеры:\n"
        "🔗 YouTube: https://youtu.be/example\n"
        "🔗 Spotify: https://open.spotify.com/track/example"
    )


@dp.message(lambda message: message.text)
async def link_handler(message: Message) -> None:
    yt_link = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    yt_link_desctop = r"(https?://)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    sp_link = r"(https?://)?(open\.)?spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)"

    links = re.findall(r"https?://\S+", message.text)

    for link in links:
        if re.match(yt_link, link):
            platform, track_id = await extract_platform_and_id(link)
            track_info = await get_track_details_yt(track_id)
            if track_info:
                await message.answer(
                    f"Platform: {platform}\nTrack info:\n"
                    f"Title: {track_info['title']}\n"
                    f"Description: {track_info['description']}\n"
                    f"Views: {track_info['views']}\n"
                    f"Duration: {track_info['duration']}\n"
                    f"Published on: {track_info['publication date']}"
                )
            else:
                await message.answer(
                    "Не удалось получить информацию о видео YouTube. Возможно, видео недоступно, "
                    "либо произошла ошибка при запросе к API."
                )
        elif re.match(yt_link_desctop, link):
            platform, track_id = await extract_platform_and_id(link)
            track_info = await get_track_details_yt(track_id)
            if track_info:
                await message.answer(
                    f"Platform: {platform}\nTrack info:\n"
                    f"Title: {track_info['title']}\n"
                    f"Description: {track_info['description']}\n"
                    f"Views: {track_info['views']}\n"
                    f"Duration: {track_info['duration']}\n"
                    f"Published on: {track_info['publication date']}"
                )
            else:
                await message.answer(
                    "Не удалось получить информацию о видео YouTube. Возможно, видео недоступно, "
                    "либо произошла ошибка при запросе к API."
                )
        elif re.match(sp_link, link):
            platform, track_id = await extract_platform_and_id(link)
            track_info = await get_track_details_sp(track_id)
            if track_info:
                await message.answer(
                    f"Platform: {platform}\nTrack info:\n"
                    f"Title: {track_info['title']}\n"
                    f"Description: {track_info['description']}\n"
                    f"Views: {track_info['views']}\n"
                    f"Duration: {track_info['duration']}\n"
                    f"Published on: {track_info['publication date']}"
                )
            else:
                await message.answer(
                    "Не удалось получить информацию о треке Spotify. Возможно, видео недоступно, "
                    "либо произошла ошибка при запросе к API."
                )
        else:
            await message.answer(f"Unknown link format: {link}")


async def extract_platform_and_id(link_url):
    youtube_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)([a-zA-Z0-9_-]{11})"
    yt_regex_desctop = r"(https?://)?(youtube|youtu|youtube-nocookie)\.(com|be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    spotify_regex = r"(https?://)?(open\.)?spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)"

    match_youtube = re.match(youtube_regex, link_url)
    match_youtube_desktop = re.match(yt_regex_desctop, link_url)
    match_spotify = re.match(spotify_regex, link_url)
    if match_youtube:
        return "youtube", match_youtube.group(5)
    elif match_youtube_desktop:
        return "youtube", match_youtube_desktop.group(4)
    elif match_spotify:
        return "spotify", match_spotify.group(4)
    else:
        return "unknown", None


async def get_track_details_yt(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={video_id}&key={YT_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("items"):
                    video_data = data["items"][0]
                    return {
                        "title": video_data["snippet"]["title"],
                        "description": video_data["snippet"]["description"],
                        "views": video_data["statistics"]["viewCount"],
                        "duration": video_data["contentDetails"]["duration"],
                        "publication date": video_data["snippet"]["publishedAt"],
                    }
                else:
                    logging.warning("Видео с указанным ID не найдено.")
                    return None
            else:
                logging.error(f"Ошибка при запросе данных: {response.status}")
                return None


async def get_track_details_sp(track_id):
    track_info = await asyncio.to_thread(sp.track, track_id)

    if track_info:
        return {
            "title": track_info["name"],
            "description": track_info["album"]["name"],
            "views": track_info["popularity"],
            "duration": track_info["duration_ms"],
            "publication date": track_info["album"]["release_date"],
        }
    else:
        logging.warning(f"Трек с указанным ID не найден.")
        return None


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
