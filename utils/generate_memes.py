import json
from utils import file_paths as paths

metadata = json.loads(paths.GIF_METADATA.read_text())
additional_keywords = metadata.get("keywords", {})

def get_keywords(command_name: str) -> str:
    keywords = command_name.replace("_", " ").split()
    
    for word in (additional_keywords.get(command_name) or "").split():
        if word not in keywords and word != "gif":
            keywords.append(word)

    return " ".join(keywords)

def generate() -> None:
    links = metadata.get("links", {})
    files = sorted(path for path in paths.GIFS.iterdir() if path.is_file())

    commands = {}
    for path in files:
        commands[path.stem] = ("file", path.name)
    for command_name, link in links.items():
        commands[command_name] = ("link", link)

    lines = [
        "import discord",
        "from discord.ext import commands",
        "from utils.send import send",
        "from utils import file_paths as paths",
        "from utils.perms import enforce_whitelist",
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
        if command_name in metadata.get("private", []):
            lines.append(f"        await enforce_whitelist(ctx)")
        if kind == "file":
            lines.append(f'        await send(ctx, file=discord.File(paths.GIFS / {value!r}))')
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
    paths.MEMES_COG.write_text("\n".join(lines))

if __name__ == "__main__":
    generate()
