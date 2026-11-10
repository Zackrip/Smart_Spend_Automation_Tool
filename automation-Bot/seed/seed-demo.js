import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import models from "../models/index.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const data = JSON.parse(
  fs.readFileSync(path.join(__dirname, "seed-data.json"), "utf8")
);

const {
  sequelize, User, Account, Category, Transaction, Budget,
  SavingsGoal, RecurringPayment, FinancialInsight,
  AiConversation, AiMessage
} = models;

const userIds = new Map();
const accountIds = new Map();
const categoryIds = new Map();
const conversationIds = new Map();

const monthDate = (year, monthIndex, day) =>
  new Date(Date.UTC(year, monthIndex, day, 12, 0, 0));

const dateOnly = (year, monthIndex, day) =>
  `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

async function seed() {
  const tx = await sequelize.transaction();

  try {
    // 1. Users: email makes each demo user repeatable across runs.
    for (const item of data.demoUsers) {
      const [record] = await User.findOrCreate({
        where: { email: item.email },
        defaults: {
          firstName: item.firstName,
          lastName: item.lastName,
          email: item.email,
          passwordHash: item.passwordHash,
          currency: item.currency
        },
        transaction: tx
      });
      userIds.set(item.key, record.id);
    }

    // 2. Accounts: identify by user + account name.
    for (const item of data.accounts) {
      const userId = userIds.get(item.userKey);
      const [record] = await Account.findOrCreate({
        where: { userId, accountName: item.accountName },
        defaults: {
          userId,
          accountName: item.accountName,
          accountType: item.accountType,
          institutionName: item.institutionName,
          currency: "INR",
          isActive: true
        },
        transaction: tx
      });
      accountIds.set(item.key, record.id);
    }

    // 3. Categories: global/system categories have userId null.
    for (const item of data.categories) {
      const userId = item.userKey ? userIds.get(item.userKey) : null;
      const [record] = await Category.findOrCreate({
        where: { name: item.name, type: item.type, userId },
        defaults: {
          userId,
          name: item.name,
          type: item.type,
          icon: item.icon,
          isSystem: item.isSystem
        },
        transaction: tx
      });
      categoryIds.set(item.key, record.id);
    }

    // 4. Generate six months of synthetic income and expense transactions.
    const [startYear, startMonth] = data.transactionGeneration.startMonth
      .split("-").map(Number);
    const startMonthIndex = startMonth - 1;

    for (const profile of data.monthlyProfiles) {
      const userId = userIds.get(profile.userKey);
      const accountId = accountIds.get(profile.accountKey);

      for (let offset = 0; offset < data.transactionGeneration.months; offset++) {
        const absoluteMonth = startMonthIndex + offset;
        const year = startYear + Math.floor(absoluteMonth / 12);
        const monthIndex = absoluteMonth % 12;
        const monthLabel = dateOnly(year, monthIndex, 1).slice(0, 7);

        const incomeDate = monthDate(year, monthIndex, data.transactionGeneration.incomeDay);
        const salaryCategoryId = categoryIds.get("salary");
        await Transaction.findOrCreate({
          where: {
            userId, accountId, categoryId: salaryCategoryId,
            transactionType: "income", transactionDate: incomeDate,
            description: `Demo salary ${monthLabel}`
          },
          defaults: {
            userId, accountId, categoryId: salaryCategoryId,
            amount: profile.monthlyIncome,
            transactionType: "income",
            merchant: "Demo Employer",
            description: `Demo salary ${monthLabel}`,
            transactionDate: incomeDate,
            source: data.transactionGeneration.source
          },
          transaction: tx
        });

        const extraIncome = profile.incomeExtra?.freelance || 0;
        if (extraIncome > 0) {
          const freelanceCategoryId = categoryIds.get("freelance");
          const freelanceDate = monthDate(year, monthIndex, 15);
          await Transaction.findOrCreate({
            where: {
              userId, accountId, categoryId: freelanceCategoryId,
              transactionType: "income", transactionDate: freelanceDate,
              description: `Demo freelance income ${monthLabel}`
            },
            defaults: {
              userId, accountId, categoryId: freelanceCategoryId,
              amount: extraIncome,
              transactionType: "income",
              merchant: "Demo Freelance Client",
              description: `Demo freelance income ${monthLabel}`,
              transactionDate: freelanceDate,
              source: data.transactionGeneration.source
            },
            transaction: tx
          });
        }

        for (const [categoryKey, usualAmount] of Object.entries(profile.monthlyExpenses)) {
          const amount = categoryKey === "groceries"
            ? profile.groceryAmountsByMonth[offset]
            : usualAmount;
          const categoryId = categoryIds.get(categoryKey);
          const transactionDate = monthDate(
            year, monthIndex, data.transactionGeneration.expenseDay
          );
          const description = `Demo ${categoryKey} expense ${monthLabel}`;

          await Transaction.findOrCreate({
            where: {
              userId, accountId, categoryId,
              transactionType: "expense", transactionDate, description
            },
            defaults: {
              userId, accountId, categoryId,
              amount,
              transactionType: "expense",
              merchant: `Demo ${categoryKey}`,
              description,
              transactionDate,
              source: data.transactionGeneration.source
            },
            transaction: tx
          });
        }
      }
    }

    // 5. Budgets (one current demo period per configured user/category).
    for (const item of data.budgets) {
      const userId = userIds.get(item.userKey);
      const categoryId = categoryIds.get(item.categoryKey);
      await Budget.findOrCreate({
        where: {
          userId, categoryId, period: "monthly",
          startDate: "2026-06-01"
        },
        defaults: {
          userId, categoryId,
          amountLimit: item.amountLimit,
          period: "monthly",
          startDate: "2026-06-01",
          endDate: "2026-06-30"
        },
        transaction: tx
      });
    }

    // 6. Savings goals.
    for (const item of data.savingsGoals) {
      const userId = userIds.get(item.userKey);
      await SavingsGoal.findOrCreate({
        where: { userId, name: item.name },
        defaults: {
          userId,
          name: item.name,
          targetAmount: item.targetAmount,
          currentAmount: item.currentAmount,
          targetDate: item.targetDate,
          status: item.status
        },
        transaction: tx
      });
    }

    // 7. Recurring payments.
    for (const item of data.recurringPayments) {
      const userId = userIds.get(item.userKey);
      const categoryId = item.categoryKey ? categoryIds.get(item.categoryKey) : null;
      await RecurringPayment.findOrCreate({
        where: { userId, name: item.name },
        defaults: {
          userId, categoryId,
          name: item.name,
          expectedAmount: item.expectedAmount,
          frequency: item.frequency,
          nextDueDate: item.nextDueDate,
          status: item.status
        },
        transaction: tx
      });
    }

    // 8. Example insights (labelled demo; not real predictions).
    for (const item of data.insights) {
      const userId = userIds.get(item.userKey);
      await FinancialInsight.findOrCreate({
        where: { userId, title: item.title },
        defaults: {
          userId,
          insightType: item.insightType,
          title: item.title,
          description: item.description,
          severity: item.severity,
          metadata: item.metadata,
          generatedAt: new Date(),
          isRead: false
        },
        transaction: tx
      });
    }

    // 9. AI conversation and messages.
    for (const item of data.conversations) {
      const userId = userIds.get(item.userKey);
      const [record] = await AiConversation.findOrCreate({
        where: { userId, title: item.title },
        defaults: { userId, title: item.title },
        transaction: tx
      });
      conversationIds.set(item.key, record.id);
    }

    for (const item of data.messages) {
      const conversationId = conversationIds.get(item.conversationKey);
      await AiMessage.findOrCreate({
        where: { conversationId, role: item.role, content: item.content },
        defaults: {
          conversationId,
          role: item.role,
          content: item.content
        },
        transaction: tx
      });
    }

    await tx.commit();

    console.log("\nSmartSpend AI demo seed completed.");
    console.log("Synthetic data covers January–June 2026.");
    console.log("Seed is designed to be repeatable; existing matching demo records are reused.");
    console.log("IMPORTANT: demo users have a placeholder passwordHash and cannot log in.");
    console.log("Do not use this data as real financial data.\n");
  } catch (error) {
    await tx.rollback();
    console.error("Seed failed; transaction rolled back.");
    console.error(error);
    process.exitCode = 1;
  } finally {
    await sequelize.close();
  }
}

seed();
