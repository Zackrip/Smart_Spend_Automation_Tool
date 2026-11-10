import { DataTypes } from "sequelize";
import sequelize from "../../../automation-Bot/config/database.js";

const User = sequelize.define(
  "User",
  {
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
    },

    firstName: {
      type: DataTypes.STRING(100),
      allowNull: false,
    },

    lastName: {
      type: DataTypes.STRING(100),
      allowNull: true,
    },

    email: {
      type: DataTypes.STRING(255),
      allowNull: false,
      unique: true,
      validate: {
        isEmail: true,
      },
    },

    passwordHash: {
      type: DataTypes.TEXT,
      allowNull: false,
      field: "password_hash",
    },

    currency: {
      type: DataTypes.STRING(3),
      defaultValue: "INR",
    },
  },
  {
    tableName: "users",
    underscored: true,
    timestamps: true,
  },
);

export default User;
