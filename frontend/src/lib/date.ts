import { TIMEZONE } from './api';

const parseDate = (input?: string | number | Date): Date | null => {
  if (!input) return null;
  if (input instanceof Date) return isNaN(input.getTime()) ? null : input;
  if (typeof input === 'number') {
    const d = new Date(input);
    return isNaN(d.getTime()) ? null : d;
  }
  
  // If the string looks like ISO format without 'Z', treat it as UTC
  // e.g., "2025-11-18T06:01:49.454300" -> append 'Z' to parse as UTC
  let dateStr = input;
  if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}/.test(dateStr) && !dateStr.endsWith('Z') && !dateStr.includes('+')) {
    dateStr = dateStr.replace(' ', 'T') + 'Z';
  }
  
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : d;
};

/**
 * Formats a date string to the configured timezone
 * @param dateString - ISO or SQL date string from the API
 * @param format - 'relative' for "5 mins ago" or 'full' for full date
 */
export const formatDate = (dateString: string, format: 'relative' | 'full' = 'relative'): string => {
  const date = parseDate(dateString);
  if (!date) return '';
  
  if (format === 'relative') {
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSec < 30) return 'just now';
    if (diffMin === 1) return '1 min ago';
    if (diffMin < 60) return `${diffMin} mins ago`; 
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    // Older than a week: show full date
    return formatDate(dateString, 'full');
  }
  
  // Full format with timezone consideration
  try {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: TIMEZONE,
    }).format(date);
  } catch (error) {
    // Fallback if timezone is invalid
    return date.toLocaleString();
  }
};

export const getCurrentTime = (): Date => {
  return new Date();
};
