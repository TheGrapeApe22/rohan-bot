import json
from utils.file_paths import ROOT

GIFS_DIR = ROOT / "assets" / "gifs"
OUTPUT_PATH = ROOT / "cogs" / "memes.py"

metadata = json.loads((ROOT / "data" / "gifs.json").read_text())
additional_keywords = metadata.get("keywords", {})

def get_keywords(command_name: str) -> str:
    keywords = command_name.replace("_", " ").split()
    
    for word in (additional_keywords.get(command_name) or "").split():
        if word not in keywords and word != "gif":
            keywords.append(word)

    return " ".join(keywords)

def generate() -> None:
    links = metadata.get("links", {})
    files = sorted(path for path in GIFS_DIR.iterdir() if path.is_file())

    commands = {}
    for path in files:
        commands[path.stem] = ("file", path.name)
    for command_name, link in links.items():
        commands[command_name] = ("link", link)

    lines = [
        "import discord",
        "from discord.ext import commands",
        "from utils.send import send",
        "class Memes(commands.Cog):",
        "    def __init__(self, bot: commands.Bot):",
        "        self.bot = bot",
        ""
    ]

    for command_name, (kind, value) in commands.items():
        lines.extend(
            [
                f'    @commands.hybrid_command(help="{get_keywords(command_name)}")',
                f"    async def {command_name}(self, ctx):",
            ]
        )
        if kind == "file":
            lines.append(f'        await send(ctx, file=discord.File("assets/gifs/{value}"))')
        else:
            lines.append(f"        await send(ctx, {value!r})")
        lines.append("")

    lines.extend(
        [
            "async def setup(bot: commands.Bot):",
            "    await bot.add_cog(Memes(bot))",
            "",
        ]
    )
    OUTPUT_PATH.write_text("\n".join(lines))

if __name__ == "__main__":
    generate()
