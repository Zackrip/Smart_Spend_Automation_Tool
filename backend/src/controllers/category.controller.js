import category from "../models/category.model.js";
import { Op, UniqueConstraintError } from "sequelize";

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

const createCategory = async (req, res) => {
  try {
    const { name, type, icon } = req.body;

    // Basic validation
    if (!name || !type) {
      return res.status(400).json({
        success: false,
        message: "Category name and type are required",
      });
    }

    if (!["income", "expense"].includes(type)) {
      return res.status(400).json({
        success: false,
        message: "Type must be income or expense",
      });
    }
    const categoryData = await category.create({
      name: name.trim(),
      type,
      icon: icon || null,
      userId: req.user.id,
      isSystem: false,
    });
    res.status(201).json({
      success: true,
      message: "Category created successfully",
      data: categoryData,
    });
  } catch (err) {
    if (isDuplicate(err)) {
      return res.status(409).json({
        success: false,
        message: "You already have a category with this name",
      });
    }
    console.error("Create category error:", err);
    return res
      .status(500)
      .json({ success: false, message: "Could not create category" });
  }
};

export default {
  getCategories,
  createCategory,
};
