import express from 'express';
import authRoutes from './routes/auth.route.js';

const app = express();
app.use(express.json());

// auth routes
app.use('/api/auth/v1', authRoutes);

app.get('/', (req, res) => {
  res.send('Hello, World!');
});




export default app;