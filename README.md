# webRPG

TO-DO:
- Coordinate Grid
    - Add Position & Move Speed To Entities
    - Maybe small, 10x10
- Stats:
    - Movement Speed
    - Armor Inventory
    - Carrying Cap
- Highlight Command Words
- Items
    - Update items to have On pickup, On drop, on Use scripts
    - Item Types:
        - Armor
        - Weapon
        - Consumable
- Entities:
    - Update entities to have On Spawn, On Death, On Attack Scripts
    - Types:
        - Alive
            - Can pick up if small
            - Alive items have turns
        - Item
        - Big
- Commands:
    - Player:
        - Attack <entity> / <player>
            - Requires items to have range
        - Move <>
            - Requires Grid & Move Speed
            - Better Approach May Be To Set Up Grid Fire Emblem Style
        - Use <item>
            - Use Inventory Item 
        - Use <entity>
            - Use Entity
        - Grab <entity>
            - Pick Up Entity
        - Echo
    
    - Gamemaster:
        - Tp <entity>/<player> <location>
        - Save Scene
        - Set Scene
        - Heal <entity>/<player> <number>
        - Damage <entity>/<player> <number>
            - Before player dies, give gamemaster chance to veto
        - Set Health <entity>/<player> <percentage>



    
- Command Scripting
- Token Ring Turn System


COMPLETE:
- SPAWN command
- Realtime Chat System
- Game & Player Management
- Registration / Login System