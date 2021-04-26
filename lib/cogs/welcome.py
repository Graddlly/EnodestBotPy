from discord import Forbidden
from discord.ext.commands import Cog
from discord.ext.commands import command

class welcome(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("welcome")

	@Cog.listener()
	async def on_member_join(self, member):
		await self.bot.get_channel(766615873087602709).send(f"Welcome to **{member.guild.name}** {member.mention}! Head over to <#766615872478773279> to say hi!")

		try:
			await member.send(f"Welcome to **{member.guild.name}**! Enjoy your stay!")

		except Forbidden:
			pass

		await member.add_roles(member.guild.get_role(766616208337534996))

	@Cog.listener()
	async def on_member_remove(self, member):
		await self.bot.get_channel(766615873087602709).send(f"{member.display_name} has left {member.guild.name}.")


def setup(bot):
	bot.add_cog(welcome(bot))