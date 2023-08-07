from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    players = db.relationship('Player', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    players = db.relationship('Player', backref='game', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Either 'Gamemaster' or 'Adventurer'
    messages = db.relationship('GameMessage', back_populates='player')
    
    name = db.Column(db.String(50), nullable=False, default="")
    health = db.Column(db.Integer, nullable=False, default=100)
    strength = db.Column(db.Integer, nullable=False, default=10)
    mana = db.Column(db.Integer, nullable=False, default=50)
    
    # Relationship to manage player's inventory items
    inventory_items = db.relationship('InventoryItem', backref='owner', lazy=True)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    script = db.Column(db.Text, nullable=True)  # for the command scripts
    attack_power = db.Column(db.Integer, default=0, nullable=False)


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Relationship to reference the actual item
    item = db.relationship('Item', backref='inventory_instances', lazy=True)


class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    health = db.Column(db.Integer, default=100, nullable=False)
    attack = db.Column(db.Integer, default=10, nullable=False)
    defense = db.Column(db.Integer, default=5, nullable=False)
    script = db.Column(db.Text, nullable=True)  # for the command scripts or interactions

class GameContext(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    
    # Relationship to manage entity instances in this game context
    entities = db.relationship('EntityInstance', backref='game_context', lazy=True)

class EntityInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    game_context_id = db.Column(db.Integer, db.ForeignKey('game_context.id'), nullable=False)
    
    current_health = db.Column(db.Integer, nullable=False)
    # Add other attributes as needed (e.g., current_attack, current_defense)
    
    # Relationship to reference the base entity
    base_entity = db.relationship('Entity', backref='instances', lazy=True)



class GameMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', back_populates='messages')
