import express from "express";
import {
  createCategorySchema,
  updateCategorySchema,
  validate,
} from "../middlewares/validation.middleware.js";

import categoryController from "../controllers/category.controller.js";
import verifyToken from "../middlewares/auth.middleware.js";

const router = express.Router();

// get all categories or filter by type (income/expense)
router.get("/", verifyToken, categoryController.getCategories);
// create a new category
router.post(
  "/create-category",
  verifyToken,
  validate(createCategorySchema),
  categoryController.createCategory,
);
// update a category by ID
router.put(
  "/update-category/:id",
  verifyToken,
  validate(updateCategorySchema),
  categoryController.updateCategorybyid,
);
// delete a category by ID
router.delete(
  "/delete-category/:id",
  verifyToken,
  categoryController.deleteCategory,
);

export default router;
