from datetime import datetime
from dotenv import load_dotenv
from typing import Callable, Awaitable, Any
from discord import Interaction

import ast
import discord
import os
import pandas as pd
import re
from discord.ext import commands

load_dotenv()

csv_files = {
    "ashesOfWar": 'eldenringScrap/ashesOfWar.csv',
    "armors": 'eldenringScrap/armors.csv',
    "bosses": 'eldenringScrap/bosses.csv',
    "incantations": 'eldenringScrap/incantations.csv',
    "shields": 'eldenringScrap/shields.csv',
    "skills": 'eldenringScrap/skills.csv',
    "sorceries": 'eldenringScrap/sorceries.csv',
    "spiritAshes": 'eldenringScrap/spiritAshes.csv',
    "talismans": 'eldenringScrap/talismans.csv',
    "weapons": 'eldenringScrap/weapons.csv',
    "remembrances": 'eldenringScrap/items/remembrances.csv',
    "consumables": 'eldenringScrap/items/consumables.csv',
    "crystalTears": 'eldenringScrap/items/crystalTears.csv',
    "greatRunes": 'eldenringScrap/items/greatRunes.csv',
    "cookbooks": 'eldenringScrap/items/cookbooks.csv',
    "keyitems": 'eldenringScrap/items/keyitems.csv',
    "materials": 'eldenringScrap/items/materials.csv',
    "multi": 'eldenringScrap/items/multi.csv',
    "tools": 'eldenringScrap/items/tools.csv',
    "upgradeMaterials": 'eldenringScrap/items/upgradeMaterials.csv',
    "whetblades": 'eldenringScrap/items/whetblades.csv',
    "bells": 'eldenringScrap/items/bells.csv',
}

dataframes = {name: pd.read_csv(path) for name, path in csv_files.items()}

df = dataframes["ashesOfWar"]
armor_df = dataframes["armors"]
boss_df = dataframes["bosses"]
incantation_df = dataframes["incantations"]
shields_df = dataframes['shields']
skills_df = dataframes['skills']
sorceries_df = dataframes['sorceries']
spirit_ashes_df = dataframes['spiritAshes']
talisman_df = dataframes['talismans']
weapon_df = dataframes['weapons']
remembrances_df = dataframes['remembrances']
consumables_df = dataframes['consumables']
crystalTears_df = dataframes['crystalTears']
greatRunes_df = dataframes['greatRunes']
cookbooks_df = dataframes['cookbooks']
keyitems_df = dataframes['keyitems']
materials_df = dataframes['materials']
multi_df = dataframes['multi']
tools_df = dataframes['tools']
upgradeMaterials_df = dataframes['upgradeMaterials']
whetblades_df = dataframes['whetblades']
bells_df = dataframes['bells']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAX_FIELDS_PER_EMBED = 10

status_mapping = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_ACTIVITY_WATCHING = os.getenv('DISCORD_ACTIVITY_WATCHING')
status_string = os.getenv("DISCORD_STATUS")
DISCORD_STATUS = status_mapping.get(status_string.lower(), discord.Status.online)
ICON_URL = os.getenv('ICON_URL')
FOOTER_TEXT = os.getenv('FOOTER_TEXT')
AUTHOR_NAME = os.getenv('AUTHOR_NAME')
NO_ITEMS_FOUND_IMAGE = os.getenv('NO_ITEMS_FOUND_IMAGE')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    await bot.change_presence(status=DISCORD_STATUS,
                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                        name=DISCORD_ACTIVITY_WATCHING))
    await bot.tree.sync()


def search_item_in_df(df_name, search_value):
    try:
        exact_match = df_name[df_name['name'].str.lower() == search_value.lower()]
        if not exact_match.empty:
            return exact_match

        results = df_name[df_name['name'].str.contains(search_value, case=False, na=False)]
        return results

    except re.error as e:
        print(f"Regex error: {e}")
        return pd.DataFrame()


def validate_item_name(min_length: int = 3) -> Callable[[Callable[[Interaction, str], Awaitable[Any]]], Callable[[Interaction, str], Awaitable[Any]]]:
    def decorator(func: Callable[[Interaction, str], Awaitable[Any]]) -> Callable[[Interaction, str], Awaitable[Any]]:
        async def wrapper(interaction: Interaction, item_name: str) -> Any:
            if len(item_name) < min_length:
                embed = discord.Embed(
                    title="Search Term Too Short",
                    description=f"Please enter at least **{min_length} characters** for your search.",
                    colour=0xbea56f,
                    timestamp=datetime.now()
                )
                embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                await interaction.response.send_message(embed=embed)
                return
            return await func(interaction, item_name)

        return wrapper

    return decorator


