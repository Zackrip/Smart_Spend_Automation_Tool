import express from 'express';
import authRoutes from './routes/auth.route.js';
import "../src/models/index.model.js";
import categoryRoutes from './routes/category.route.js';
import transactionRoutes from './routes/transaction.route.js';

const app = express();
app.use(express.json());

// auth routes
app.use('/api/v1/auth', authRoutes);

// category routes
app.use('/api/v1/categories', categoryRoutes);

// transaction routes
app.use('/api/v1/transactions', transactionRoutes);


app.get('/', (req, res) => {
  res.send('Hello, World!');
});




export default app;