from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from models import *
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'mysecretkey'  # You should set this to a random string in a real application
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://wackyschemes:B0nerometrics@localhost/rpg_game_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
limiter = Limiter(app, key_func=get_remote_address)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
def index():
    return redirect(url_for('game'))#render_template('index.html')

### Command List ###
def spawn(tokens, user_id, role, game_id):

    if role != "Gamemaster":
        return ['failure', 'Only Gamemasters can use the spawn command.']

    entity_name = tokens[0]
    entity = Entity.query.filter_by(name=entity_name).first()

    if not entity:
        return ['failure', f"No entity named {entity_name} found."]

    game_context = GameContext.query.filter_by(game_id=game_id).first()

    # Create an EntityInstance for the specific entity in the game context
    entity_instance = EntityInstance(entity_id=entity.id, game_context_id=game_context.id, current_health=entity.health)
    db.session.add(entity_instance)
    db.session.commit()

    # Notify all players in the game session about the new entity
    emit('new_entity', {'entity_name': entity_name, 'current_health': entity.health}, room="game_" + game_id)

    return ['success', f"{entity_name} has been spawned in the game!"]





command_list = {
    'spawn': spawn
}


### Account Session Management Routes ###

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('game'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return f"Hello, {current_user.username}!"


@app.route('/register', methods=['GET'])
def show_register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check if the username is already in use
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already in use. Please choose a different username.', 'danger')
        return redirect(url_for('show_register_page'))

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return redirect(url_for('index'))



### Game Logic ### 

@app.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    if request.method == 'POST':
        if 'create_game' in request.form:
            game_title = request.form['game_title']
            game_password = request.form['game_password']
            
            new_game = Game(title=game_title)
            new_game.set_password(game_password)
            
            db.session.add(new_game)
            db.session.flush()

            # Create a GameContext for the new game
            new_game_context = GameContext(game_id=new_game.id)
            db.session.add(new_game_context)
            
            # Create Gamemaster Player
            gm_player = Player(user_id=current_user.id, game_id=new_game.id, name="Gamemaster", role="Gamemaster")
            db.session.add(gm_player)
            db.session.commit()
            
            return redirect(url_for('game_session', game_id=new_game.id))
        
        elif 'join_game' in request.form:
            game_id = request.form['game_id']
            game_password = request.form['game_password']
            player_name = request.form['player_name']
            game = Game.query.get(game_id)
            
            if game and game.check_password(game_password):
                # Check if user is already part of this game
                existing_player = Player.query.filter_by(user_id=current_user.id, game_id=game.id).first()
                
                if not existing_player:
                    new_player = Player(user_id=current_user.id, game_id=game.id, role="Adventurer", name=player_name)
                    db.session.add(new_player)
                    db.session.commit()
                    
                    return redirect(url_for('game_session', game_id=game.id))
                else:
                    flash('You are already part of this game.', 'warning')
            else:
                flash('Invalid game ID or password.', 'danger')
    
    # Query games associated with the current user
    user_games = db.session.query(Game, Player.role).join(Player).filter(Player.user_id == current_user.id).all()
    
    return render_template('game.html', user_games=user_games)






@app.route('/game_session/<int:game_id>', methods=['GET', 'POST'])
@login_required
def game_session(game_id):
    game = Game.query.get(game_id)
    print(game)
    if not game:
        flash('Game not found.', 'danger')
        return redirect(url_for('game'))
    
    # Check if the current user is a part of this game
    player = Player.query.filter_by(user_id=current_user.id, game_id=game.id).first()
    players = Player.query.filter_by(game_id=game.id).all()
    if not player:
        flash('You are not a part of this game.', 'warning')
        return redirect(url_for('game'))

    if request.method == 'POST':
        # Handle the game command logic here
        message_content = request.form.get('command')
        new_message = GameMessage(game_id=game.id, player_id=player.id, content=message_content)
        db.session.add(new_message)
        db.session.commit()

    game_context = GameContext.query.filter_by(game_id=game.id).first()
    entity_instances = []
    if game_context:
        entity_instances = EntityInstance.query.filter_by(game_context_id=game_context.id).all()


    # Retrieve the last n messages
    n = 10  # or however many messages you want
    messages = GameMessage.query.filter_by(game_id=game.id).order_by(GameMessage.timestamp.desc()).limit(n).all()

    return render_template('game_session.html', game=game, player=player, messages=messages, players=players, entity_instances=entity_instances)


@limiter.limit("1 per 3 seconds")
@socketio.on('send_message')
def handle_message(data):
    game_id = data['game_id']
    message_content = data['content']

        # Get the role of the current user in this game session
    player = Player.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    if not player:
        # Emit a failure message back to the user if they're not a player in this game session
        emit('command_response', ['failure', 'You are not a player in this game.'], room=request.sid)
        return

    role = player.role

    tokens = message_content.split()
    command = tokens[0]

    if command in command_list:
        response = command_list[command](tokens[1:], current_user.id, role, game_id)
        if response[0] == 'failure':
            # Send the message only to the issuer
            emit('new_message', {'user': 'System', 'content': response[1]}, room=request.sid)
        else:
            # Send the message to all players in the game
            emit('new_message', {'user': 'System', 'content': response[1]}, room="game_" + game_id)

    # If it's not a command, continue with the usual message sending logic ...

    new_message = GameMessage(game_id=game_id, player_id=current_user.id, content=message_content+" - "+response[1])
    db.session.add(new_message)
    db.session.commit()

    # Emit the new message to all connected clients within the game session
    room = "game_" + game_id
    emit('new_message', {'user': data['user'], 'content': data['content']}, room=room)



@socketio.on('join')
def on_join(data):
    room = "game_" + data['game_id']
    join_room(room)
    
    player = Player.query.filter_by(user_id=current_user.id, game_id=data['game_id']).first()
    if player:
        emit('player_online', {'player_id': player.id}, room=room)
    else:
        return None

@socketio.on('leave')
def on_leave(data):
    room = "game_" + data['game_id']
    leave_room(room)
    
    player = Player.query.filter_by(user_id=current_user.id, game_id=data['game_id']).first()
    if player:
        emit('player_offline', {'player_id': player.id}, room=room)
    else:
        return None


### Customization ###

@app.route('/create_entity', methods=['GET', 'POST'])
@login_required
def create_entity():
    if request.method == 'POST':
        name = request.form.get('name')
        health = request.form.get('health')
        attack = request.form.get('attack')
        defense = request.form.get('defense')
        
        new_entity = Entity(name=name, health=health, attack=attack, defense=defense)
        db.session.add(new_entity)
        db.session.commit()
        
        flash('Entity created successfully!', 'success')
        return redirect(url_for('index'))  # Redirect to a suitable page, maybe a list of all entities

    return render_template('create_entity.html')



### Run App ###

if __name__ == '__main__':
    socketio.run(app,debug=True)
