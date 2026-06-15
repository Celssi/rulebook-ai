import type { ReactNode } from "react";
import { X } from "lucide-react";

type DialogSize = "md" | "lg";

const SIZE_CLASS: Record<DialogSize, string> = {
  md: "max-w-2xl",
  lg: "max-w-3xl",
};

interface Props {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  size?: DialogSize;
  closeLabel?: string;
}

export default function AppDialog({
  open,
  title,
  subtitle,
  onClose,
  children,
  size = "md",
  closeLabel = "Close",
}: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className={`panel-elevated w-full ${SIZE_CLASS[size]} max-h-[90vh] flex flex-col overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="app-dialog-title"
        aria-modal="true"
      >
        <header className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border shrink-0">
          <div className="min-w-0">
            <h2 id="app-dialog-title" className="text-lg font-semibold">
              {title}
            </h2>
            {subtitle && <p className="text-sm text-muted truncate">{subtitle}</p>}
          </div>
          <button
            type="button"
            className="btn-ghost p-2 rounded-lg shrink-0"
            onClick={onClose}
            aria-label={closeLabel}
          >
            <X className="w-4 h-4" />
          </button>
        </header>
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden">{children}</div>
      </div>
    </div>
  );
}
