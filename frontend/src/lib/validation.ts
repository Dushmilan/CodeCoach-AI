import { FetchClient } from '@/lib/fetch-client';

const api = new FetchClient();

const ID_PATTERN = /^[a-z0-9-]+$/;

export interface FieldErrors {
  [key: string]: string;
}

export function validateRequired(value: string, fieldName: string): string | null {
  if (!value || value.trim() === '') return `${fieldName} is required`;
  return null;
}

export function validateIdFormat(value: string): string | null {
  if (!value) return null;
  if (!ID_PATTERN.test(value)) {
    return 'ID must contain only lowercase letters, numbers, and hyphens';
  }
  return null;
}

export function validateOrder(value: number): string | null {
  if (value === undefined || value === null) return null;
  if (!Number.isInteger(value) || value < 1) {
    return 'Order must be a positive integer';
  }
  return null;
}

export async function validateIdUnique(
  entityType: 'course' | 'module' | 'lesson',
  id: string,
  isEdit: boolean = false,
): Promise<string | null> {
  if (isEdit || !id) return null;
  try {
    const data = await api.get<{ exists: boolean }>(
      `/api/admin/check-id?entity_type=${entityType}&entity_id=${id}`,
    );
    return data.exists ? `This ${entityType} ID already exists` : null;
  } catch {
    return null;
  }
}

export function validateCourseForm(data: {
  id: string;
  title: string;
  order: number;
}): FieldErrors {
  const errors: FieldErrors = {};
  const idErr = validateRequired(data.id, 'ID') || validateIdFormat(data.id);
  if (idErr) errors.id = idErr;
  const titleErr = validateRequired(data.title, 'Title');
  if (titleErr) errors.title = titleErr;
  const orderErr = validateOrder(data.order);
  if (orderErr) errors.order = orderErr;
  return errors;
}

export function validateModuleForm(data: {
  id: string;
  title: string;
  order: number;
}): FieldErrors {
  const errors: FieldErrors = {};
  const idErr = validateRequired(data.id, 'ID') || validateIdFormat(data.id);
  if (idErr) errors.id = idErr;
  const titleErr = validateRequired(data.title, 'Title');
  if (titleErr) errors.title = titleErr;
  const orderErr = validateOrder(data.order);
  if (orderErr) errors.order = orderErr;
  return errors;
}

export function validateLessonForm(data: {
  id: string;
  title: string;
  order: number;
}): FieldErrors {
  const errors: FieldErrors = {};
  const idErr = validateRequired(data.id, 'ID') || validateIdFormat(data.id);
  if (idErr) errors.id = idErr;
  const titleErr = validateRequired(data.title, 'Title');
  if (titleErr) errors.title = titleErr;
  const orderErr = validateOrder(data.order);
  if (orderErr) errors.order = orderErr;
  return errors;
}
