const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://adhd-board-api.batistela.tech';
export const TIMEZONE = import.meta.env.VITE_TIMEZONE || 'America/Sao_Paulo';

export interface Category {
  id: number;
  name: string;
  label: string;
  icon: string; // SVG string
  color: string; // Hex color
  is_active: boolean;
  created_at: string;
}

export interface Template {
  id: number;
  name: string;
  template_html: string;
  is_active: boolean;
  created_at: string;
}

export interface Note {
  id: number;
  ticket_id: string;
  category_id: number;
  category: Category;
  text: string;
  date: string;
  image_path: string | null;
  html_content: string | null;
  template_id: number | null;
  printed: boolean;
  created_at: string;
}

export interface PaginatedNotes {
  data: Note[];
  metadata: {
    total: number;
    total_pages: number;
    page: number;
    first_page: number;
    last_page: number;
    previous_page: number | null;
    next_page: number | null;
  };
}

// Categories
export const getCategories = async (): Promise<Category[]> => {
  const response = await fetch(`${API_BASE_URL}/api/categories/`);
  if (!response.ok) throw new Error('Failed to fetch categories');
  return response.json();
};

export const createCategory = async (data: {
  name: string;
  label: string;
  icon: string;
  color: string;
  is_active?: boolean;
}): Promise<Category> => {
  const response = await fetch(`${API_BASE_URL}/api/categories/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create category');
  return response.json();
};

export const updateCategory = async (
  id: number,
  data: Partial<{
    name: string;
    label: string;
    icon: string;
    color: string;
    is_active: boolean;
  }>
): Promise<Category> => {
  const response = await fetch(`${API_BASE_URL}/api/categories/${id}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update category');
  return response.json();
};

export const deleteCategory = async (id: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/categories/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete category');
};

// Templates
export const getTemplates = async (): Promise<Template[]> => {
  const response = await fetch(`${API_BASE_URL}/api/templates/`);
  if (!response.ok) throw new Error('Failed to fetch templates');
  return response.json();
};

export const createTemplate = async (data: {
  name: string;
  template_html: string;
  is_active?: boolean;
}): Promise<Template> => {
  const response = await fetch(`${API_BASE_URL}/api/templates/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create template');
  return response.json();
};

export const updateTemplate = async (
  id: number,
  data: Partial<{
    name: string;
    template_html: string;
    is_active: boolean;
  }>
): Promise<Template> => {
  const response = await fetch(`${API_BASE_URL}/api/templates/${id}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update template');
  return response.json();
};

export const deleteTemplate = async (id: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/templates/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete template');
};

// Notes
export const getNotes = async (page = 1, perPage = 10): Promise<PaginatedNotes> => {
  const response = await fetch(`${API_BASE_URL}/api/notes/?page=${page}&per_page=${perPage}`);
  if (!response.ok) throw new Error('Failed to fetch notes');
  const payload = await response.json();
  const items: Note[] = payload.data || payload.items || [];
  const metadata = payload.metadata || {
    total: payload.total ?? items.length,
    total_pages: payload.total_pages ?? 1,
    page: payload.page ?? page,
    first_page: payload.first_page ?? 1,
    last_page: payload.last_page ?? 1,
    previous_page: payload.previous_page ?? null,
    next_page: payload.next_page ?? null,
  };
  return { data: items, metadata } as PaginatedNotes;
};

export const createNote = async (data: {
  category_id: number;
  text: string;
  template_id?: number | null;
  should_print?: boolean;
  width?: number;
}): Promise<Note> => {
  const response = await fetch(`${API_BASE_URL}/api/notes/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...data,
      should_print: data.should_print ?? true,
      width: data.width ?? 384,
    }),
  });
  if (!response.ok) throw new Error('Failed to create note');
  return response.json();
};

export const reprintNote = async (noteId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/notes/${noteId}/print`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to reprint note');
};

export const getNotePreview = async (
  noteId: number,
  format: 'image' | 'html' = 'image'
): Promise<string> => {
  const response = await fetch(`${API_BASE_URL}/api/notes/${noteId}/preview?format=${format}`);
  if (!response.ok) throw new Error('Failed to fetch note preview');
  return response.text();
};

// Helper to fetch SVG from Iconify and convert to string
export const fetchIconifySvg = async (icon: string): Promise<string> => {
  const response = await fetch(`https://api.iconify.design/${icon}.svg`);
  if (!response.ok) throw new Error('Failed to fetch icon');
  return response.text();
};
