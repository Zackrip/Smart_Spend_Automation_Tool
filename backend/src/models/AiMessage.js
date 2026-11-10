import { DataTypes } from "sequelize";
import sequelize from "../../../automation-Bot/config/database.js";

const AiMessage = sequelize.define(
  "AiMessage",
  {
    id: {
      type: DataTypes.BIGINT,
      primaryKey: true,
      autoIncrement: true,
    },

    conversationId: {
      type: DataTypes.BIGINT,
      allowNull: false,
    },

    role: {
      type: DataTypes.ENUM("user", "assistant", "tool"),
      allowNull: false,
    },

    content: {
      type: DataTypes.TEXT,
      allowNull: false,
    },
  },
  {
    tableName: "ai_messages",
    underscored: true,
    timestamps: true,
    updatedAt: false,
  },
);

export default AiMessage;
