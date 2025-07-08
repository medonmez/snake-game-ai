import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random

class SnakeAI(nn.Module):
    def __init__(self, grid_size=12, output_size=3):
        super(SnakeAI, self).__init__()
        # Input: 9x9 vision matrix (81) + current direction (4) + food direction (4)
        input_size = 89  # 81 for vision + 4 for current direction + 4 for food direction
        self.dropout_active = False  # Track if dropout should be active
        
        self.layer1 = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(p=0.125)
        )
        
        self.layer2 = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Dropout(p=0.125)
        )

        self.layer3 = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(p=0.125)
        )
        
        self.output = nn.Linear(128, output_size)
        
    def forward(self, x):
        # Handle both single samples and batches
        is_single = len(x.shape) == 1
        if is_single:
            x = x.unsqueeze(0)  # Add batch dimension
        
        # Only use dropout if it's active and model is in training mode
        if not self.dropout_active:
            self.layer1[2].p = 0
            self.layer2[2].p = 0
            self.layer3[2].p = 0
        else:
            self.layer1[2].p = 0.125
            self.layer2[2].p = 0.125
            self.layer3[2].p = 0.125
            
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.output(x)
        
        if is_single:
            x = x.squeeze(0)  # Remove batch dimension
        return x

class SnakeAIAgent:
    def __init__(self):
        self.model = SnakeAI()
        self.target_model = SnakeAI()  # Target network for stable learning
        self.target_model.load_state_dict(self.model.state_dict())
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0003)
        self.memory = deque(maxlen=200000)  # 100000'den 200000'e
        
        self.batch_size = 128  # 64'ten 128'e
        self.gamma = 0.98  # 0.95'ten 0.98'e - uzun vadeli ödüllere daha fazla önem
        self.epsilon = 1.0  # Start with 100% exploration
        self.epsilon_min = 0.01  # 0.01'den 0.001'e
        self.games_played = 0  # Track number of games played
        self.total_games = 200  # 50'den 100'e
        self.target_update = 1024  # Update target network every N steps
        self.steps = 0
        
        # Previous state storage for reward calculation
        self.previous_score = 0
        self.current_game_steps = 0  # Track steps in current game
        
        
    def get_reward(self, state, score, done):
        """Simple reward system with components:
        1. Food reward
        2. Death penalty
        3. Dynamic survival points
        4. Distance to food reward"""
        reward = 0
        self.current_game_steps += 1
        
        # Get food direction from state (last 4 values of state)
        food_direction = state[-4:]  # [up, right, down, left]
        
        # Calculate Manhattan distance from food direction values
        # Vertical distance (up or down) + Horizontal distance (left or right)
        vertical_distance = max(food_direction[0], food_direction[2])  # up or down
        horizontal_distance = max(food_direction[1], food_direction[3])  # right or left
        current_distance = vertical_distance + horizontal_distance
        
        # Add distance-based reward
        reward += 0.05 * (1 / (current_distance + 1))  # More reward when closer
        
        # Reward for eating food
        if score > self.previous_score:
            reward += 15  # Base reward for eating food
            self.previous_score = score
            self.current_game_steps = 0
        
        # Penalty for dying
        if done:
            reward -= 20  # Fixed penalty for death
            self.previous_score = 0
            self.current_game_steps = 0
        
        # Dynamic survival points based on snake length
        if not done:
            # Calculate allowed steps based on snake length (score/10 gives length-1)
            snake_length = (score / 10) + 1  # +1 for initial length
            # Allowed steps increases with snake length: longer snake = more allowed steps
            allowed_steps = 50 + (snake_length * 3)  # Base 50 steps + 3 per length
            
            # Calculate survival reward
            if self.current_game_steps <= allowed_steps:
                # Linear decrease from 0.1 to 0 until allowed_steps
                survival_reward = 0.1 * (1 - self.current_game_steps / allowed_steps)
            else:
                # Linear decrease from 0 to -0.1 after allowed_steps
                extra_steps = self.current_game_steps - allowed_steps
                max_extra_steps = allowed_steps / 2  # Takes another 50% of allowed_steps to reach -0.1
                survival_reward = max(-0.1, -0.1 * (extra_steps / max_extra_steps))
            
            reward += survival_reward
        
        return reward
        
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state):
        """Choose action based on epsilon-greedy policy"""
        if random.random() < self.epsilon:
            return random.randint(0, 2)
        
        state = torch.FloatTensor(state)
        # Set model to eval mode for inference
        self.model.eval()
        with torch.no_grad():
            q_values = self.model(state)
            action = torch.argmax(q_values).item()
        # Set model back to train mode
        self.model.train()
        
        return action
    
    def replay(self):
        """Train the model using experiences from memory"""
        if len(self.memory) < self.batch_size:
            return
        
        # Ensure model is in training mode
        self.model.train()
        self.target_model.eval()
        
        # Sample random batch from memory
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Current Q values
        current_q = self.model(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target model
        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss and update model
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update target network
        self.steps += 1
        if self.steps % self.target_update == 0:
            self.target_model.load_state_dict(self.model.state_dict())
    
    def update_epsilon(self):
        """Update epsilon after each game"""
        self.games_played += 1
        if self.games_played <= self.total_games:
            self.epsilon = max(self.epsilon_min, 1.0 - (self.games_played / self.total_games) * (1.0 - self.epsilon_min))
            # Activate dropout when epsilon reaches minimum
            if self.epsilon <= self.epsilon_min:
                self.model.dropout_active = True
    
    def train(self, state, action, next_state, score, done):
        """Main training function to be called from the game"""
        reward = self.get_reward(state, score, done)
        self.remember(state, action, reward, next_state, done)
        self.replay()
        return reward 