<h1 align="center">
  <br>
  <img src="https://i.ibb.co/sqPsXMR/Logo-Animation.gif" alt="EldenRingDiscordBot">
  <br>
  Lands Between
  <br>
</h1>

<p align="center">
  A Discord bot to search for detailed information on any Elden Ring item, including stats, descriptions, and images (DLC supported).
</p>

---

## Installation

### Install Requirements
To install the necessary dependencies, run:
```bash
pip install -r requirements.txt
```

### Configure the `.env` File
Edit the `.env` file with your bot's settings:
```env
DISCORD_BOT_TOKEN=<Your Discord Bot Token Here>

# Options: online, idle, dnd, invisible
DISCORD_STATUS=online

# Watching Activity
DISCORD_ACTIVITY_WATCHING=discord.gg/xcc

AUTHOR_NAME=Lands Between
ICON_URL=https://i.ibb.co/sqPsXMR/Logo-Animation.gif
FOOTER_TEXT=S2RT

NO_ITEMS_FOUND_IMAGE=https://i.pinimg.com/originals/73/b0/05/73b0054acf8be08b254ba90945a19d09.gif
```

---

## Overview

Lands Between is a Discord bot designed to provide detailed information about items in Elden Ring. The bot supports a wide range of queries, including weapons, armor, spells, consumables, and DLC content. Each query returns stats, descriptions, and associated images for the requested item.

### Features:
- Search for any item in the game, including weapons, armor, spells, and more.
- Includes detailed stats and descriptions.
- Provides high-quality images for visual reference.
- Supports base game and DLC content.

---

## Example Usage

### Searching for talisman
```
/talisman item_name:Red-Feathered
```

### Searching for incantation
```
/incantation item_name:golden vow
```

---

## Screenshots

### Searching for an Item
![Item Search Example](https://i.ibb.co/xGjmBzn/Screenshot-1.png)

### No Results Found
![No Results Example](https://i.ibb.co/m8W35CR/Screenshot-2.png)

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