@bot.tree.command(name="ashe", description="Search for an Ashe Of War")
@validate_item_name(min_length=3)
async def ashe(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Items Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Affinity: {row['affinity']} | Skill: {row['skill']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            affinity = row['affinity']
            skill = row['skill']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/ashesOfWar/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=f"**Affinity**: {affinity}\n**Skill**: {skill}\n\n**Description**: {description}",
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Items Found",
            description=f"No items found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


def format_damage_negation(damage_negation_str):
    try:
        damage_negation_list = ast.literal_eval(damage_negation_str)
        formatted_str = "\n".join([f"**{k}**: {v}" for item in damage_negation_list for k, v in item.items()])
        return formatted_str
    except Exception as e:
        print(f"Error formatting damage negation: {e}")
        return "N/A"


def format_resistance(resistance_str):
    try:
        resistance_list = ast.literal_eval(resistance_str)
        formatted_str = "\n".join([f"**{k}**: {v}" for item in resistance_list for k, v in item.items()])
        return formatted_str
    except Exception as e:
        print(f"Error formatting resistance: {e}")
        return "N/A"


@bot.tree.command(name="armor", description="Search for an armor")
@validate_item_name(min_length=3)
async def armor(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(armor_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Items Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Weight: {row['weight']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            armor_type = row['type']
            damage_negation = format_damage_negation(row['damage negation'])
            resistance = format_resistance(row['resistance'])
            weight = row['weight']
            special_effect = row['special effect']
            how_to_acquire = row['how to acquire']
            in_game_section = row['in-game section']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/armors/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Type**: {armor_type}\n"
                    f"**Weight**: {weight}\n"
                    f"**Special Effect**: {special_effect if special_effect else 'None'}"
                ),
                inline=False
            )

            embed.add_field(
                name="**Damage Negation**",
                value=damage_negation,
                inline=True
            )

            embed.add_field(
                name="**Resistance**",
                value=resistance,
                inline=True
            )

            embed.add_field(
                name="\u200B",
                value=f"**How to Acquire**: {how_to_acquire}\n**In-Game Section**: {in_game_section}",
                inline=False
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Items Found",
            description=f"No items found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="boss", description="Search for a boss")
@validate_item_name(min_length=3)
async def boss(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(boss_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Bosses Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"HP: {row['HP']} | Location(s): {row['Locations & Drops']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            hp = row['HP']
            locations_and_drops = ast.literal_eval(row['Locations & Drops']) if pd.notna(
                row['Locations & Drops']) else {}
            blockquote = row['blockquote'] if pd.notna(row['blockquote']) else "No quotes available."
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/bosses/{image_filename}'

            file = discord.File(local_image_path, filename=image_filename)

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=f"**HP**: {hp}",
                inline=False
            )

            if locations_and_drops:
                for location, drops in locations_and_drops.items():
                    embed.add_field(
                        name=f"**Location**: {location}",
                        value=f"**Drops**: {', '.join(drops)}",
                        inline=False
                    )

            embed.add_field(
                name="**Quote**",
                value=blockquote,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(file=file, embed=embed)
    else:
        embed = discord.Embed(
            title="No Bosses Found",
            description=f"No bosses found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="incantation", description="Search for an incantation")
@validate_item_name(min_length=3)
async def incantation(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(incantation_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Incantations Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | FP: {row['FP']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            effect = row['effect']
            fp = row['FP']
            slot = row['slot']
            int_stat = row['INT']
            fai_stat = row['FAI']
            arc_stat = row['ARC']
            stamina_cost = row['stamina cost']
            bonus = row['bonus']
            group = row['group']
            location = row['location']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/incantations/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**FP**: {fp}\n"
                    f"**Slot**: {slot}\n"
                    f"**INT**: {int_stat}\n"
                    f"**FAI**: {fai_stat}\n"
                    f"**ARC**: {arc_stat}\n"
                    f"**Stamina Cost**: {stamina_cost}\n"
                    f"**Bonus**: {bonus}\n"
                    f"**Group**: {group}\n"
                    f"**Location**: {location}"
                ),
                inline=False
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            file = discord.File(local_image_path, filename=image_filename)
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Incantations Found",
            description=f"No incantations found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="shield", description="Search for a shield")
@validate_item_name(min_length=3)
async def shield(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(shields_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Shields Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Weight: {row['weight']} | Damage Type: {row['damage type']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            weight = row['weight']
            description = row['description']
            dlc = row['dlc']
            damage_type = row['damage type']
            category = row['category']
            passive_effect = row['passive effect']
            skill = row['skill']
            fp_cost = row['FP cost']

            try:
                requirements = ast.literal_eval(row['requirements'])
                if isinstance(requirements, list):
                    requirements_str = "\n".join(
                        [f"**{key}**: {value}" for req in requirements for key, value in req.items()])
                else:
                    requirements_str = "No specific requirements."
            except (ValueError, SyntaxError):
                requirements_str = "No specific requirements."

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/shields/{image_filename}'

            file = discord.File(local_image_path, filename=image_filename)

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Weight**: {weight}\n"
                    f"**Damage Type**: {damage_type}\n"
                    f"**Category**: {category}\n"
                    f"**Passive Effect**: {passive_effect}\n"
                    f"**Skill**: {skill}\n"
                    f"**FP Cost**: {fp_cost}\n"
                ),
                inline=False
            )

            embed.add_field(
                name="**Requirements**",
                value=requirements_str,
                inline=True
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Shields Found",
            description=f"No shields found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="skill", description="Search for a skill")
@validate_item_name(min_length=3)
async def skill(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(skills_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Skills Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Equipment: {row['equipament']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            skill_type = row['type']
            equipment = row['equipament']
            charge = row['charge']
            fp = row['FP']
            effect = row['effect']
            locations = row['locations']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url) if pd.notna(image_url) and image_url != "No Image" else None
            local_image_path = f'images/skills/{image_filename}' if image_filename else None

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Type**: {skill_type}\n"
                    f"**Equipment**: {equipment}\n"
                    f"**Charge**: {charge}\n"
                    f"**FP**: {fp}\n"
                    f"**Effect**: {effect}\n"
                    f"**Locations**: {locations}\n"
                ),
                inline=False
            )

            if local_image_path and os.path.exists(local_image_path):
                file = discord.File(local_image_path, filename=image_filename)
                embed.set_image(url=f"attachment://{image_filename}")
                embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                await interaction.response.send_message(embed=embed, file=file)
            else:
                embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="No Skills Found",
            description=f"No skills found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sorcery", description="Search for sorcery")
@validate_item_name(min_length=3)
async def sorcery(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(sorceries_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Sorceries Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | FP Cost: {row['FP']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            effect = row['effect']
            fp = row['FP']
            slot = row['slot']
            intelligence = row['INT']
            faith = row['FAI']
            arcane = row['ARC']
            stamina_cost = row['stamina cost']
            bonus = row['bonus']
            location = row['location']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url) if pd.notna(image_url) and image_url != "No Image" else None
            local_image_path = f'images/sorceries/{image_filename}' if image_filename else None

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**FP**: {fp}\n"
                    f"**Slot**: {slot}\n"
                    f"**INT**: {intelligence} | **FAI**: {faith} | **ARC**: {arcane}\n"
                    f"**Stamina Cost**: {stamina_cost}\n"
                    f"**Bonus**: {bonus}\n"
                    f"**Location**: {location}\n"
                ),
                inline=False
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            if local_image_path and os.path.exists(local_image_path):
                file = discord.File(local_image_path, filename=image_filename)
                embed.set_image(url=f"attachment://{image_filename}")
                embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                await interaction.response.send_message(embed=embed, file=file)
            else:
                embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="No Sorceries Found",
            description=f"No sorceries found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="spirit", description="Search for spirit")
@validate_item_name(min_length=3)
async def spirit(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(spirit_ashes_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Spirit Ashes Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"FP Cost: {row['FP cost']} | HP Cost: {row['HP cost']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            type_ = row['type']
            fp_cost = row['FP cost']
            hp_cost = row['HP cost']
            effect = row['effect']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/spiritAshes/{image_filename}'

            file = discord.File(local_image_path, filename=image_filename)

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Type**: {type_}\n"
                    f"**FP Cost**: {fp_cost}\n"
                    f"**HP Cost**: {hp_cost}\n"
                    f"**Effect**: {effect}\n"
                ),
                inline=False
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Spirit Ashes Found",
            description=f"No Spirit Ashes found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="talisman", description="Search for a talisman")
@validate_item_name(min_length=3)
async def talisman(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(talisman_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Talismans Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | Weight: {row['weight']} | Value: {row['value']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            effect = row['effect']
            weight = row['weight']
            value = row['value']
            description = row['description']
            image_url = row['image']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/talismans/{image_filename}'

            file = discord.File(local_image_path, filename=image_filename)

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**Weight**: {weight}\n"
                    f"**Value**: {value}\n"
                ),
                inline=False
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Talismans Found",
            description=f"No talismans found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="weapon", description="Search for a Weapon")
@validate_item_name(min_length=3)
async def weapon(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(weapon_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Weapons Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Weight: {row['weight']} | Damage Type: {row['damage type']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            weight = row['weight']
            description = row['description']
            dlc = row['dlc']

            try:
                requirements = ast.literal_eval(row['requirements'])
                if isinstance(requirements, dict):
                    requirements = [requirements]
            except:
                requirements = [{"Requirement": row['requirements']}]

            damage_type = row['damage type']
            category = row['category']
            passive_effect = row['passive effect']
            skill = row['skill']
            fp_cost = row['FP cost']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"
            image_filename = os.path.basename(image_url)
            local_image_path = f'images/weapons/{image_filename}'

            file = discord.File(local_image_path, filename=image_filename)

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"**Name**: {name} {dlc_label}\n",
                value=(
                    f"**Weight**: {weight}\n"
                    f"**Damage Type**: {damage_type}\n"
                    f"**Category**: {category}\n"
                    f"**Passive Effect**: {passive_effect}\n"
                    f"**Skill**: {skill}\n"
                    f"**FP Cost**: {fp_cost}\n"
                ),
                inline=False
            )

            requirements_str = "\n".join([f"**{key}**: {value}" for req in requirements for key, value in req.items()])
            embed.add_field(
                name="**Requirements**",
                value=requirements_str,
                inline=True
            )

            embed.add_field(
                name="**Description**",
                value=description,
                inline=False
            )

            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Weapons Found",
            description=f"No weapons found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


def search_remembrance(boss_name):
    try:
        results = remembrances_df[remembrances_df['boss'].str.contains(boss_name, case=False, na=False)]
        return results
    except Exception as e:
        print(f"Error during search: {e}")
        return pd.DataFrame()


@bot.tree.command(name="remembrance", description="Search for a remembrance by boss name")
@validate_item_name(min_length=3)
async def remembrance(interaction: discord.Interaction, boss_name: str):
    results = search_remembrance(boss_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Remembrances Found",
                description=(
                    f"Your search for '**{boss_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['boss']}",
                    value=f"Type: {row['type']} | Value: {row['value']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            option_1 = row['option 1']
            option_2 = row['option 2']
            value = row['value']
            dlc = row['dlc']
            boss = row['boss']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/remembrances/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Type**: {row['type']}\n"
                    f"**Boss**: {boss}\n"
                    f"**Value**: {value}\n"
                    f"**Option 1**: {option_1}\n"
                    f"**Option 2**: {option_2}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Remembrances Found",
            description=f"No remembrances found for boss '**{boss_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="consumable", description="Search for consumables")
@validate_item_name(min_length=3)
async def consumable(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(consumables_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Consumables Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | FP Cost: {row['FP cost']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            fp_cost = row['FP cost']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else "(Base Game)"

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/consumables/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**FP Cost**: {fp_cost}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Consumables Found",
            description=f"No consumables found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="tear", description="Search for a Crystal Tear")
@validate_item_name(min_length=3)
async def tear(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(crystalTears_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Crystal Tears Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | FP Cost: {row['FP cost']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            fp_cost = row['FP cost']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/crystalTears/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**FP Cost**: {fp_cost}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Crystal Tears Found",
            description=f"No crystal tears found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


def search_great_rune(search_value):
    try:
        exact_match = greatRunes_df[greatRunes_df['boss'].str.lower() == search_value.lower()]

        if not exact_match.empty:
            return exact_match

        results = greatRunes_df[greatRunes_df['boss'].str.contains(search_value, case=False, na=False)]
        return results
    except re.error as e:
        print(f"Regex error: {e}")
        return pd.DataFrame()


@bot.tree.command(name="greatrune", description="Search for a Great Rune by boss name")
@validate_item_name(min_length=3)
async def greatrune(interaction: discord.Interaction, boss_name: str):
    results = search_great_rune(boss_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Great Runes Found",
                description=(
                    f"Your search for '**{boss_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Effect: {row['effect']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            description = row['description']
            location = row['location']
            divine_tower = row['divine tower locations']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/greatRunes/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Type**: {row['type']}\n"
                    f"**Effect**: {effect}\n"
                    f"**Location**: {location}\n"
                    f"**Divine Tower Location**: {divine_tower}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Great Runes Found",
            description=f"No great runes found for '**{boss_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cookbook", description="Search for a Cookbook")
@validate_item_name(min_length=3)
async def cookbook(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(cookbooks_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Cookbooks Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | Required For: {row['required for']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            required_for = row['required for']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/cookbooks/{image_filename}'

            required_for_str = ', '.join(ast.literal_eval(required_for))
            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**Required For**: {required_for_str}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Cookbooks Found",
            description=f"No cookbooks found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="keyitem", description="Search for a key item by name")
@validate_item_name(min_length=3)
async def keyitem(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(keyitems_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Key Items Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Usage: {row['usage']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            item_type = row['type']
            usage = row['usage']
            location = row['location']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/keyitems/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Type**: {item_type}\n"
                    f"**Usage**: {usage}\n"
                    f"**Location**: {location}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Key Items Found",
            description=f"No key items found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="material", description="Search for a material by name")
@validate_item_name(min_length=3)
async def material(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(materials_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Materials Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/materials/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Materials Found",
            description=f"No materials found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="multi", description="Search for a multiplayer item by name")
@validate_item_name(min_length=3)
async def multi(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(multi_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Items Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Effect: {row['effect']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            item_type = row['type']
            effect = row['effect']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/multi/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Type**: {item_type}\n"
                    f"**Effect**: {effect}\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Items Found",
            description=f"No multiplayer items found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="tool", description="Search for a tool by name")
@validate_item_name(min_length=3)
async def tool(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(tools_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Tools Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Type: {row['type']} | Usage: {row['usage']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            tool_type = row['type']
            usage = row['usage']
            location = row['location']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/tools/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Type**: {tool_type}\n"
                    f"**Usage**: {usage}\n"
                    f"**Location**: {location}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Tools Found",
            description=f"No tools found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="upgradematerial", description="Search for an upgrade material by name")
@validate_item_name(min_length=3)
async def upgradematerial(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(upgradeMaterials_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Upgrade Materials Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            effect = row['effect']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/upgradeMaterials/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Upgrade Materials Found",
            description=f"No upgrade materials found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="whetblade", description="Search for a whetblade by name")
@validate_item_name(min_length=3)
async def whetblade(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(whetblades_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Whetblades Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Usage: {row['usage']} | Location: {row['location']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            description = row['description']
            usage = row['usage']
            location = row['location']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/whetblades/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Usage**: {usage}\n"
                    f"**Location**: {location}\n\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Whetblades Found",
            description=f"No whetblades found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bell", description="Search for a bell bearing by name")
@validate_item_name(min_length=3)
async def bell(interaction: discord.Interaction, item_name: str):
    results = search_item_in_df(bells_df, item_name)

    if not results.empty:
        if len(results) > 1:
            embed = discord.Embed(
                title="Multiple Bell Bearings Found",
                description=(
                    f"Your search for '**{item_name}**' returned **{len(results)}** results. "
                    f"Please refine your search using a more specific name if needed."
                ),
                colour=0xbea56f,
                timestamp=datetime.now()
            )

            fields_count = 0
            for index, row in results.iterrows():
                embed.add_field(
                    name=f"{row['name']}",
                    value=f"Effect: {row['effect']} | Type: {row['type']}",
                    inline=False
                )
                fields_count += 1

                if fields_count >= MAX_FIELDS_PER_EMBED:
                    embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
                    await interaction.response.send_message(embed=embed)
                    return

            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
            await interaction.response.send_message(embed=embed)
        else:
            row = results.iloc[0]

            name = row['name']
            image_url = row['image']
            effect = row['effect']
            description = row['description']
            dlc = row['dlc']

            dlc_label = "(DLC)" if dlc == 1 else ""

            image_filename = os.path.basename(image_url)

            local_image_path = f'images/bells/{image_filename}'

            embed = discord.Embed(colour=0xbea56f, timestamp=datetime.now())
            embed.set_author(name=AUTHOR_NAME, icon_url=ICON_URL)

            embed.add_field(
                name=f"{name} {dlc_label}",
                value=(
                    f"**Effect**: {effect}\n"
                    f"**Description**: {description}"
                ),
                inline=True
            )

            file = discord.File(local_image_path, filename=image_filename)
            embed.set_image(url=f"attachment://{image_filename}")
            embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)

            await interaction.response.send_message(embed=embed, file=file)
    else:
        embed = discord.Embed(
            title="No Bell Bearings Found",
            description=f"No bell bearings found for '**{item_name}**'. Please try again with a different search term.",
            colour=0xbea56f,
            timestamp=datetime.now()
        )
        embed.set_image(url=NO_ITEMS_FOUND_IMAGE)
        embed.set_footer(text=FOOTER_TEXT, icon_url=ICON_URL)
        await interaction.response.send_message(embed=embed)


bot.run(DISCORD_BOT_TOKEN)
