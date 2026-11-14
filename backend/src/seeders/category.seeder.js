
import Category from "../models/category.model.js";

const defaultCategories = [
  // Expense categories
  { name: "Food", type: "expense", icon: "🍔" },
  { name: "Transport", type: "expense", icon: "🚗" },
  { name: "Shopping", type: "expense", icon: "🛍️" },
  { name: "Bills", type: "expense", icon: "💡" },
  { name: "Entertainment", type: "expense", icon: "🎮" },
  { name: "Health", type: "expense", icon: "🏥" },
  { name: "Education", type: "expense", icon: "📚" },
  { name: "Rent", type: "expense", icon: "🏠" },
  { name: "Travel", type: "expense", icon: "✈️" },
  { name: "Other", type: "expense", icon: "📦" },

  // Income categories
  { name: "Salary", type: "income", icon: "💼" },
  { name: "Freelance", type: "income", icon: "💻" },
  { name: "Business", type: "income", icon: "🏢" },
  { name: "Investment", type: "income", icon: "📈" },
  { name: "Gift", type: "income", icon: "🎁" },
  { name: "Other", type: "income", icon: "💰" },
];

export const seedCategories = async () => {
  try {
    for (const item of defaultCategories) {
      await Category.findOrCreate({
        where: {
          userId: null,
          name: item.name,
          type: item.type,
        },
        defaults: {
          ...item,
          userId: null,
          isSystem: true,
        },
      });
    }

    console.log("Default categories seeded successfully.");
  } catch (error) {
    console.error("Category seeding failed:", error.message);
    throw error;
  }
};
