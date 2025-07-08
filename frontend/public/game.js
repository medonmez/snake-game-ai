class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.gridSize = 50;
        this.snake = [{x: 5, y: 5}];
        this.food = this.generateFood();
        this.direction = 'right';
        this.score = 0;
        this.highScore = parseInt(localStorage.getItem('snakeHighScore')) || 0;
        this.gameSpeed = 200;
        this.normalSpeed = 200;
        this.fastSpeed = 50;
        this.isFastMode = false;
        this.gameLoop = null;
        this.isGameRunning = false;
        this.isGameOver = false;
        this.activeKeys = new Set();
        this.isAIMode = false;
        
        // Initialize Socket.IO connection
        this.socket = io('http://localhost:5000');
        this.setupSocketEvents();
        
        this.setupEventListeners();
        this.setupDarkMode();
        this.updateHighScoreDisplay();
        
        // Initialize charts after a short delay to ensure DOM is ready
        setTimeout(() => this.initializeCharts(), 100);
        
        this.draw();
    }

    initializeCharts() {
        try {
            const chartConfig = {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                elements: {
                    line: {
                        tension: 0.2
                    },
                    point: {
                        radius: 0
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#fff',
                            font: {
                                size: 10
                            },
                            maxTicksLimit: 5
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#fff',
                            font: {
                                size: 10
                            },
                            maxTicksLimit: 5
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                layout: {
                    padding: 5
                }
            };

            // Score Chart
            const scoreCtx = document.getElementById('scoreChart');
            if (scoreCtx) {
                this.scoreChart = new Chart(scoreCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Game Scores',
                            data: [],
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            fill: true,
                            borderWidth: 1.5
                        }]
                    },
                    options: {
                        ...chartConfig,
                        scales: {
                            ...chartConfig.scales,
                            y: {
                                ...chartConfig.scales.y,
                                title: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            }

            // Reward Chart
            const rewardCtx = document.getElementById('rewardChart');
            if (rewardCtx) {
                this.rewardChart = new Chart(rewardCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Rewards',
                            data: [],
                            borderColor: '#2196F3',
                            backgroundColor: 'rgba(33, 150, 243, 0.1)',
                            fill: true,
                            borderWidth: 1.5
                        }]
                    },
                    options: {
                        ...chartConfig,
                        scales: {
                            ...chartConfig.scales,
                            y: {
                                ...chartConfig.scales.y,
                                beginAtZero: false,
                                title: {
                                    display: false
                                }
                            }
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }

    updateCharts(scores, rewards) {
        try {
            if (this.scoreChart) {
                const scoreLabels = Array.from({length: scores.length}, (_, i) => i + 1);
                this.scoreChart.data.labels = scoreLabels;
                this.scoreChart.data.datasets[0].data = scores;
                this.scoreChart.update('none');
            }

            if (this.rewardChart && rewards.length > 0) {
                const rewardLabels = Array.from({length: rewards.length}, (_, i) => i + 1);
                this.rewardChart.data.labels = rewardLabels;
                this.rewardChart.data.datasets[0].data = rewards;
                this.rewardChart.update('none');
            }
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to AI server');
        });

        this.socket.on('ai_decision', (data) => {
            if (this.isAIMode && this.isGameRunning) {
                this.handleAIDecision(data.action);
            }
        });

        this.socket.on('ai_stats_update', (data) => {
            // Update statistics display
            document.getElementById('gamesPlayed').textContent = data.games_played;
            document.getElementById('aiHighScore').textContent = data.ai_high_score;
            document.getElementById('averageScore').textContent = data.average_score.toFixed(2);
            document.getElementById('explorationRate').textContent = data.exploration_rate.toFixed(3);
            document.getElementById('totalReward').textContent = data.total_reward.toFixed(2);

            // Update charts
            this.updateCharts(data.scores, data.rewards);
        });
    }

    handleAIDecision(action) {
        // Convert AI action to direction
        const newDirection = action;
        
        // Validate the direction change
        const opposites = {
            'up': 'down',
            'down': 'up',
            'left': 'right',
            'right': 'left'
        };
        
        if (this.direction !== opposites[newDirection]) {
            this.direction = newDirection;
            this.highlightKey(newDirection);
        }
    }

    sendGameState() {
        if (this.isAIMode && this.isGameRunning) {
            const gameState = {
                snake_position: this.snake.map(pos => [pos.x, pos.y]),
                food_position: [this.food.x, this.food.y],
                score: this.score,
                direction: this.direction,
                game_over: false
            };
            this.socket.emit('game_state', gameState);
        }
    }

    updateHighScoreDisplay() {
        document.getElementById('highScore').textContent = this.highScore;
        document.getElementById('overlayHighScore').textContent = this.highScore;
    }

    updateHighScore() {
        if (this.score > this.highScore) {
            this.highScore = this.score;
            localStorage.setItem('snakeHighScore', this.highScore);
            this.updateHighScoreDisplay();
            return true;
        }
        return false;
    }

    highlightKey(keyName) {
        const keyElement = document.querySelector(`.arrow-key.${keyName}`);
        if (keyElement) {
            keyElement.classList.add('active');
            setTimeout(() => {
                keyElement.classList.remove('active');
            }, 200);
        }
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (this.isGameOver) return;

            let keyPressed = '';
            switch(e.key) {
                case 'ArrowUp': keyPressed = 'up'; break;
                case 'ArrowDown': keyPressed = 'down'; break;
                case 'ArrowLeft': keyPressed = 'left'; break;
                case 'ArrowRight': keyPressed = 'right'; break;
                default: return;
            }

            this.highlightKey(keyPressed);

            if (!this.isGameRunning) {
                this.start();
                document.getElementById('playButton').textContent = 'Restart Game';
            }
            
            if (!this.isGameRunning || this.isAIMode) return;
            
            switch(keyPressed) {
                case 'up':
                    if (this.direction !== 'down') this.direction = 'up';
                    break;
                case 'down':
                    if (this.direction !== 'up') this.direction = 'down';
                    break;
                case 'left':
                    if (this.direction !== 'right') this.direction = 'left';
                    break;
                case 'right':
                    if (this.direction !== 'left') this.direction = 'right';
                    break;
            }
        });

        // Play button
        const playButton = document.getElementById('playButton');
        playButton.addEventListener('click', () => {
            if (!this.isGameRunning) {
                this.start();
                playButton.textContent = 'Restart Game';
            } else {
                this.reset();
            }
        });

        // AI Mode toggle
        const aiModeToggle = document.getElementById('aiModeToggle');
        aiModeToggle.addEventListener('click', () => {
            this.isAIMode = !this.isAIMode;
            aiModeToggle.textContent = `AI Mode: ${this.isAIMode ? 'On' : 'Off'}`;
            if (this.isAIMode && this.isGameRunning) {
                this.sendGameState();
            }
        });

        // Speed toggle
        const speedToggle = document.getElementById('speedToggle');
        speedToggle.addEventListener('click', () => {
            if (!this.isAIMode) return; // Only allow speed toggle in AI mode
            this.isFastMode = !this.isFastMode;
            speedToggle.textContent = `Fast Mode: ${this.isFastMode ? 'On' : 'Off'}`;
            this.gameSpeed = this.isFastMode ? this.fastSpeed : this.normalSpeed;
            
            // Restart the game loop with new speed if game is running
            if (this.isGameRunning) {
                clearInterval(this.gameLoop);
                this.gameLoop = setInterval(() => this.update(), this.gameSpeed);
            }
        });

        // Restart button in game over overlay
        const restartButton = document.getElementById('restartButton');
        restartButton.addEventListener('click', () => {
            this.hideGameOver();
            this.reset();
            this.start();
        });
    }

    setupDarkMode() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        darkModeToggle.addEventListener('click', () => {
            const isDarkMode = document.body.classList.toggle('dark-mode');
            darkModeToggle.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
        });
    }

    showGameOver() {
        this.isGameOver = true;
        const overlay = document.getElementById('gameOverOverlay');
        const finalScore = document.getElementById('finalScore');
        finalScore.textContent = this.score;
        
        // Check for new high score
        const isNewHighScore = this.updateHighScore();
        if (isNewHighScore) {
            finalScore.style.color = 'var(--highlight-color)';
            finalScore.textContent += ' (New High Score!)';
        } else {
            finalScore.style.color = 'white';
        }
        
        // Only show overlay if not in AI mode
        if (!this.isAIMode) {
            overlay.classList.remove('hidden');
        }
    }

    hideGameOver() {
        this.isGameOver = false;
        const overlay = document.getElementById('gameOverOverlay');
        overlay.classList.add('hidden');
    }

    generateFood() {
        let newFood;
        do {
            newFood = {
                x: Math.floor(Math.random() * 12),
                y: Math.floor(Math.random() * 12)
            };
        } while (this.isPositionOnSnake(newFood)); // Keep generating until food is not on snake
        return newFood;
    }

    isPositionOnSnake(position) {
        return this.snake.some(segment => 
            segment.x === position.x && segment.y === position.y
        );
    }

    update() {
        const head = {...this.snake[0]};

        switch(this.direction) {
            case 'up': head.y--; break;
            case 'down': head.y++; break;
            case 'left': head.x--; break;
            case 'right': head.x++; break;
        }

        // Check collision with walls
        if (head.x < 0 || head.x >= 12 ||
            head.y < 0 || head.y >= 12) {
            this.gameOver();
            return;
        }

        // Check collision with self
        if (this.snake.some(segment => segment.x === head.x && segment.y === head.y)) {
            this.gameOver();
            return;
        }

        this.snake.unshift(head);

        // Check if food is eaten
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            document.getElementById('score').textContent = this.score;
            this.food = this.generateFood();
        } else {
            this.snake.pop();
        }

        // Send game state to AI if in AI mode
        this.sendGameState();

        this.draw();
    }

    draw() {
        const isDarkMode = document.body.classList.contains('dark-mode');
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw snake
        this.ctx.fillStyle = isDarkMode ? '#6ECF70' : '#4CAF50';
        this.snake.forEach(segment => {
            this.ctx.fillRect(
                segment.x * this.gridSize,
                segment.y * this.gridSize,
                this.gridSize - 2,
                this.gridSize - 2
            );
        });

        // Draw food
        this.ctx.fillStyle = isDarkMode ? '#FF7043' : '#FF5722';
        this.ctx.fillRect(
            this.food.x * this.gridSize,
            this.food.y * this.gridSize,
            this.gridSize - 2,
            this.gridSize - 2
        );
    }

    gameOver() {
        clearInterval(this.gameLoop);
        this.isGameRunning = false;
        document.getElementById('playButton').textContent = 'Play Game';
        
        // Send game over state to AI
        if (this.isAIMode) {
            const gameState = {
                snake_position: this.snake.map(pos => [pos.x, pos.y]),
                food_position: [this.food.x, this.food.y],
                score: this.score,
                direction: this.direction,
                game_over: true
            };
            this.socket.emit('game_over', gameState);
            
            // Automatically restart after a short delay in AI mode
            setTimeout(() => {
                this.reset();
                this.start();
            }, 1000);  // 1 second delay before restart
        }
        
        this.showGameOver();
    }

    reset() {
        this.hideGameOver();
        this.snake = [{x: 5, y: 5}];
        this.direction = 'right';
        this.score = 0;
        document.getElementById('score').textContent = this.score;
        this.food = this.generateFood();
        this.isGameRunning = false;
        clearInterval(this.gameLoop);
        this.draw();
    }

    start() {
        this.hideGameOver();
        this.isGameRunning = true;
        this.gameLoop = setInterval(() => this.update(), this.gameSpeed);
    }
}

// Initialize the game
const game = new SnakeGame(); 