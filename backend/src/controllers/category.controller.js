import category from "../models/category.model.js";
import {Op, UniqueConstraintError } from "sequelize";

const isDuplicate = (error) => error instanceof UniqueConstraintError;

// GET /api/v1/categories?type=expense

const getCategories = async (req, res) => {
  try {
    const filter = {
      [Op.or]: [
        { userId: null }, // System categories
        { userId: req.user.id }, // User-specific categories
      ],
    };
    if (["income", "expense"].includes(req.query.type)) {
      filter.type = req.query.type;
    }
    const categories = await category.findAll({
      where: filter,
      order: [
        ["is_system", "DESC"],
        ["name", "ASC"],
      ],
      raw: true,
    });
    res.json({ success: true, count: categories.length, data: categories });
  } catch (err) {
    res
      .status(500)
      .json({ success: false, message: "Could not fetch categories" });
  }
};

export default {
  getCategories,
};