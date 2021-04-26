from asyncio import sleep
from datetime import datetime, timedelta
from typing import Optional
from better_profanity import profanity

from discord import Embed, Member, NotFound, Object
from discord.utils import find
from discord.ext.commands import Cog, Greedy, Converter
from discord.ext.commands import CheckFailure, BadArgument
from discord.ext.commands import command, has_permissions, bot_has_permissions

profanity.load_censor_words_from_file("./data/profanity.txt")

class BannedUser(Converter):
	async def convert(self, ctx, arg):
		if ctx.guild.me.guild_permissions.ban_members:
			if arg.isdigit():
				try:
					return (await ctx.guild.fetch_ban(Object(id=int(arg)))).user
				except NotFound:
					raise BadArgument

		banned = [e.user for e in await ctx.guild.bans()]

		if banned:
			if (user := find(lambda u: str(u) == arg, banned)) is not None:
				return user
			else:
				raise BadArgument


class moderation(Cog):
	def __init__(self, bot):
		self.bot = bot

	async def kick_members(self, message, targets, reason):
		for target in targets:
			if (message.guild.me.top_role.position > target.top_role.position and not target.guild_permissions.administrator):
				await target.kick(reason = reason)

				embed = Embed(title = "Member kicked", colour = 0xDD2222, timestamp = datetime.utcnow())

				embed.set_thumbnail(url = target.avatar_url)
				fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False), ("Actioned by", message.author.display_name, False), ("Reason", reason, False)]

				for name, value, inline in fields:
					embed.add_field(name = name, value = value, inline = inline)

				await self.log_channel.send(embed = embed)
	
	async def ban_members(self, message, targets, reason):
		for target in targets:
			if (message.guild.me.top_role.position > target.top_role.position and not target.guild_permissions.administrator):
				await target.ban(reason = reason)

				embed = Embed(title = "Member banned", colour = 0xDD2222, timestamp = datetime.utcnow())

				embed.set_thumbnail(url = target.avatar_url)
				fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False), ("Actioned by", message.author.display_name, False), ("Reason", reason, False)]

				for name, value, inline in fields:
					embed.add_field(name = name, value = value, inline = inline)

				await self.log_channel.send(embed = embed)

	@command(name = "kick")
	@bot_has_permissions(kick_members = True)
	@has_permissions(kick_members = True)
	async def kick_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")
		else:
			await self.kick_members(ctx.message, targets, reason)
			await ctx.send("Action complete.")

	@kick_command.error
	async def kick_command_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("Insufficient permissions to perform that task.")

	@command(name = "ban")
	@bot_has_permissions(ban_members = True)
	@has_permissions(ban_members = True)
	async def ban_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")
		else:
			await self.ban_members(ctx.message, targets, reason)
			await ctx.send("Action complete.")

	@ban_command.error
	async def ban_command_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("Insufficient permissions to perform that task.")

	@command(name = "unban")
	@bot_has_permissions(ban_members = True)
	@has_permissions(ban_members = True)
	async def unban_command(self, ctx, targets: Greedy[BannedUser], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")
		else:
			for target in targets:
				await ctx.guild.unban(target, reason = reason)

				embed = Embed(title = "Member unbanned", colour = 0xDD2222, timestamp = datetime.utcnow())

				embed.set_thumbnail(url = target.avatar_url)
				fields = [("Member", target.name, False), ("Actioned by", ctx.author.display_name, False), ("Reason", reason, False)]

				for name, value, inline in fields:
					embed.add_field(name = name, value = value, inline = inline)

				await self.log_channel.send(embed = embed)

			await ctx.send("Action complete.")

	@command(name = "clear", aliases = ["purge"])
	@bot_has_permissions(manage_messages = True)
	@has_permissions(manage_messages = True)
	async def clear_messages(self, ctx, targets: Greedy[Member], limit: Optional[int] = 1):
		def _check(message):
			return not len(targets) or message.author in targets

		if 0 < limit <= 100:
			with ctx.channel.typing():
				await ctx.message.delete()
				deleted = await ctx.channel.purge(limit = limit, after = datetime.utcnow() - timedelta(days = 14), check = _check)

				await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)
		else:
			await ctx.send("The limit provided is not within acceptable bounds.")

	@command(name = "addprofanity", aliases = ["addswears", "addcurses"])
	@has_permissions(manage_guild = True)
	async def add_profanity(self, ctx, *words):
		with open("./data/profanity.txt", "a", encoding = "utf-8") as f:
			f.write("".join(f"{w}\n" for w in words))

		profanity.load_censor_words_from_file("./data/profanity.txt")
		await ctx.send("Action complete.")

	@command(name = "delprofanity", aliases = ["delswears", "delcurses"])
	@has_permissions(manage_guild = True)
	async def remove_profanity(self, ctx, *words):
		with open("./data/profanity.txt", "r", encoding="utf-8") as f:
			stored = [w.strip() for w in f.readlines()]

		with open("./data/profanity.txt", "w", encoding = "utf-8") as f:
			f.write("".join(f"{w}\n" for w in stored if w not in words))

		profanity.load_censor_words_from_file("./data/profanity.txt")
		await ctx.send("Action complete.")

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.log_channel = self.bot.get_channel(766625032234991647)
			self.bot.cogs_ready.ready_up("moderation")

	@Cog.listener()
	async def on_message(self, message):
		def _check(m):
			return (m.author == message.author
					and len(m.mentions)
					and (datetime.utcnow() - m.created_at).seconds < 60)

		if not message.author.bot:
			if len(list(filter(lambda m: _check(m), self.bot.cached_messages))) >= 3:
				await message.channel.send("Don't spam mentions!", delete_after = 10)
				unmutes = await self.mute_members(message, [message.author], 5, reason = "Mention spam")

				if len(unmutes):
					await sleep(5)
					await self.unmute_members(message.guild, [message.author])
			elif profanity.contains_profanity(message.content):
				await message.delete()
				await message.channel.send("You can't use that word here.", delete_after = 10)

def setup(bot):
	bot.add_cog(moderation(bot))
