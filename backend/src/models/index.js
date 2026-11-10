
import sequelize from '../config/database.js';
// Import all models
import User from './User.js';
import Account from './account.js';
import Category from './Category.js';
import Transaction from './Transaction.js';
import Budget from './budget.js';
import SavingsGoal from './SavingsGoal.js';
import RecurringPayment from './RecurringPayment.js';
import FinancialInsight from './FinancialInsight.js';
import AiConversation from './AiConversation.js';
import AiMessage from './AiMessage.js';

// USER - ACCOUNT
User.hasMany(Account, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
Account.belongsTo(User, {
    foreignKey: 'userId'
});
// USER - CATEGORY
User.hasMany(Category, {
    foreignKey: 'userId'
});
Category.belongsTo(User, {
    foreignKey: 'userId'
});
// USER - TRANSACTION
User.hasMany(Transaction, {
    foreignKey: 'userId'
});
Transaction.belongsTo(User, {
    foreignKey: 'userId'
});
// ACCOUNT - TRANSACTION
Account.hasMany(Transaction, {
    foreignKey: 'accountId'
});
Transaction.belongsTo(Account, {
    foreignKey: 'accountId'
});
// CATEGORY - TRANSACTION
Category.hasMany(Transaction, {
    foreignKey: 'categoryId'
});
Transaction.belongsTo(Category, {
    foreignKey: 'categoryId'
});
// USER - BUDGET
User.hasMany(Budget, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
Budget.belongsTo(User, {
    foreignKey: 'userId'
});
// CATEGORY - BUDGET
Category.hasMany(Budget, {
    foreignKey: 'categoryId'
});
Budget.belongsTo(Category, {
    foreignKey: 'categoryId'
});
// USER - SAVINGS GOAL
User.hasMany(SavingsGoal, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
SavingsGoal.belongsTo(User, {
    foreignKey: 'userId'
});
// USER - RECURRING PAYMENT
User.hasMany(RecurringPayment, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
RecurringPayment.belongsTo(User, {
    foreignKey: 'userId'
});
// CATEGORY - RECURRING PAYMENT
Category.hasMany(RecurringPayment, {
    foreignKey: 'categoryId'
});
RecurringPayment.belongsTo(Category, {
    foreignKey: 'categoryId'
});
// USER - FINANCIAL INSIGHT
User.hasMany(FinancialInsight, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
FinancialInsight.belongsTo(User, {
    foreignKey: 'userId'
});
// USER - AI CONVERSATION
User.hasMany(AiConversation, {
    foreignKey: 'userId',
    onDelete: 'CASCADE'
});
AiConversation.belongsTo(User, {
    foreignKey: 'userId'
});
// AI CONVERSATION - AI MESSAGE
AiConversation.hasMany(AiMessage, {
    foreignKey: 'conversationId',
    onDelete: 'CASCADE'
});
AiMessage.belongsTo(AiConversation, {
    foreignKey: 'conversationId'
});
// Export all models and the database connection
export default {
    sequelize,
    User,
    Account,
    Category,
    Transaction,
    Budget,
    SavingsGoal,
    RecurringPayment,
    FinancialInsight,
    AiConversation,
    AiMessage
};
