import { DataTypes, Op } from "sequelize";
import crypto from "crypto";
import sequelize from "../config/database.js";
import { TRANSACTION_CONSTANTS } from "../constants/transaction.constant.js";

const Transaction = sequelize.define(
  "Transaction",
  {
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
    },

    userId: {
      type: DataTypes.BIGINT,
      allowNull: false,
    },

    accountId: {
      type: DataTypes.BIGINT,
      allowNull: false,
    },

    categoryId: {
      type: DataTypes.BIGINT,
      allowNull: true,
    },

    amount: {
      type: DataTypes.DECIMAL(12, 2),
      allowNull: false,
      validate: {
        min: 0.01,
      },
    },

    transactionType: {
      type: DataTypes.ENUM(...TRANSACTION_CONSTANTS.TRANSACTION_TYPES),
      allowNull: false,
    },

    paymentMethod: {
      type: DataTypes.ENUM(...TRANSACTION_CONSTANTS.PAYMENT_MODES),
      defaultValue: "other",
      allowNull: false,
    },

    merchant: {
      type: DataTypes.STRING(200),
      allowNull: true,
    },

    description: {
      type: DataTypes.TEXT,
      allowNull: true,
    },

    transactionDate: {
      type: DataTypes.DATE,
      allowNull: false,
    },

    source: {
      type: DataTypes.ENUM(...TRANSACTION_CONSTANTS.SOURCES),
      defaultValue: "manual",
    },
    isRecurring: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: false,
    },
    notes: {
      type: DataTypes.STRING(500),
      allowNull: false,
      defaultValue: "",
    },
    hash: {
      type: DataTypes.STRING(64),
      allowNull: true,
      defaultValue: null,
    },
  },
  {
    tableName: "transactions",
    underscored: true,
    timestamps: true,

    indexes: [
      // Fast listing: newest transactions for one user
      {
        fields: ["user_id", "transaction_date"],
      },

      // Category reports and budget calculations
      {
        fields: ["user_id", "category_id", "transaction_date"],
      },

      // Prevent duplicate automated transactions
      {
        unique: true,
        fields: ["user_id", "hash"],
        where: {
          hash: {
            [Op.ne]: null,
          },
        },
      },
    ],

    hooks: {
      beforeValidate: (transaction) => {
        if (transaction.source !== "manual" && !transaction.hash) {
          const hashInput = [
            transaction.userId,
            transaction.transactionType,
            transaction.amount,
            transaction.transactionDate
              ? new Date(transaction.transactionDate).toISOString()
              : "",
            (transaction.merchant || "").toLowerCase().trim(),
          ].join("|");

          transaction.hash = crypto
            .createHash("sha256")
            .update(hashInput)
            .digest("hex");
        }
      },
    },
  },
);

export default Transaction;
