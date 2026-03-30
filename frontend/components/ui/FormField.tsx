"use client";

import React from "react";

interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  children: React.ReactNode;
}

export const FormField = React.forwardRef<HTMLDivElement, FormFieldProps>(
  (
    { label, error, helperText, required, children, className = "", ...props },
    ref
  ) => (
    <div ref={ref} className={`flex flex-col gap-1.5 ${className}`} {...props}>
      {label && (
        <label className="text-sm font-medium text-[#ededed]">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
      )}
      {children}
      {error && <p className="text-xs text-red-400">{error}</p>}
      {helperText && !error && (
        <p className="text-xs text-[#8c8c8c]">{helperText}</p>
      )}
    </div>
  )
);
FormField.displayName = "FormField";

interface TextInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, helperText, required, ...props }, ref) => (
    <FormField label={label} error={error} helperText={helperText} required={required}>
      <input ref={ref} type="text" {...props} />
    </FormField>
  )
);
TextInput.displayName = "TextInput";

interface TextAreaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, helperText, required, ...props }, ref) => (
    <FormField label={label} error={error} helperText={helperText} required={required}>
      <textarea ref={ref} {...props} />
    </FormField>
  )
);
TextArea.displayName = "TextArea";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: Array<{ value: string; label: string }>;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, required, options, ...props }, ref) => (
    <FormField label={label} error={error} helperText={helperText} required={required}>
      <select ref={ref} {...props}>
        <option value="">선택하세요</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </FormField>
  )
);
Select.displayName = "Select";
