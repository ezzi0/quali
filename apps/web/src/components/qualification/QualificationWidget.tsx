import { useState } from 'react';
import { MessageCircle, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import QualificationChat from './QualificationChat';

export default function QualificationWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-4 py-3 rounded-full bg-black/70 text-white text-sm backdrop-blur-md border border-white/20 hover:bg-black/80"
      >
        <Sparkles className="w-4 h-4 text-primary" />
        Start qualification
      </button>
    );
  }

  return (
    <div className="w-full max-w-sm">
      <QualificationChat
        variant="widget"
        onOpenFull={() => navigate('/qualification')}
        onClose={() => setIsOpen(false)}
      />
      <div className="mt-3 flex items-center justify-between text-xs text-white/70">
        <span className="inline-flex items-center gap-1">
          <MessageCircle className="w-3 h-3" />
          Continues on the qualification page
        </span>
        <button
          onClick={() => navigate('/qualification')}
          className="text-white/80 hover:text-white underline"
        >
          Open full
        </button>
      </div>
    </div>
  );
}
