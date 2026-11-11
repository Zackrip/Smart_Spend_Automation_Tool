import express from 'express';
import authRoutes from './routes/auth.route.js';
import categoryRoutes from './routes/category.route.js';

const app = express();
app.use(express.json());

// auth routes
app.use('/api/auth/v1', authRoutes);

// category routes
app.use('/api/categories/v1', categoryRoutes);

app.get('/', (req, res) => {
  res.send('Hello, World!');
});




export default app;