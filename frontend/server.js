const express = require('express');
const path = require('path');
const app = express();

// Middleware to log requests
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

// Handle 404 errors
app.use((req, res) => {
    res.status(404).send('Page not found');
});

// Configuration
const PORT = process.env.PORT || 8080;
const HOST = process.env.HOST || 'localhost';

// Start server
app.listen(PORT, HOST, (err) => {
    if (err) {
        console.error('Error starting server:', err);
        process.exit(1);
    }
    console.log(`Server is running at http://${HOST}:${PORT}`);
    console.log('Press Ctrl+C to stop the server');
}); 