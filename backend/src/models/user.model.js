import { DataTypes } from "sequelize";
import {sequelize} from "../configs/database.config.js";

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
      field: "first_name",
    },

    lastName: {
      type: DataTypes.STRING(100),
      allowNull: true,
      field: "last_name",
    },

    MobileNo: {
      type: DataTypes.STRING(10),
      allowNull: false,
      unique: true,
      field: "mobile_no",
    },

    MobileNo: {
      type: DataTypes.STRING(10),
      allowNull: false,
      unique: true,
    },

    MobileNo: {
      type: DataTypes.STRING(10),
      allowNull: false,
      unique: true,
    },

    MobileNo: {
      type: DataTypes.STRING(10),
      allowNull: false,
      unique: true,
    },

    email: {
      type: DataTypes.STRING(255),
      allowNull: true,
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
