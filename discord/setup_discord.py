"""
Automated Discord Server Setup for GlowStatus
Creates channels, roles, and permissions for the GlowStatus community
"""

import discord
from discord.ext import commands
import asyncio
import json
import os
import aiohttp
from datetime import datetime

# Configuration
CONFIG = {
    "server_name": "GlowStatus",
    "bot_token": os.getenv("DISCORD_BOT_TOKEN") or os.getenv("GLOWBOY"),  # GitHub Actions secret or local env
    "authorized_users": ["severswoed"],  # Only these users can run the bot setup
    "github_integration": {
        "use_github_secret": True,  # Use GLOWBOY secret from GitHub Actions
        "local_fallback": True      # Allow local DISCORD_BOT_TOKEN for testing
    },
    "channels": {
        "info": [
            {"name": "welcome", "description": "Quick intro + project links"},
            {"name": "rules", "description": "Code of conduct"},
            {"name": "announcements", "description": "Releases, roadmap updates"}
        ],
        "support": [
            {"name": "setup-help", "description": "Troubleshooting and questions"},
            {"name": "feature-requests", "description": "Community ideas and feedback"},
            {"name": "integration-requests", "description": "Ask for brand support"}
        ],
        "development": [
            {"name": "dev-updates", "description": "Auto post from GitHub"},
            {"name": "cli-version-v1", "description": "v1 CLI questions/support"},
            {"name": "app-version-v2", "description": "v2 GUI installer questions/support"},
            {"name": "api-dev", "description": "Endpoint discussion"}
        ],
        "lounge": [
            {"name": "general", "description": "Chit-chat"},
            {"name": "show-your-glow", "description": "Users post pics of their setup"}
        ]
    },
    "roles": {
        "admin": {"name": "🛡️ Admin", "color": 0xFF0000, "permissions": ["administrator"]},
        "moderator": {"name": "🔨 Moderator", "color": 0xFF6600, "permissions": ["manage_messages", "manage_channels", "kick_members", "ban_members"]},
        "sponsor": {"name": "✨ Sponsor", "color": 0xFFD700, "permissions": ["embed_links", "attach_files"]},
        "beta_tester": {"name": "🧪 Beta Tester", "color": 0x9932CC, "permissions": ["embed_links"]},
        "dev_team": {"name": "⚙️ Dev Team", "color": 0xFF4500, "permissions": ["manage_messages", "embed_links", "attach_files"]},
        "support": {"name": "🖥️ Support", "color": 0x00CED1, "permissions": ["manage_messages"]},
        "verified": {"name": "✅ Verified", "color": 0x00FF00, "permissions": []},
        "trusted_bots": {"name": "🤖 Trusted Bots", "color": 0x808080, "permissions": ["embed_links", "attach_files"]},
        "quarantine": {"name": "⚠️ Quarantine", "color": 0x800000, "permissions": []}
    },
    "protected_channels": ["welcome", "rules", "general", "show-your-glow", "feature-requests"],
    "bot_allowed_channels": ["dev-updates", "announcements"],
    "security": {
        "verification_level": "medium",  # none, low, medium, high, very_high
        "content_filter": "all_members",  # disabled, members_without_roles, all_members
        "require_verified_email": True,
        "rate_limit_per_user": 5,  # seconds between messages for new users
        "auto_moderation": {
            "enabled": True,
            "block_spam": True,
            "block_invites": True,
            "block_excessive_caps": True,
            "block_suspicious_links": True
        }
    },
    "owner": {
        "username": "severswoed",  # Discord username (without @)
        "user_id": None,  # Will be set automatically when found
        "auto_assign_admin": True
    },
    "github_webhooks": {
        "enabled": True,
        "repositories": [
            {
                "name": "GlowStatus",
                "owner": "Severswoed",
                "channel": "dev-updates",
                "events": ["push", "pull_request", "release", "issues"]
            },
            {
                "name": "GlowStatus-site", 
                "owner": "Severswoed",
                "channel": "dev-updates",
                "events": ["push", "pull_request", "release"]
            }
        ]
    }
}

