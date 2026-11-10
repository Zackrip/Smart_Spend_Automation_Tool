
import models from './models/index.js';

async function testDemo() {
    try {
        // 1. Connect to PostgreSQL
        await models.sequelize.authenticate();
        console.log('Database connected!');

        // 2. Create a fictional demo user
        // This is NOT a real password.
        const user = await models.User.create({
            firstName: 'Demo',
            lastName: 'User',
            email: `demo_${Date.now()}@example.com`,
            passwordHash: 'DEMO_HASH_NOT_FOR_LOGIN',
            currency: 'INR'
        });

        console.log('Demo user created:', user.id);

        // 3. Create a cash account
        const account = await models.Account.create({
            userId: user.id,
            accountName: 'Demo Cash Wallet',
            accountType: 'cash',
            currency: 'INR',
            isActive: true
        });

        console.log('Demo account created:', account.id);

        // 4. Create an expense category
        const category = await models.Category.create({
            userId: user.id,
            name: 'Demo Food',
            type: 'expense',
            icon: 'utensils',
            isSystem: false
        });

        console.log('Demo category created:', category.id);

        // 5. Insert a fictional transaction
        const transaction = 
        await models.Transaction.create({
            userId: user.id,
            accountId: account.id,
            categoryId: category.id,
            amount: 250.00,
            transactionType: 'expense',
            merchant: 'Demo Cafe',
            description: 'Sample lunch expense',
            transactionDate: '2026-10-12',
            source: 'manual'
        });
           // Additional test transaction 1
        await models.Transaction.create({
            userId: user.id,
            accountId: account.id,
            categoryId: category.id,
            amount: 120.00,
            transactionType: 'expense',
            merchant: 'Demo Grocery Store',
            description: 'Sample grocery shopping',
            transactionDate: '2026-10-12',
            source: 'manual'
        });

// Additional test transaction 2
        await models.Transaction.create({
            userId: user.id,
            accountId: account.id,
            categoryId: category.id,
            amount: 500.00,
            transactionType: 'income',
            merchant: 'Demo Scholarship',
            description: 'Sample scholarship received',
            transactionDate: '2026-10-12',
            source: 'manual'
        });

console.log('Additional demo transactions created!');


        console.log('Transaction inserted:', transaction.id);

        // 6. Retrieve the transaction from PostgreSQL
        const foundTransaction =
            await models.Transaction.findByPk(transaction.id);

        console.log(
            'Retrieved transaction:',
            foundTransaction?.toJSON()
        );

        // 7. Update the transaction description
        await foundTransaction.update({
            description: 'Updated sample lunch expense'
        });

        console.log(
            'Updated description:',
            foundTransaction.description
        );

        console.log('All demo tests passed!');

    } catch (error) {
        console.error('Demo test failed:', error);
    } finally {
        // Close the database connection
        await models.sequelize.close();
    }
}

testDemo();
