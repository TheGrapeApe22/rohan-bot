from dotenv import load_dotenv
import os
from utils.send import send

load_dotenv()
MY_ID = os.getenv("MY_ID")

def get_whitelist_users():
    with open('data/whitelist_users.txt', "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [int(line.strip()) for line in lines if line.strip() and not line.startswith("#")]

async def enforce_whitelist(ctx, user_id):
    if user_id not in get_whitelist_users():
        await send(ctx, f"You do not have permission to use this command. Feel free to DM <@{MY_ID}> for access.")
        raise PermissionError("User is not on the whitelist.")
