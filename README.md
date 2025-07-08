# AI Snake Game - Reinforcement Learning

A modern implementation of the classic Snake game with an AI learning component that learns to play through reinforcement learning using PyTorch.

##  Project Overview

This project combines a playable Snake game with an intelligent AI agent that learns to play through trial and error using reinforcement learning techniques. The AI uses a 9x9 vision matrix to understand the game state and makes decisions based on neural network predictions.

## ️ Architecture

The project consists of two main components:

### Frontend (`/frontend`)
- **Technology Stack:**
  - Node.js with Express.js server
  - HTML5 Canvas for game rendering
  - WebSocket communication for real-time AI visualization
  - Chart.js for performance metrics visualization
  - Responsive design with dark/light mode support

### Backend (`/backend`)
- **Technology Stack:**
  - Python with Flask for REST endpoints
  - Flask-SocketIO for real-time communication
  - PyTorch for AI/ML implementation
  - SQLite for storing game states and AI progress
  - NumPy for mathematical operations

## ✨ Key Features

###  Classic Snake Game
- Responsive arrow key controls
- Real-time score tracking
- High score persistence
- Progressive difficulty (speed increases with score)
- Game over detection (wall collision, self-collision)
- Visual game over overlay

### 🤖 AI Learning Component
- **Reinforcement Learning Implementation:**
  - Deep Q-Network (DQN) with PyTorch
  - 9x9 vision matrix for state representation
  - Experience replay for stable learning
  - Epsilon-greedy exploration strategy
- **Real-time Visualization:**
  - Live AI statistics dashboard
  - Score history charts
  - Reward tracking
  - Exploration rate monitoring
- **Performance Metrics:**
  - Games played counter
  - AI high score tracking
  - Average score calculation
  - Total reward accumulation

### 🎛️ Interactive Controls
- Toggle between manual and AI mode
- Speed control (normal/fast mode)
- Dark/light theme switching
- Real-time AI statistics display

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd snake-game-ai
   ```

2. **Set up Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

#### Option 1: Manual Start
1. **Start Backend Server**
   ```bash
   cd backend
   python app.py
   ```
   The backend will run on `http://localhost:5000`

2. **Start Frontend Server**
   ```bash
   cd frontend
   npm start
   ```
   The frontend will run on `http://localhost:8080`

#### Option 2: Windows PowerShell Script
```powershell
.\start_app.ps1
```
This script automatically starts both servers and opens the application in your default browser.

### Usage

1. **Manual Play:**
   - Click "Play Game" to start
   - Use arrow keys to control the snake
   - Try to eat food and avoid walls/yourself

2. **AI Mode:**
   - Toggle "AI Mode" to watch the AI learn
   - Monitor the dashboard for real-time statistics
   - Watch the AI improve over time

3. **Dashboard Features:**
   - View games played and high scores
   - Monitor exploration rate and average scores
   - Analyze performance through interactive charts

## 🧠 AI Implementation Details

### State Representation
The AI uses a comprehensive state representation:
- **9x9 Vision Matrix:** 81 values representing the snake's immediate surroundings
- **Direction Encoding:** 4 values for current movement direction
- **Food Direction:** 4 values indicating food location relative to snake head

### Neural Network Architecture
- Input layer: 89 neurons (81 vision + 4 direction + 4 food direction)
- Hidden layers: Fully connected layers with ReLU activation
- Output layer: 3 neurons (straight, left turn, right turn)

### Learning Algorithm
- **Deep Q-Learning** with experience replay
- **Epsilon-greedy** exploration strategy
- **Reward System:**
  - +1 for eating food
  - -1 for collision
  - Small negative reward for each move to encourage efficiency

## 📊 Performance Monitoring

The application provides comprehensive monitoring:
- Real-time score tracking
- Average performance metrics
- Learning progress visualization
- Reward accumulation tracking
- Exploration rate monitoring

## 🛠️ Development

### Project Structure


