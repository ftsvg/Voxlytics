from discord import app_commands
from typing import List

MODES: List[app_commands.Choice] = [
    app_commands.Choice(name='Overall', value='Overall'),
    app_commands.Choice(name='Bed Bridge Fight', value='Bed Bridge Fight'), 
    app_commands.Choice(name='Void Fight', value='Void Fight'),
    app_commands.Choice(name='Ground Fight', value='Ground Fight'),
    app_commands.Choice(name='Block Sumo', value='Block Sumo'), 
    app_commands.Choice(name='Beta Block Sumo', value='Beta Block Sumo'), 
    app_commands.Choice(name='Bedwars Normal', value='Bedwars Normal'), 
    app_commands.Choice(name='Sumo Duels', value='Sumo Duels'), 
    app_commands.Choice(name='Stick Fight', value='Stick Fight'), 
    app_commands.Choice(name='Pearl Fight', value='Pearl Fight'), 
    app_commands.Choice(name='Bed Rush', value='Bed Rush'),
    app_commands.Choice(name='Obstacles', value='Obstacles'),
    app_commands.Choice(name='Party Games', value='Party Games'),
    app_commands.Choice(name='Bow Fight', value='Bow Fight'), 
    app_commands.Choice(name='Ladder Fight', value='Ladder Fight'), 
    app_commands.Choice(name='Flat Fight', value='Flat Fight'), 
    app_commands.Choice(name='Resource Collect', value='Resource Collect'), 
    app_commands.Choice(name='Miniwars', value='Miniwars'),
]