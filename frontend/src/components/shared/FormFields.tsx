import type { ReactNode, SelectHTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { rosterEntryLabel } from "../../lib/rosterLabel";

export interface SelectOption {
  id: string;
  label: string;
}

function joinClass(...parts: (string | false | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function FieldLabel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={joinClass("label mb-1", className)}>{children}</div>;
}

export function FormSelect({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={joinClass("select", className)} {...props} />;
}

export function FormInput({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={joinClass("input", className)} {...props} />;
}

export function FormTextarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={joinClass("input", className)} {...props} />;
}

export function SelectField({
  label,
  value,
  options,
  onChange,
  className,
  selectClassName,
  placeholder,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (id: string) => void;
  className?: string;
  selectClassName?: string;
  placeholder?: string;
}) {
  return (
    <div className={className}>
      <FieldLabel>{label}</FieldLabel>
      <FormSelect
        className={selectClassName}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.id || "empty"} value={o.id}>
            {o.label}
          </option>
        ))}
      </FormSelect>
    </div>
  );
}

export function LabeledSelect({
  label,
  className,
  selectClassName,
  options,
  placeholder,
  children,
  ...selectProps
}: {
  label: string;
  className?: string;
  selectClassName?: string;
  options?: SelectOption[];
  placeholder?: string;
  children?: ReactNode;
} & Omit<SelectHTMLAttributes<HTMLSelectElement>, "children">) {
  return (
    <label className={joinClass("block", className)}>
      <span className="text-muted text-xs">{label}</span>
      <FormSelect className={joinClass("w-full mt-1", selectClassName)} {...selectProps}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {children ??
          (options || []).map((o) => (
            <option key={o.id || "empty"} value={o.id}>
              {o.label}
            </option>
          ))}
      </FormSelect>
    </label>
  );
}

export function RosterSelect({
  label = "Character",
  roster,
  activeId,
  disabled,
  onChange,
  className,
  selectClassName,
}: {
  label?: string;
  roster: { id: string; name: string }[];
  activeId: string;
  disabled?: boolean;
  onChange: (id: string) => void;
  className?: string;
  selectClassName?: string;
}) {
  return (
    <div className={className}>
      <FieldLabel>{label}</FieldLabel>
      <FormSelect
        className={joinClass("w-full", selectClassName)}
        value={activeId}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      >
        {roster.map((r) => (
          <option key={r.id} value={r.id}>
            {rosterEntryLabel(r.name) || r.id}
          </option>
        ))}
      </FormSelect>
    </div>
  );
}
