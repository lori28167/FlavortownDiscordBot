import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
from dotenv import load_dotenv
from flavortown_api import FlavorTownAPI

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FLAVORTOWN_API_KEY = os.getenv("FLAVORTOWN_API_KEY")

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Initialize API client
api = FlavorTownAPI(FLAVORTOWN_API_KEY)

# Auto-delete settings
AUTO_DELETE_TIMEOUT = 60  # 5 minutes in seconds

def format_price_with_hours(biscuits):
    """Format price showing both biscuits and equivalent hours (1h = 10 biscuits)"""
    if biscuits is None or biscuits == 'N/A':
        return 'N/A'
    
    hours = biscuits / 10
    if hours == int(hours):
        # Whole number of hours
        return f"{biscuits} biscuits ({int(hours)}h)"
    else:
        # Decimal hours, show with 1 decimal place
        return f"{biscuits} biscuits ({hours:.1f}h)"

async def send_and_schedule_delete(interaction: discord.Interaction, content=None, *, embed=None, view=None, ephemeral=False):
    """Send a message and schedule it for auto-deletion if not ephemeral"""
    if ephemeral:
        # Ephemeral messages disappear on their own
        return await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=True)
    
    # Send the message
    if hasattr(interaction, 'response') and not interaction.response.is_done():
        # Use response.send_message for initial responses
        message = await interaction.response.send_message(content=content, embed=embed, view=view)
    else:
        # Use followup.send for follow-up messages
        message = await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=False)
    
    # Schedule auto-deletion
    if message:
        asyncio.create_task(delete_message_after_delay(message, AUTO_DELETE_TIMEOUT))
    
    return message


async def delete_message_after_delay(message: discord.Message, delay: int):
    """Delete a message after the specified delay"""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except discord.NotFound:
        # Message was already deleted
        pass
    except discord.Forbidden:
        # Bot doesn't have permission to delete the message
        pass
    except Exception as e:
        print(f"Error deleting message: {e}")


