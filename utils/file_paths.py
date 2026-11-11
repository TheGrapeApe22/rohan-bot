from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENV = ROOT / ".env"
COGS = ROOT / "cogs"
DATA = ROOT / "data"
LOGS = ROOT / "logs"
ASSETS = ROOT / "assets"
TRACEBACKS = DATA / "tracebacks"
GIFS = ASSETS / "gifs"
ABG = ASSETS / "abg"
SOLILOQUY = ASSETS / "soliloquy"
SOLILOQUY_ATTACHMENTS = SOLILOQUY / "attachments"

DISCORD_LOG = DATA / "discord.log"
CARDS = DATA / "cards.json"
ARTICLE_TEMPLATES = DATA / "article_templates.json"
GIF_METADATA = DATA / "gifs.json"
IGNORE_CHANNELS = DATA / "ignore_channels.txt"
WHITELIST_USERS = DATA / "whitelist_users.txt"
NIRANJAN_LINES = DATA / "niranjan_lines.txt"
DAVID_LINES_DATABASE = DATA / "david_lines.sqlite3"
SENTENCES = SOLILOQUY / "sentences.txt"
NOUNS = SOLILOQUY / "nouns.txt"
MEMES_COG = COGS / "memes.py"