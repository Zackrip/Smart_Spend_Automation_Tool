import models from "../models/index.js";

const {
  sequelize, User, Account, Category, Transaction, Budget,
  SavingsGoal, RecurringPayment, FinancialInsight,
  AiConversation, AiMessage
} = models;

async function verify() {
  try {
    await sequelize.authenticate();
    const counts = await Promise.all([
      User.count(),
      Account.count(),
      Category.count(),
      Transaction.count(),
      Budget.count(),
      SavingsGoal.count(),
      RecurringPayment.count(),
      FinancialInsight.count(),
      AiConversation.count(),
      AiMessage.count()
    ]);

    const labels = [
      "users", "accounts", "categories", "transactions", "budgets",
      "savings_goals", "recurring_payments", "financial_insights",
      "ai_conversations", "ai_messages"
    ];

    console.log("\nCurrent row counts (includes any existing records):");
    labels.forEach((label, index) => console.log(`${label}: ${counts[index]}`));

    const anomalyDemo = await Transaction.findOne({
      where: {
        description: "Demo groceries expense 2026-06"
      }
    });
    console.log(
      "\nExample June grocery transaction found:",
      anomalyDemo ? "yes (at least one matching row)" : "no"
    );
  } catch (error) {
    console.error("Verification failed:", error);
    process.exitCode = 1;
  } finally {
    await sequelize.close();
  }
}

verify();
