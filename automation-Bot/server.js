
import express from 'express';
import models from './models/index.js';
import transactionRoutes from './routes/transactionRoutes.js';

const app = express();
app.use(express.json());
app.use('/api/transactions', transactionRoutes);

async function start() {
    await models.sequelize.authenticate();
    console.log('PostgreSQL connected successfully.');

    await models.sequelize.sync();
    console.log('All SmartSpend AI models synchronized.');

    const port = Number(process.env.PORT) || 5000;
    app.listen(port, () => {
        console.log(`SmartSpend AI server listening on port ${port}.`);
    });
}

start().catch((error) => {
    console.error('Server startup failed:', error);
    process.exitCode = 1;
});
