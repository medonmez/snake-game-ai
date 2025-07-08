from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
import sqlite3
import json
from ai_model import SnakeAIAgent
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize AI agent
ai_agent = SnakeAIAgent()

# AI Statistics
ai_stats = {
    'games_played': 0,
    'ai_high_score': 0,
    'total_score': 0,
    'scores': [],
    'rewards': [],
    'current_game_rewards': [],
    'current_game_total_reward': 0
}

# Store previous state for training
previous_state = None
previous_action = None
moves_counter = 0  # Counter for total moves

def get_state_representation(data):
    """Convert game state to AI input format using 9x9 vision matrix"""
    if not data or 'snake_position' not in data or 'food_position' not in data:
        # Return default state if data is invalid
        return np.concatenate([
            np.zeros(81),  # Empty 9x9 vision
            np.array([1, 0, 0, 0]),  # Default direction (right)
            np.array([0, 0, 0, 0]),  # Default food direction (no direction)
        ])
    
    snake_pos = data['snake_position']
    food_pos = data['food_position']
    direction = data.get('direction', 'right')
    grid_size = 12  # Updated from 20 to 12
    
    if not snake_pos:
        return np.concatenate([
            np.zeros(81),  # Empty 9x9 vision
            np.array([1, 0, 0, 0]),  # Default direction (right)
            np.array([0, 0, 0, 0]),  # Default food direction (no direction)
        ])
    
    # Get head position
    head = snake_pos[0]
    
    # Create 9x9 vision matrix centered on snake's head
    vision = np.zeros(81)  # Flattened 9x9 matrix
    
    # Calculate vision matrix bounds
    vision_start_x = head[0] - 4
    vision_start_y = head[1] - 4
    
    # Fill the vision matrix
    for i in range(9):
        for j in range(9):
            world_x = vision_start_x + j
            world_y = vision_start_y + i
            idx = i * 9 + j  # Index in flattened vision array
            
            # Check if position is out of bounds (wall)
            if (world_x < 0 or world_x >= grid_size or 
                world_y < 0 or world_y >= grid_size):
                vision[idx] = -1.0  # Wall
            # Check if position has food
            elif [world_x, world_y] == food_pos:
                vision[idx] = 1.0  # Food
            # Check if position has snake body
            elif [world_x, world_y] in snake_pos:
                vision[idx] = -0.5  # Snake body
            else:
                vision[idx] = 0.0  # Empty space
    
    # Current direction one-hot encoding
    current_direction = np.zeros(4)
    if direction == 'up':
        current_direction[0] = 1
    elif direction == 'right':
        current_direction[1] = 1
    elif direction == 'down':
        current_direction[2] = 1
    elif direction == 'left':
        current_direction[3] = 1
    
    # Food direction relative to snake head
    food_direction = np.zeros(4)  # [up, right, down, left]
    if head and food_pos:
        dx = food_pos[0] - head[0]
        dy = food_pos[1] - head[1]
        
        # Set vertical direction
        if dy < 0:  # Food is above
            food_direction[0] = abs(dy)  # Up with magnitude
        elif dy > 0:  # Food is below
            food_direction[2] = abs(dy)  # Down with magnitude
            
        # Set horizontal direction
        if dx > 0:  # Food is to the right
            food_direction[1] = abs(dx)  # Right with magnitude
        elif dx < 0:  # Food is to the left
            food_direction[3] = abs(dx)  # Left with magnitude
    
    # Combine all features
    return np.concatenate([
        vision,  # 81 values for 9x9 vision
        current_direction,  # 4 values for direction
        food_direction,  # 4 values for food direction
    ])

def get_action_from_direction(current_direction, ai_action):
    """Convert AI action to game direction"""
    directions = ['up', 'right', 'down', 'left']
    current_idx = directions.index(current_direction)
    
    if ai_action == 0:  # straight
        return current_direction
    elif ai_action == 1:  # right turn
        return directions[(current_idx + 1) % 4]
    else:  # left turn
        return directions[(current_idx - 1) % 4]

def emit_ai_stats():
    """Emit current AI statistics to frontend"""
    average_score = ai_stats['total_score'] / ai_stats['games_played'] if ai_stats['games_played'] > 0 else 0
    emit('ai_stats_update', {
        'games_played': ai_stats['games_played'],
        'ai_high_score': ai_stats['ai_high_score'],
        'average_score': average_score,
        'exploration_rate': ai_agent.epsilon,
        'scores': ai_stats['scores'],
        'rewards': ai_stats['current_game_rewards'],
        'total_reward': ai_stats['current_game_total_reward']
    })

