from dotenv import load_dotenv
import os
from utils.send import send
from utils import file_paths as paths

load_dotenv(paths.ENV)
MY_ID = os.getenv("MY_ID")

def get_whitelist_users():
    with paths.WHITELIST_USERS.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return [int(line.strip()) for line in lines if line.strip() and not line.startswith("#")]

async def enforce_whitelist(ctx):
    if ctx.author.id not in get_whitelist_users():
        await send(ctx, f"You do not have permission to use this command. Feel free to DM <@{MY_ID}> to ask for access.")
        raise PermissionError("User is not on the whitelist.")
