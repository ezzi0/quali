import { Calendar } from 'lucide-react';

interface UpdatedBlockProps {
  date: string;
  note?: string;
}

export default function UpdatedBlock({ date, note }: UpdatedBlockProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground border-t border-border pt-6 mt-12">
      <Calendar className="w-4 h-4" />
      <span>Last updated: {date}</span>
      {note && (
        <>
          <span className="mx-2">•</span>
          <span>{note}</span>
        </>
      )}
    </div>
  );
}
