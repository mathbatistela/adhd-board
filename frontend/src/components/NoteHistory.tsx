import { Eye, Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Note } from '@/lib/api';

interface NoteHistoryProps {
  notes: Note[];
  onView: (note: Note) => void;
  onPrint: (note: Note) => void;
}

import { formatDate } from '@/lib/date';

export const NoteHistory = ({ notes, onView, onPrint }: NoteHistoryProps) => {

  if (!notes || notes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
        <div className="text-6xl opacity-30">🧾</div>
        <p className="text-muted-foreground text-sm">No notes yet</p>
        <p className="text-xs text-muted-foreground/70 max-w-[200px]">
          Start by writing a note above and tap Print!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold mb-4">Recent Notes</h2>
      {notes.map((note) => (
        <div
          key={note.id}
          className="flex items-start gap-3 p-4 rounded-xl border bg-card shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-semibold text-accent px-2 py-1 bg-accent/10 rounded-md">
                {note.category.label}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatDate(note.created_at || note.date, 'relative')}
              </span>
            </div>
            <p className="text-sm receipt-font line-clamp-2 break-all leading-relaxed">
              {note.text}
            </p>
          </div>
          <div className="flex gap-1 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onView(note)}
              className="hover:bg-accent/10"
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onPrint(note)}
              className="hover:bg-accent/10"
            >
              <Printer className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};
