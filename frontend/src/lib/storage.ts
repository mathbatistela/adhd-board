// Re-export types from API
export type { Category, Template, Note } from './api';

const STORAGE_KEYS = {
  RECENT_CATEGORIES: 'receipt-notes-recent-categories',
  LAST_CATEGORY: 'receipt-notes-last-category',
  LAST_TEMPLATE: 'receipt-notes-last-template',
};

// Recent categories (still using localStorage for UI state)
export const getRecentCategories = (): number[] => {
  const data = localStorage.getItem(STORAGE_KEYS.RECENT_CATEGORIES);
  return data ? JSON.parse(data) : [];
};

export const updateRecentCategory = (categoryId: number): void => {
  let recent = getRecentCategories();
  recent = recent.filter(id => id !== categoryId);
  recent.unshift(categoryId);
  recent = recent.slice(0, 4);
  localStorage.setItem(STORAGE_KEYS.RECENT_CATEGORIES, JSON.stringify(recent));
};

// Last selected category
export const getLastCategory = (): number | null => {
  const data = localStorage.getItem(STORAGE_KEYS.LAST_CATEGORY);
  return data ? JSON.parse(data) : null;
};

export const setLastCategory = (categoryId: number | null): void => {
  if (categoryId === null) {
    localStorage.removeItem(STORAGE_KEYS.LAST_CATEGORY);
  } else {
    localStorage.setItem(STORAGE_KEYS.LAST_CATEGORY, JSON.stringify(categoryId));
  }
};

// Last selected template
export const getLastTemplate = (): number | null => {
  const data = localStorage.getItem(STORAGE_KEYS.LAST_TEMPLATE);
  return data ? JSON.parse(data) : null;
};

export const setLastTemplate = (templateId: number | null): void => {
  if (templateId === null) {
    localStorage.removeItem(STORAGE_KEYS.LAST_TEMPLATE);
  } else {
    localStorage.setItem(STORAGE_KEYS.LAST_TEMPLATE, JSON.stringify(templateId));
  }
};