def debug_print_vision(vision_array, current_direction, food_direction):
    """Print a visual representation of the 9x9 vision matrix and other inputs"""
    print("\n=== AI Input Debug ===")
    
    # Print Vision Matrix
    print("\nVision Matrix (9x9):")
    print("-" * 37)  # Border
    for i in range(9):
        print("|", end=" ")
        for j in range(9):
            val = vision_array[i * 9 + j]
            if val == -1.0:
                symbol = "W"  # Wall
            elif val == 1.0:
                symbol = "F"  # Food
            elif val == -0.5:
                symbol = "S"  # Snake
            else:
                symbol = "."  # Empty
            print(f"{symbol:2}", end=" ")
        print("|")
    print("-" * 37)  # Border
    
    # Print Current Direction Vector
    print("\nCurrent Direction Vector [up, right, down, left]:")
    print(f"[{', '.join([f'{x:.1f}' for x in current_direction])}]")
    
    # Print Food Direction Vector
    print("\nFood Direction Vector [up, right, down, left]:")
    print(f"[{', '.join([f'{x:.1f}' for x in food_direction])}]")
    
    print("\n===================")

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected'})
    emit_ai_stats()  # Send initial stats

@socketio.on('game_state')
def handle_game_state(data):
    global previous_state, previous_action, moves_counter
    
    # Increment moves counter
    moves_counter += 1
    
    # Add total reward to the game state data
    data['total_reward'] = ai_stats['current_game_total_reward']
    
    # Convert game state to AI input format
    current_state = get_state_representation(data)
    
    # Debug print all inputs
    vision_matrix = current_state[:81]  # First 81 values are the vision matrix
    current_direction_vector = current_state[81:85]  # Next 4 values are current direction
    food_direction_vector = current_state[85:]  # Last 4 values are food direction
    debug_print_vision(vision_matrix, current_direction_vector, food_direction_vector)
    
    current_score = data.get('score', 0)
    
    # Train the model if we have a previous state
    if previous_state is not None and previous_action is not None:
        # Check if game is over
        is_game_over = data.get('game_over', False)
        
        # Train the model
        reward = ai_agent.train(
            previous_state,
            previous_action,
            current_state,
            current_score,
            is_game_over
        )
        
        # Track reward
        ai_stats['current_game_rewards'].append(reward)
        ai_stats['current_game_total_reward'] += reward
        emit_ai_stats()
        
        print(f"Reward: {reward:.2f}, Score: {current_score}")
    
    # Get AI decision for current state
    action = ai_agent.act(current_state)
    
    # Store current state and action for next training step
    previous_state = current_state
    previous_action = action
    
    # Convert AI action to game direction
    new_direction = get_action_from_direction(data.get('direction', 'right'), action)
    
    # Send decision back to frontend
    emit('ai_decision', {'action': new_direction})

@socketio.on('game_over')
def handle_game_over(data):
    global previous_state, previous_action, moves_counter
    
    if previous_state is not None and previous_action is not None:
        # Final training step with game over state
        final_state = get_state_representation(data)
        current_score = data.get('score', 0)
        
        # Train with game over
        reward = ai_agent.train(
            previous_state,
            previous_action,
            final_state,
            current_score,
            True  # game over
        )
        
        # Update statistics
        ai_stats['games_played'] += 1
        ai_stats['total_score'] += current_score
        ai_stats['scores'].append(current_score)
        if current_score > ai_stats['ai_high_score']:
            ai_stats['ai_high_score'] = current_score
        
        # Add final reward
        ai_stats['current_game_rewards'].append(reward)
        ai_stats['current_game_total_reward'] += reward
        ai_stats['rewards'].extend(ai_stats['current_game_rewards'])
        
        # Update epsilon after game ends
        ai_agent.update_epsilon()
        
        # Emit final stats before reset
        emit_ai_stats()
        
        # Reset current game stats
        ai_stats['current_game_rewards'] = []
        ai_stats['current_game_total_reward'] = 0
        
        print(f"Game Over - Final Reward: {reward:.2f}, Final Score: {current_score}")
    
    # Reset previous state, action and moves counter
    previous_state = None
    previous_action = None
    moves_counter = 0

@socketio.on('disconnect')
def handle_disconnect():
    global previous_state, previous_action
    previous_state = None
    previous_action = None
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 