# Custom button views
class PaginationView(ui.View):
    # Navigation buttons for paginated results
    def __init__(self, current_page: int, total_pages: int, callback):
        super().__init__(timeout=180)
        self.current_page = current_page
        self.total_pages = total_pages
        self.callback = callback
        
        if current_page > 1:
            self.first_page.disabled = False
            self.prev_page.disabled = False
        else:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        
        if current_page < total_pages:
            self.next_page.disabled = False
            self.last_page.disabled = False
        else:
            self.next_page.disabled = True
            self.last_page.disabled = True

    @ui.button(label="⏮️ First", style=discord.ButtonStyle.blurple)
    async def first_page(self, interaction: discord.Interaction, button: ui.Button):
        # Go to first page
        await self.callback(interaction, 1)

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.blurple)
    async def prev_page(self, interaction: discord.Interaction, button: ui.Button):
        # Go to previous page
        await self.callback(interaction, self.current_page - 1)

    @ui.button(label="Next ▶️", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        # Go to next page
        await self.callback(interaction, self.current_page + 1)

    @ui.button(label="Last ⏭️", style=discord.ButtonStyle.blurple)
    async def last_page(self, interaction: discord.Interaction, button: ui.Button):
        # Go to last page
        await self.callback(interaction, self.total_pages)


class ProjectView(ui.View):
    # Action buttons for project details
    def __init__(self, project):
        super().__init__(timeout=180)
        self.project = project
        
        if not project.get("repo_url"):
            self.repo_button.disabled = True
        if not project.get("demo_url"):
            self.demo_button.disabled = True

    @ui.button(label="📚 Repository", style=discord.ButtonStyle.green, emoji="🔗")
    async def repo_button(self, interaction: discord.Interaction, button: ui.Button):
        # Open repository link
        await interaction.response.send_message(f"Repository: {self.project['repo_url']}", ephemeral=True)

    @ui.button(label="🎯 Live Demo", style=discord.ButtonStyle.green, emoji="🌐")
    async def demo_button(self, interaction: discord.Interaction, button: ui.Button):
        # Open demo link
        await interaction.response.send_message(f"Live Demo: {self.project['demo_url']}", ephemeral=True)

    @ui.button(label="📖 View Full Details", style=discord.ButtonStyle.primary)
    async def details_button(self, interaction: discord.Interaction, button: ui.Button):
        # Show full details
        embed = discord.Embed(title=self.project["title"], description=self.project["description"], color=discord.Color.blue())
        embed.add_field(name="ID", value=str(self.project["id"]), inline=True)
        embed.add_field(name="Status", value=self.project.get("ship_status", "N/A"), inline=True)
        embed.add_field(name="Created", value=self.project["created_at"][:10], inline=True)
        if self.project.get("ai_declaration"):
            embed.add_field(name="AI Declaration", value=self.project["ai_declaration"], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class UserView(ui.View):
    # Action buttons for user details
    def __init__(self, user):
        super().__init__(timeout=180)
        self.user = user

    @ui.button(label="📊 Stats", style=discord.ButtonStyle.primary, emoji="📈")
    async def stats_button(self, interaction: discord.Interaction, button: ui.Button):
        # Show user stats
        embed = discord.Embed(title=f"{self.user['display_name']}'s Stats", color=discord.Color.orange())
        embed.add_field(name="Votes", value=str(self.user.get("vote_count", 0)), inline=True)
        embed.add_field(name="Likes", value=str(self.user.get("like_count", 0)), inline=True)
        embed.add_field(name="Cookies", value=str(self.user.get("cookies", 0)), inline=True)
        embed.add_field(name="Devlog Time (Today)", value=f"{self.user.get('devlog_seconds_today', 0)}s", inline=True)
        embed.add_field(name="Devlog Time (Total)", value=f"{self.user.get('devlog_seconds_total', 0)}s", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="🔗 Slack ID", style=discord.ButtonStyle.blurple)
    async def slack_button(self, interaction: discord.Interaction, button: ui.Button):
        # Show Slack ID
        slack_id = self.user.get("slack_id", "Not linked")
        await interaction.response.send_message(f"Slack ID: `{slack_id}`", ephemeral=True)


class StoreItemView(ui.View):
    # Action buttons for store items
    def __init__(self, item):
        super().__init__(timeout=180)
        self.item = item

    @ui.button(label="💰 Price Info", style=discord.ButtonStyle.success, emoji="💵")
    async def price_button(self, interaction: discord.Interaction, button: ui.Button):
        # Show pricing information
        ticket_cost = self.item.get("ticket_cost", {})
        base_cost = ticket_cost.get('base_cost')
        
        embed = discord.Embed(title=f"🍪 {self.item['name']} - Pricing", color=discord.Color.gold())
        
        # Check if all country prices are the same as base cost
        country_prices = [ticket_cost.get('us'), ticket_cost.get('eu'), ticket_cost.get('uk'), ticket_cost.get('ca')]
        all_same = all(price == base_cost for price in country_prices if price is not None)
        
        if all_same and base_cost is not None:
            # All prices are the same, just show base cost
            embed.add_field(name="Price", value=format_price_with_hours(base_cost), inline=False)
        else:
            # Show individual country prices
            embed.add_field(name="Base Cost", value=format_price_with_hours(base_cost), inline=True)
            embed.add_field(name="US Price", value=format_price_with_hours(ticket_cost.get('us')), inline=True)
            embed.add_field(name="EU Price", value=format_price_with_hours(ticket_cost.get('eu')), inline=True)
            embed.add_field(name="UK Price", value=format_price_with_hours(ticket_cost.get('uk')), inline=True)
            embed.add_field(name="CA Price", value=format_price_with_hours(ticket_cost.get('ca')), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="📦 Availability", style=discord.ButtonStyle.primary)
    async def avail_button(self, interaction: discord.Interaction, button: ui.Button):
        # Show availability
        enabled = self.item.get("enabled", {})
        embed = discord.Embed(title=f"📦 {self.item['name']} - Availability", color=discord.Color.green())
        embed.add_field(name="🇺🇸 United States", value="✅" if enabled.get("enabled_us") else "❌", inline=True)
        embed.add_field(name="🇪🇺 Europe", value="✅" if enabled.get("enabled_eu") else "❌", inline=True)
        embed.add_field(name="🇬🇧 UK", value="✅" if enabled.get("enabled_uk") else "❌", inline=True)
        embed.add_field(name="🇨🇦 Canada", value="✅" if enabled.get("enabled_ca") else "❌", inline=True)
        embed.add_field(name="🇦🇺 Australia", value="✅" if enabled.get("enabled_au") else "❌", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class StorePaginationView(ui.View):
    # Pagination view for store items
    def __init__(self, items_by_type, current_page: int = 0, items_per_page: int = 5):
        super().__init__(timeout=180)
        self.items_by_type = items_by_type
        self.current_page = current_page
        self.items_per_page = items_per_page
        self.item_page = 0  # Current page within the category
        self.types = list(items_by_type.keys())
        
        self.update_buttons()

    def update_buttons(self):
        # Enable/disable buttons based on current page
        current_items = self.items_by_type[self.types[self.current_page]]
        total_item_pages = (len(current_items) - 1) // self.items_per_page
        
        self.prev_button.disabled = self.current_page == 0 and self.item_page == 0
        self.next_button.disabled = self.current_page == len(self.types) - 1 and self.item_page == total_item_pages

    def get_current_embed(self):
        # Get embed for current page
        item_type = self.types[self.current_page]
        type_items = self.items_by_type[item_type]
        
        # Calculate pagination for items within this category
        start_idx = self.item_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = type_items[start_idx:end_idx]
        
        total_item_pages = (len(type_items) - 1) // self.items_per_page + 1
        
        embed = discord.Embed(
            title=f"🛍️ Store Items - {item_type.title()}",
            color=discord.Color.gold(),
            description=f"Found {len(type_items)} {item_type.lower()} item{'s' if len(type_items) != 1 else ''}"
        )

        for item in page_items:
            stock = item.get("stock", "Unknown")
            limited = "🔴 Limited" if item.get("limited") else "🟢 Available"
            embed.add_field(
                name=f"{item['name']} (ID: {item['id']})",
                value=f"{limited} | Stock: {stock}",
                inline=False,
            )

        embed.set_footer(text=f"Category {self.current_page + 1} of {len(self.types)} | Items {self.item_page + 1} of {total_item_pages}")
        return embed

    @ui.button(label="<--", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        # Go to previous page (either previous category or previous items in current category)
        current_items = self.items_by_type[self.types[self.current_page]]
        total_item_pages = (len(current_items) - 1) // self.items_per_page
        
        if self.item_page > 0:
            # Go to previous items page in current category
            self.item_page -= 1
        elif self.current_page > 0:
            # Go to previous category and last items page
            self.current_page -= 1
            prev_items = self.items_by_type[self.types[self.current_page]]
            self.item_page = (len(prev_items) - 1) // self.items_per_page
        
        self.update_buttons()
        embed = self.get_current_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="-->", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        # Go to next page (either next items in current category or next category)
        current_items = self.items_by_type[self.types[self.current_page]]
        total_item_pages = (len(current_items) - 1) // self.items_per_page
        
        if self.item_page < total_item_pages:
            # Go to next items page in current category
            self.item_page += 1
        elif self.current_page < len(self.types) - 1:
            # Go to next category and first items page
            self.current_page += 1
            self.item_page = 0
        
        self.update_buttons()
        embed = self.get_current_embed()
        await interaction.response.edit_message(embed=embed, view=self)


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="project", description="Get a project by ID")
async def get_project(interaction: discord.Interaction, project_id: int):
    # Fetch a specific project
    await interaction.response.defer()
    try:
        project = await api.get_project(project_id)
        embed = discord.Embed(title=project["title"], description=project["description"], color=discord.Color.blue())
        embed.add_field(name="ID", value=str(project["id"]), inline=True)
        embed.add_field(name="Status", value=project.get("ship_status", "N/A"), inline=True)
        if project.get("repo_url"):
            embed.add_field(name="Repository", value=f"[Link]({project['repo_url']})", inline=False)
        if project.get("demo_url"):
            embed.add_field(name="Demo", value=f"[Link]({project['demo_url']})", inline=False)
        embed.set_footer(text=f"Created: {project['created_at']}")
        await send_and_schedule_delete(interaction, embed=embed, view=ProjectView(project))
    except ValueError as e:
        await send_and_schedule_delete(interaction, content=f"Error: {e}")


@bot.tree.command(name="projects", description="Search for projects")
async def search_projects(interaction: discord.Interaction, query: str, page: int = 1):
    # Search for projects
    await interaction.response.defer()
    
    async def render_projects(inter: discord.Interaction, p: int):
        try:
            result = await api.get_projects(page=p, query=query)
            projects = result.get("projects", [])
            pagination = result.get("pagination", {})

            if not projects:
                await send_and_schedule_delete(inter, content="No projects found.")
                return

            embed = discord.Embed(
                title=f"Projects Search Results",
                description=f"Found {pagination.get('total_count', 0)} projects",
                color=discord.Color.green(),
            )

            for project in projects[:5]:  # Show first 5 results
                embed.add_field(
                    name=project["title"],
                    value=f"{project['description'][:100]}...",
                    inline=False,
                )

            embed.set_footer(
                text=f"Page {pagination.get('current_page', 1)} of {pagination.get('total_pages', 1)}"
            )
            view = PaginationView(pagination.get('current_page', 1), pagination.get('total_pages', 1), render_projects)
            await send_and_schedule_delete(inter, embed=embed, view=view)
        except ValueError as e:
            await send_and_schedule_delete(inter, content=f"Error: {e}")
    
    await render_projects(interaction, page)


@bot.tree.command(name="devlog", description="Get a devlog by ID")
async def get_devlog(interaction: discord.Interaction, devlog_id: int):
    # Fetch a specific devlog
    await interaction.response.defer()
    try:
        devlog = await api.get_devlog(devlog_id)
        embed = discord.Embed(
            title=f"Devlog #{devlog_id}",
            description=devlog["body"][:300] + "..." if len(devlog["body"]) > 300 else devlog["body"],
            color=discord.Color.purple(),
        )
        embed.add_field(name="Comments", value=str(devlog.get("comments_count", 0)), inline=True)
        embed.add_field(name="Likes", value=str(devlog.get("likes_count", 0)), inline=True)
        embed.add_field(
            name="Duration", value=f"{devlog.get('duration_seconds', 0)}s", inline=True
        )
        if devlog.get("scrapbook_url"):
            embed.add_field(name="Scrapbook", value=f"[Link]({devlog['scrapbook_url']})", inline=False)
        embed.set_footer(text=f"Created: {devlog['created_at']}")
        await send_and_schedule_delete(interaction, embed=embed)
    except ValueError as e:
        await send_and_schedule_delete(interaction, content=f"Error: {e}")


@bot.tree.command(name="user", description="Get user info by ID")
async def get_user(interaction: discord.Interaction, user_id: int):
    # Fetch a specific user
    await interaction.response.defer()
    try:
        user = await api.get_user(user_id)
        embed = discord.Embed(title=user["display_name"], color=discord.Color.orange())
        embed.add_field(name="ID", value=str(user["id"]), inline=True)
        if user.get("slack_id"):
            embed.add_field(name="Slack ID", value=user["slack_id"], inline=True)
        embed.add_field(name="Votes", value=str(user.get("vote_count", 0)), inline=True)
        embed.add_field(name="Likes", value=str(user.get("like_count", 0)), inline=True)
        embed.add_field(
            name="Devlog Time (Today)", value=f"{user.get('devlog_seconds_today', 0)}s", inline=True
        )
        embed.add_field(
            name="Devlog Time (Total)", value=f"{user.get('devlog_seconds_total', 0)}s", inline=True
        )
        if user.get("avatar"):
            embed.set_thumbnail(url=user["avatar"])
        await send_and_schedule_delete(interaction, embed=embed, view=UserView(user))
    except ValueError as e:
        await send_and_schedule_delete(interaction, content=f"Error: {e}")


@bot.tree.command(name="users", description="Search for users")
async def search_users(interaction: discord.Interaction, query: str, page: int = 1):
    # Search for users
    await interaction.response.defer()
    
    async def render_users(inter: discord.Interaction, p: int):
        try:
            result = await api.get_users(page=p, query=query)
            users = result.get("users", [])
            pagination = result.get("pagination", {})

            if not users:
                await send_and_schedule_delete(inter, content="No users found.")
                return

            embed = discord.Embed(
                title=f"User Search Results",
                description=f"Found {pagination.get('total_count', 0)} users",
                color=discord.Color.yellow(),
            )

            for user in users[:5]:  # Show first 5 results
                embed.add_field(
                    name=user["display_name"],
                    value=f"Slack: {user.get('slack_id', 'N/A')} | Cookies: {user.get('cookies', 0)}",
                    inline=False,
                )

            embed.set_footer(
                text=f"Page {pagination.get('current_page', 1)} of {pagination.get('total_pages', 1)}"
            )
            view = PaginationView(pagination.get('current_page', 1), pagination.get('total_pages', 1), render_users)
            await send_and_schedule_delete(inter, embed=embed, view=view)
        except ValueError as e:
            await send_and_schedule_delete(inter, content=f"Error: {e}")
    
    await render_users(interaction, page)


@bot.tree.command(name="store", description="Get store items")
async def get_store(interaction: discord.Interaction):
    # Fetch store items
    await interaction.response.defer()
    try:
        items = await api.get_store_items()

        if not items:
            await send_and_schedule_delete(interaction, content="No store items found.")
            return

        # Group items by type and sort by price
        items_by_type = {}
        for item in items:
            item_type = item.get("type", "Other")
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)

        # Sort items within each type by base cost (ascending)
        for item_type in items_by_type:
            items_by_type[item_type].sort(key=lambda x: x.get("ticket_cost", {}).get("base_cost", float('inf')))

        # Create pagination view
        view = StorePaginationView(items_by_type)
        embed = view.get_current_embed()
        
        await send_and_schedule_delete(interaction, embed=embed, view=view)

    except ValueError as e:
        await send_and_schedule_delete(interaction, content=f"Error: {e}")


@bot.tree.command(name="store_item", description="Get a store item by ID")
async def get_store_item(interaction: discord.Interaction, item_id: int):
    # Fetch a specific store item
    await interaction.response.defer()
    try:
        item = await api.get_store_item(item_id)
        embed = discord.Embed(title=item["name"], description=item.get("description", ""), color=discord.Color.blurple())
        embed.add_field(name="Type", value=item.get("type", "N/A"), inline=True)
        embed.add_field(name="Stock", value=str(item.get("stock", 0)), inline=True)
        embed.add_field(name="Limited", value="Yes" if item.get("limited") else "No", inline=True)
        
        if item.get("image_url"):
            embed.set_image(url=item["image_url"])
        
        embed.set_footer(text=f"Item ID: {item['id']}")
        await send_and_schedule_delete(interaction, embed=embed, view=StoreItemView(item))
    except ValueError as e:
        await send_and_schedule_delete(interaction, content=f"Error: {e}")


@bot.tree.command(name="devlogs", description="Get recent devlogs")
async def get_devlogs(interaction: discord.Interaction, page: int = 1):
    # Fetch recent devlogs
    await interaction.response.defer()
    
    async def render_devlogs(inter: discord.Interaction, p: int):
        try:
            result = await api.get_devlogs(page=p)
            devlogs = result.get("devlogs", [])
            pagination = result.get("pagination", {})

            if not devlogs:
                await send_and_schedule_delete(inter, content="No devlogs found.")
                return

            embed = discord.Embed(
                title="Recent Devlogs",
                description=f"Total: {pagination.get('total_count', 0)}",
                color=discord.Color.green(),
            )

            for devlog in devlogs[:5]:  # Show first 5
                embed.add_field(
                    name=f"Devlog #{devlog['id']}",
                    value=f"{devlog['body'][:80]}... | 💬 {devlog.get('comments_count', 0)} | ❤️ {devlog.get('likes_count', 0)}",
                    inline=False,
                )

            embed.set_footer(
                text=f"Page {pagination.get('current_page', 1)} of {pagination.get('total_pages', 1)}"
            )
            view = PaginationView(pagination.get('current_page', 1), pagination.get('total_pages', 1), render_devlogs)
            await send_and_schedule_delete(inter, embed=embed, view=view)
        except ValueError as e:
            await send_and_schedule_delete(inter, content=f"Error: {e}")
    
    await render_devlogs(interaction, page)


def main():
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN not found in .env file")
    if not FLAVORTOWN_API_KEY:
        raise ValueError("FLAVORTOWN_API_KEY not found in .env file")

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