class GlowStatusSetup(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True  # For member join/leave events
        intents.message_content = True  # For content filtering
        intents.moderation = True  # For auto-mod features
        super().__init__(command_prefix='!', intents=intents)

    async def on_ready(self):
        print(f'Bot logged in as {self.user}')
        
        # Security check: Verify authorized user is running this
        if not await self.verify_authorized_user():
            print("❌ Unauthorized user attempting to run Discord setup")
            print("⚠️ Only authorized maintainers can configure the server")
            await self.close()
            return
        
        # Get the action to perform (from GitHub Actions input or default)
        action = os.getenv("DISCORD_SETUP_ACTION", "setup").lower()
        
        guild = discord.utils.get(self.guilds, name=CONFIG["server_name"])
        if not guild:
            print(f"Server '{CONFIG['server_name']}' not found!")
            await self.close()
            return
        
        # Perform the requested action
        if action == "setup":
            await self.setup_server(guild)
            await self.assign_owner_privileges(guild)
        elif action == "update-webhooks":
            await self.setup_github_webhooks(guild)
        elif action == "security-check":
            await self.run_security_audit(guild)
        else:
            print(f"❌ Unknown action: {action}")
        
        await self.close()  # Close bot after completing action

    async def on_member_join(self, member):
        """Handle new member security screening"""
        await self.screen_new_member(member)

    async def on_message(self, message):
        """Monitor messages for security threats"""
        if message.author.bot:
            return
        
        await self.check_message_security(message)
        await self.process_commands(message)

    async def verify_authorized_user(self):
        """Verify that an authorized user is running the Discord setup"""
        # Check if running in GitHub Actions (controlled environment)
        if os.getenv("GITHUB_ACTIONS") == "true":
            github_actor = os.getenv("GITHUB_ACTOR", "").lower()
            if github_actor in [user.lower() for user in CONFIG["authorized_users"]]:
                print(f"✅ Authorized GitHub Actions run by: {github_actor}")
                return True
            else:
                print(f"❌ Unauthorized GitHub Actions user: {github_actor}")
                return False
        
        # For local runs, check environment or prompt for confirmation
        local_user = os.getenv("DISCORD_SETUP_USER", "").lower()
        if local_user in [user.lower() for user in CONFIG["authorized_users"]]:
            print(f"✅ Authorized local user: {local_user}")
            return True
        
        # Interactive confirmation for local testing
        print("🔐 Discord Bot Setup Security Check")
        print("This setup will configure the GlowStatus Discord server.")
        print("Only authorized maintainers should run this setup.")
        print()
        
        user_input = input("Enter your Discord username to continue (or 'cancel' to abort): ").strip().lower()
        
        if user_input == "cancel":
            print("Setup cancelled by user")
            return False
        
        if user_input in [user.lower() for user in CONFIG["authorized_users"]]:
            print(f"✅ Authorized user confirmed: {user_input}")
            return True
        else:
            print(f"❌ User '{user_input}' is not authorized to run Discord setup")
            print(f"Authorized users: {', '.join(CONFIG['authorized_users'])}")
            return False

    async def setup_server(self, guild):
        """Setup the entire server structure"""
        print(f"Setting up server: {guild.name}")
        
        # Apply server security settings first
        await self.setup_server_security(guild)
        
        # Create roles first
        await self.create_roles(guild)
        
        # Create categories and channels
        await self.create_channels(guild)
        
        # Set up permissions
        await self.setup_permissions(guild)
        
        # Setup auto-moderation
        await self.setup_auto_moderation(guild)
        
        # Create welcome message
        await self.setup_welcome_channel(guild)
        
        # Setup GitHub webhooks
        await self.setup_github_webhooks(guild)
        
        print("Server setup complete!")

    async def create_roles(self, guild):
        """Create all necessary roles"""
        print("Creating roles...")
        existing_roles = [role.name for role in guild.roles]
        
        for role_key, role_config in CONFIG["roles"].items():
            if role_config["name"] not in existing_roles:
                await guild.create_role(
                    name=role_config["name"],
                    color=discord.Color(role_config["color"]),
                    reason="GlowStatus server setup"
                )
                print(f"Created role: {role_config['name']}")

    async def create_channels(self, guild):
        """Create all channels with categories"""
        print("Creating channels...")
        
        for category_name, channels in CONFIG["channels"].items():
            # Create category
            category_emoji = {
                "info": "🟢",
                "support": "🔧", 
                "development": "🔨",
                "lounge": "☕"
            }
            
            category_display_name = f"{category_emoji.get(category_name, '')} {category_name.title()}"
            category = discord.utils.get(guild.categories, name=category_display_name)
            
            if not category:
                category = await guild.create_category(category_display_name)
                print(f"Created category: {category_display_name}")
            
            # Create channels in category
            for channel_config in channels:
                channel_name = channel_config["name"]
                existing_channel = discord.utils.get(guild.channels, name=channel_name)
                
                if not existing_channel:
                    await guild.create_text_channel(
                        channel_name,
                        category=category,
                        topic=channel_config["description"]
                    )
                    print(f"Created channel: #{channel_name}")

    async def setup_permissions(self, guild):
        """Setup channel permissions to protect from bot spam and enhance security"""
        print("Setting up permissions...")
        
        # Get security roles
        trusted_bots_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["trusted_bots"]["name"])
        quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        verified_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["verified"]["name"])
        
        # Set @everyone permissions (restrict by default)
        everyone_role = guild.default_role
        
        # Restrict bots from protected channels
        for channel_name in CONFIG["protected_channels"]:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel:
                # Block untrusted bots
                if trusted_bots_role:
                    await channel.set_permissions(
                        trusted_bots_role,
                        send_messages=False,
                        embed_links=False,
                        attach_files=False,
                        reason="Protect from bot spam"
                    )
                
                # Quarantined users can only read
                if quarantine_role:
                    await channel.set_permissions(
                        quarantine_role,
                        send_messages=False,
                        add_reactions=False,
                        attach_files=False,
                        embed_links=False,
                        reason="Quarantine restrictions"
                    )
                
                # Apply rate limiting for new users
                await channel.edit(
                    slowmode_delay=CONFIG["security"]["rate_limit_per_user"],
                    reason="Rate limiting for security"
                )
                
                print(f"🔒 Secured #{channel_name}")

        # Allow trusted bots in specific channels
        for channel_name in CONFIG["bot_allowed_channels"]:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel and trusted_bots_role:
                await channel.set_permissions(
                    trusted_bots_role,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    reason="Allow trusted bot posting"
                )
                print(f"✅ Allowed trusted bots in #{channel_name}")

        # Create a quarantine channel if needed
        quarantine_channel = discord.utils.get(guild.channels, name="quarantine")
        if not quarantine_channel and quarantine_role:
            quarantine_category = discord.utils.get(guild.categories, name="🔒 Moderation")
            if not quarantine_category:
                quarantine_category = await guild.create_category("🔒 Moderation")
            
            quarantine_channel = await guild.create_text_channel(
                "quarantine",
                category=quarantine_category,
                topic="Temporary holding area for new/suspicious accounts"
            )
            
            # Only quarantined users and staff can see this channel
            await quarantine_channel.set_permissions(everyone_role, view_channel=False)
            await quarantine_channel.set_permissions(quarantine_role, view_channel=True, send_messages=True)
            
            print("🔒 Created quarantine channel")

    async def setup_welcome_channel(self, guild):
        """Create welcome message with links"""
        welcome_channel = discord.utils.get(guild.channels, name="welcome")
        if not welcome_channel:
            print("Welcome channel not found!")
            return

        welcome_embed = discord.Embed(
            title="🌟 Welcome to GlowStatus!",
            description="Light up your availability with smart LED integration",
            color=0x00FF7F
        )
        
        welcome_embed.add_field(
            name="🔗 Important Links",
            value=(
                "🌐 **Website:** [glowstatus.app](https://glowstatus.app)\n"
                "💻 **GitHub:** [Severswoed/GlowStatus](https://github.com/Severswoed/GlowStatus)\n"
                "💡 **Sponsor:** [GitHub Sponsors](https://github.com/sponsors/Severswoed)\n"
                "📬 **Contact:** glowstatus.app@gmail.com"
            ),
            inline=False
        )
        
        welcome_embed.add_field(
            name="📁 Channel Guide",
            value=(
                "🟢 **Info:** Welcome, rules, announcements\n"
                "🔧 **Support:** Get help and request features\n"
                "🔨 **Development:** Updates and technical discussion\n"
                "☕ **Lounge:** General chat and show off your setup!"
            ),
            inline=False
        )
        
        welcome_embed.set_footer(text="React with 👋 to get started!")
        
        # Clear existing messages and post welcome
        await welcome_channel.purge()
        message = await welcome_channel.send(embed=welcome_embed)
        await message.add_reaction("👋")

    async def setup_server_security(self, guild):
        """Apply server-wide security settings"""
        print("Configuring server security...")
        
        # Set verification level
        verification_levels = {
            "none": discord.VerificationLevel.none,
            "low": discord.VerificationLevel.low,
            "medium": discord.VerificationLevel.medium,
            "high": discord.VerificationLevel.high,
            "very_high": discord.VerificationLevel.highest
        }
        
        # Set content filter
        content_filters = {
            "disabled": discord.ContentFilter.disabled,
            "members_without_roles": discord.ContentFilter.no_role,
            "all_members": discord.ContentFilter.all_members
        }
        
        try:
            await guild.edit(
                verification_level=verification_levels[CONFIG["security"]["verification_level"]],
                explicit_content_filter=content_filters[CONFIG["security"]["content_filter"]],
                reason="GlowStatus security setup"
            )
            print(f"Applied security settings: {CONFIG['security']['verification_level']} verification")
        except Exception as e:
            print(f"Error setting server security: {e}")

    async def setup_auto_moderation(self, guild):
        """Setup auto-moderation rules"""
        if not CONFIG["security"]["auto_moderation"]["enabled"]:
            return
            
        print("Setting up auto-moderation...")
        
        try:
            # Create spam protection rule
            if CONFIG["security"]["auto_moderation"]["block_spam"]:
                await guild.create_auto_moderation_rule(
                    name="Anti-Spam Protection",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModTriggerType.spam
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        ),
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.timeout,
                            metadata=discord.AutoModActionMetadata(duration_seconds=300)
                        )
                    ],
                    enabled=True,
                    reason="GlowStatus anti-spam protection"
                )
                print("Created anti-spam rule")

            # Create invite link blocking rule  
            if CONFIG["security"]["auto_moderation"]["block_invites"]:
                await guild.create_auto_moderation_rule(
                    name="Block Invite Links",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModTriggerType.keyword,
                        keyword_filter=["discord.gg/", "discord.com/invite/", "discordapp.com/invite/"]
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        )
                    ],
                    enabled=True,
                    reason="Block unauthorized invite links"
                )
                print("Created invite blocking rule")

        except Exception as e:
            print(f"Auto-moderation setup error: {e}")

    async def screen_new_member(self, member):
        """Screen new members for security threats"""
        guild = member.guild
        
        # Check account age (flag accounts less than 7 days old)
        account_age = (discord.utils.utcnow() - member.created_at).days
        if account_age < 7:
            print(f"⚠️ New account detected: {member.name} (created {account_age} days ago)")
            
            # Apply quarantine role for very new accounts
            if account_age < 1:
                quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
                if quarantine_role:
                    await member.add_roles(quarantine_role, reason="Very new account - quarantine")
                    print(f"🔒 Quarantined {member.name} - account less than 1 day old")

        # Log member join
        print(f"👤 New member: {member.name}#{member.discriminator} (Account: {account_age} days old)")

    async def check_message_security(self, message):
        """Check messages for security threats"""
        if not message.guild:
            return
            
        # Check for excessive caps (more than 70% uppercase)
        if len(message.content) > 10:
            caps_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
            if caps_ratio > 0.7 and CONFIG["security"]["auto_moderation"]["block_excessive_caps"]:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, please don't use excessive caps.",
                    delete_after=10
                )
                return

        # Check for suspicious links
        suspicious_domains = [
            "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", 
            "short.link", "cutt.ly", "tiny.cc"
        ]
        
        if any(domain in message.content.lower() for domain in suspicious_domains):
            if CONFIG["security"]["auto_moderation"]["block_suspicious_links"]:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, suspicious links are not allowed. Please use direct links.",
                    delete_after=15
                )
                print(f"🔗 Blocked suspicious link from {message.author.name}")

    @commands.command(name='quarantine')
    @commands.has_permissions(manage_roles=True)
    async def quarantine_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Quarantine a suspicious user"""
        quarantine_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        if not quarantine_role:
            await ctx.send("❌ Quarantine role not found!")
            return
        
        await member.add_roles(quarantine_role, reason=f"Quarantined by {ctx.author}: {reason}")
        await ctx.send(f"🔒 {member.mention} has been quarantined. Reason: {reason}")
        print(f"🔒 {member.name} quarantined by {ctx.author.name}: {reason}")

    @commands.command(name='unquarantine')
    @commands.has_permissions(manage_roles=True)
    async def unquarantine_user(self, ctx, member: discord.Member):
        """Remove quarantine from a user"""
        quarantine_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        verified_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["verified"]["name"])
        
        if quarantine_role in member.roles:
            await member.remove_roles(quarantine_role, reason=f"Unquarantined by {ctx.author}")
            if verified_role:
                await member.add_roles(verified_role, reason="Verified after quarantine")
            await ctx.send(f"✅ {member.mention} has been released from quarantine and verified.")
            print(f"✅ {member.name} unquarantined by {ctx.author.name}")
        else:
            await ctx.send(f"❌ {member.mention} is not quarantined.")

    @commands.command(name='verify')
    @commands.has_permissions(manage_roles=True)
    async def verify_user(self, ctx, member: discord.Member):
        """Manually verify a user"""
        verified_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["verified"]["name"])
        if not verified_role:
            await ctx.send("❌ Verified role not found!")
            return
        
        await member.add_roles(verified_role, reason=f"Manually verified by {ctx.author}")
        await ctx.send(f"✅ {member.mention} has been manually verified.")
        print(f"✅ {member.name} manually verified by {ctx.author.name}")

    @commands.command(name='lockdown')
    @commands.has_permissions(manage_channels=True)
    async def lockdown_channel(self, ctx, channel: discord.TextChannel = None):
        """Lock down a channel to prevent new messages"""
        if not channel:
            channel = ctx.channel
        
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"🔒 {channel.mention} has been locked down.")
        print(f"🔒 Channel {channel.name} locked down by {ctx.author.name}")

    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        if not channel:
            channel = ctx.channel
        
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send(f"🔓 {channel.mention} has been unlocked.")
        print(f"🔓 Channel {channel.name} unlocked by {ctx.author.name}")

    @commands.command(name='security_status')
    @commands.has_permissions(manage_guild=True)
    async def security_status(self, ctx):
        """Show current security status of the server"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title="🛡️ Server Security Status",
            color=0x00FF00
        )
        
        embed.add_field(
            name="Verification Level",
            value=str(guild.verification_level).title(),
            inline=True
        )
        
        embed.add_field(
            name="Content Filter",
            value=str(guild.explicit_content_filter).replace('_', ' ').title(),
            inline=True
        )
        
        embed.add_field(
            name="Member Count",
            value=f"{guild.member_count} members",
            inline=True
        )
        
        # Count quarantined users
        quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        quarantined_count = len(quarantine_role.members) if quarantine_role else 0
        
        embed.add_field(
            name="Quarantined Users",
            value=f"{quarantined_count} users",
            inline=True
        )
        
        await ctx.send(embed=embed)

    async def assign_owner_privileges(self, guild):
        """Assign admin privileges to the server owner"""
        if not CONFIG["owner"]["auto_assign_admin"]:
            return
            
        print("Assigning owner privileges...")
        
        # Find the owner by username
        owner_member = None
        for member in guild.members:
            if member.name.lower() == CONFIG["owner"]["username"].lower():
                owner_member = member
                CONFIG["owner"]["user_id"] = member.id
                break
        
        if not owner_member:
            print(f"⚠️ Owner '{CONFIG['owner']['username']}' not found in server!")
            return
        
        # Get admin role
        admin_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["admin"]["name"])
        if not admin_role:
            print("❌ Admin role not found!")
            return
        
        # Assign admin role to owner
        if admin_role not in owner_member.roles:
            await owner_member.add_roles(admin_role, reason="Server owner - auto-assigned admin")
            print(f"👑 Assigned admin privileges to {owner_member.name}")
        else:
            print(f"✅ {owner_member.name} already has admin privileges")

    async def setup_github_webhooks(self, guild):
        """Setup GitHub webhook integration"""
        if not CONFIG["github_webhooks"]["enabled"]:
            return
            
        print("Setting up GitHub webhooks...")
        
        # Create webhook information file
        webhook_data = {
            "webhooks": [],
            "setup_instructions": {
                "step_1": "Go to your GitHub repository settings",
                "step_2": "Navigate to 'Webhooks' section", 
                "step_3": "Click 'Add webhook'",
                "step_4": "Use the webhook URLs provided below",
                "step_5": "Set Content type to 'application/json'",
                "step_6": "Select events or choose 'Just the push event' for basic setup"
            }
        }
        
        for repo_config in CONFIG["github_webhooks"]["repositories"]:
            channel = discord.utils.get(guild.channels, name=repo_config["channel"])
            if not channel:
                print(f"❌ Channel #{repo_config['channel']} not found for {repo_config['name']} webhook")
                continue
            
            # Create webhook for the channel
            try:
                webhook = await channel.create_webhook(
                    name=f"GitHub-{repo_config['name']}",
                    reason=f"GitHub webhook for {repo_config['owner']}/{repo_config['name']}"
                )
                
                webhook_info = {
                    "repository": f"{repo_config['owner']}/{repo_config['name']}",
                    "channel": repo_config["channel"],
                    "webhook_url": webhook.url,
                    "events": repo_config["events"],
                    "setup_date": datetime.now().isoformat()
                }
                
                webhook_data["webhooks"].append(webhook_info)
                print(f"✅ Created webhook for {repo_config['owner']}/{repo_config['name']} -> #{repo_config['channel']}")
                
            except Exception as e:
                print(f"❌ Error creating webhook for {repo_config['name']}: {e}")
        
        # Save webhook information to file
        try:
            webhook_file_path = os.path.join(os.path.dirname(__file__), "active_webhooks.json")
            with open(webhook_file_path, 'w') as f:
                json.dump(webhook_data, f, indent=2)
            print(f"📄 Webhook information saved to: {webhook_file_path}")
        except Exception as e:
            print(f"❌ Error saving webhook data: {e}")
        
        # Send setup instructions to dev-updates channel
        await self.send_webhook_instructions(guild, webhook_data)

    async def send_webhook_instructions(self, guild, webhook_data):
        """Send GitHub webhook setup instructions privately to severswoed"""
        if not webhook_data["webhooks"]:
            return
        
        # Find severswoed user
        owner_member = None
        for member in guild.members:
            if member.name.lower() == CONFIG["owner"]["username"].lower():
                owner_member = member
                break
        
        if not owner_member:
            print(f"⚠️ Could not find {CONFIG['owner']['username']} to send private webhook info")
            return
        
        # Send webhook URLs privately via DM
        try:
            embed = discord.Embed(
                title="🔗 GitHub Webhook Setup (PRIVATE)",
                description="🔒 **CONFIDENTIAL** - Your webhook URLs for GitHub integration",
                color=0x238636
            )
            
            for webhook in webhook_data["webhooks"]:
                embed.add_field(
                    name=f"📦 {webhook['repository']}",
                    value=(
                        f"**Channel:** #{webhook['channel']}\n"
                        f"**Events:** {', '.join(webhook['events'])}\n"
                        f"**Webhook URL:** {webhook['webhook_url']}\n"
                        f"⚠️ Keep this URL secret!"
                    ),
                    inline=False
                )
            
            embed.add_field(
                name="🛠️ Setup Steps",
                value=(
                    "1. Go to your GitHub repository\n"
                    "2. Settings → Webhooks → Add webhook\n"
                    "3. Paste the webhook URL above\n"
                    "4. Content type: `application/json`\n"
                    "5. Select events or use 'Just the push event'\n"
                    "6. Click 'Add webhook'"
                ),
                inline=False
            )
            
            embed.set_footer(text="This message was sent privately for security. Do not share webhook URLs.")
            
            await owner_member.send(embed=embed)
            print(f"📧 Sent private webhook setup instructions to {owner_member.name}")
            
        except discord.Forbidden:
            print(f"❌ Could not send DM to {owner_member.name} - they may have DMs disabled")
            print("⚠️ Webhook URLs are saved in active_webhooks.json file instead")
        except Exception as e:
            print(f"❌ Error sending private webhook info: {e}")
        
        # Send public notification (without URLs) to dev-updates channel
        dev_channel = discord.utils.get(guild.channels, name="dev-updates")
        if dev_channel:
            public_embed = discord.Embed(
                title="✅ GitHub Webhooks Configured",
                description="GitHub integration has been set up successfully!",
                color=0x00FF00
            )
            
            public_embed.add_field(
                name="📦 Repositories Connected",
                value="\n".join([f"• {webhook['repository']}" for webhook in webhook_data["webhooks"]]),
                inline=False
            )
            
            public_embed.add_field(
                name="🔔 What to Expect",
                value=(
                    "This channel will now receive automatic updates for:\n"
                    "• New commits and pushes\n"
                    "• Pull requests\n"
                    "• New releases\n"
                    "• Issues (for main repo)"
                ),
                inline=False
            )
            
            public_embed.set_footer(text="Webhook configuration sent privately to server owner")
            
            await dev_channel.send(embed=public_embed)
            print("📋 Sent public webhook notification to #dev-updates")

    @commands.command(name='webhooks')
    @commands.has_permissions(manage_guild=True)
    async def list_webhooks(self, ctx):
        """List all active GitHub webhooks"""
        try:
            webhook_file_path = os.path.join(os.path.dirname(__file__), "active_webhooks.json")
            if not os.path.exists(webhook_file_path):
                await ctx.send("❌ No webhook configuration found. Run setup first.")
                return
            
            with open(webhook_file_path, 'r') as f:
                webhook_data = json.load(f)
            
            if not webhook_data["webhooks"]:
                await ctx.send("❌ No active webhooks found.")
                return
            
            embed = discord.Embed(
                title="🔗 Active GitHub Webhooks",
                color=0x238636
            )
            
            for webhook in webhook_data["webhooks"]:
                embed.add_field(
                    name=f"📦 {webhook['repository']}",
                    value=(
                        f"**Channel:** #{webhook['channel']}\n"
                        f"**Events:** {', '.join(webhook['events'])}\n"
                        f"**Setup:** {webhook['setup_date'][:10]}"
                    ),
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error retrieving webhook data: {e}")

    async def run_security_audit(self, guild):
        """Run a comprehensive security audit of the Discord server"""
        print("🔍 Running Discord server security audit...")
        
        audit_results = {
            "server_name": guild.name,
            "member_count": guild.member_count,
            "verification_level": str(guild.verification_level),
            "content_filter": str(guild.explicit_content_filter),
            "audit_date": datetime.now().isoformat()
        }
        
        # Check roles
        audit_results["roles"] = {
            "total_roles": len(guild.roles),
            "admin_roles": [role.name for role in guild.roles if role.permissions.administrator],
            "quarantine_enabled": any(CONFIG["roles"]["quarantine"]["name"] in role.name for role in guild.roles),
            "trusted_bots_role": any(CONFIG["roles"]["trusted_bots"]["name"] in role.name for role in guild.roles)
        }
        
        # Check channels
        audit_results["channels"] = {
            "total_channels": len(guild.channels),
            "protected_channels": len([ch for ch in guild.channels if ch.name in CONFIG["protected_channels"]]),
            "rate_limited_channels": len([ch for ch in guild.channels if hasattr(ch, 'slowmode_delay') and ch.slowmode_delay > 0])
        }
        
        # Check quarantined members
        quarantine_role = discord.utils.get(guild.roles, name=CONFIG["roles"]["quarantine"]["name"])
        audit_results["security"] = {
            "quarantined_members": len(quarantine_role.members) if quarantine_role else 0,
            "automod_rules": len(await guild.fetch_auto_moderation_rules()) if hasattr(guild, 'fetch_auto_moderation_rules') else 0
        }
        
        # Save audit results
        audit_file = os.path.join(os.path.dirname(__file__), f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(audit_file, 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        print(f"✅ Security audit completed - saved to: {audit_file}")
        print(f"📊 Summary: {audit_results['member_count']} members, {audit_results['security']['quarantined_members']} quarantined")

    @commands.command(name='remake_webhooks')
    @commands.has_permissions(administrator=True)
    async def remake_webhooks(self, ctx):
        """Recreate all GitHub webhooks (admin only)"""
        await ctx.send("🔄 Recreating GitHub webhooks...")
        await self.setup_github_webhooks(ctx.guild)
        await ctx.send("✅ GitHub webhooks have been recreated!")

    @commands.command(name='assign_admin')
    @commands.has_permissions(administrator=True)
    async def assign_admin_command(self, ctx, member: discord.Member):
        """Manually assign admin role to a member"""
        admin_role = discord.utils.get(ctx.guild.roles, name=CONFIG["roles"]["admin"]["name"])
        if not admin_role:
            await ctx.send("❌ Admin role not found!")
            return
        
        if admin_role in member.roles:
            await ctx.send(f"✅ {member.mention} already has admin privileges.")
            return
        
        await member.add_roles(admin_role, reason=f"Admin assigned by {ctx.author}")
        await ctx.send(f"👑 Assigned admin privileges to {member.mention}")
        print(f"👑 {member.name} assigned admin by {ctx.author.name}")

def main():
    """Run the Discord setup bot with security checks"""
    print("🤖 GlowStatus Discord Bot Setup")
    print("=" * 40)
    
    # Security validation
    if not CONFIG["bot_token"]:
        print("❌ No Discord bot token found!")
        print("For GitHub Actions: GLOWBOY secret should be set")
        print("For local testing: Set DISCORD_BOT_TOKEN environment variable")
        print("For authorized users: Set DISCORD_SETUP_USER environment variable")
        return
    
    # Check if running in a secure environment
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
    github_actor = os.getenv("GITHUB_ACTOR", "unknown")
    
    if is_github_actions:
        print(f"🔐 Running in GitHub Actions environment")
        print(f"👤 Triggered by: {github_actor}")
        if github_actor.lower() not in [user.lower() for user in CONFIG["authorized_users"]]:
            print(f"❌ ERROR: {github_actor} is not authorized to run Discord setup!")
            print(f"✅ Authorized users: {', '.join(CONFIG['authorized_users'])}")
            print("🛡️ Security: Bot setup blocked for unauthorized user")
            return
    else:
        print("🖥️ Running in local environment")
        print("⚠️ Ensure you are an authorized maintainer before proceeding")
    
    bot = GlowStatusSetup()
    
    print("\n🛡️ Security Features Enabled:")
    print("- User authorization verification")
    print("- Auto-moderation (spam, invites, caps)")
    print("- New member screening")
    print("- Quarantine system")
    print("- Channel lockdown commands")
    print("- Security status monitoring")
    print("- Owner privilege assignment")
    print("- GitHub webhook integration")
    print("- Repository monitoring (GlowStatus, GlowStatus-site)")
    print("\n🚀 Starting Discord bot...")
    
    try:
        bot.run(CONFIG["bot_token"])
    except discord.LoginFailure:
        print("❌ Discord login failed - invalid bot token")
        print("Check that GLOWBOY secret is set correctly in GitHub")
    except Exception as e:
        print(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    main()
