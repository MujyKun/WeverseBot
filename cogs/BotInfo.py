from discord.ext import commands


class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["patron"])
    async def patreon(self, ctx):
        """Sends link to become a patron."""
        return await ctx.send("https://www.patreon.com/mujykun?fan_landing=true")

    @commands.command()
    async def invite(self, ctx):
        """Sends an invite to the bot."""
        return await ctx.send("https://discord.com/oauth2/authorize?client_id=864670527187451914&scope=bot&permission"
                              "s=2952997936")

    @commands.command()
    async def support(self, ctx):
        """Sends an invite to the support server."""
        return await ctx.send("https://discord.gg/bEXm85V")

    @commands.command()
    async def ping(self, ctx):
        """Sends Ping."""
        return await ctx.send(f"{int(self.bot.latency * 1000)}ms")

    @commands.command()
    async def servercount(self, ctx):
        """View amount of servers connected to bot."""
        await ctx.send(f"I am connected to {len(self.bot.guilds)} servers.")


def setup(bot: commands.AutoShardedBot):
    bot.add_cog(BotInfo(bot))
