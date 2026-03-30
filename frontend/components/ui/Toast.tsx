"use client";

import React, { createContext, useContext, useState, useCallback, useRef, ReactNode } from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface ToastMessage {
  id: string;
  message: string;
  variant: ToastVariant;
  action?: {
    label: string;
    handler: () => void;
  };
  duration?: number;
}

interface ToastContextType {
  toasts: ToastMessage[];
  success: (message: string, options?: { action?: ToastMessage["action"] }) => void;
  error: (message: string, options?: { action?: ToastMessage["action"] }) => void;
  warning: (message: string, options?: { action?: ToastMessage["action"] }) => void;
  info: (message: string, options?: { action?: ToastMessage["action"] }) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  // Issue #4 fix: Store timeout IDs to clear them on dismiss
  const timeoutMapRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const addToast = useCallback(
    (message: string, variant: ToastVariant, options?: { action?: ToastMessage["action"] }) => {
      const id = Math.random().toString(36).substr(2, 9);
      const duration = variant === "error" ? 8000 : 5000;

      const toast: ToastMessage = {
        id,
        message,
        variant,
        action: options?.action,
        duration,
      };

      setToasts((prev) => [...prev, toast]);

      const timeoutId = setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
        timeoutMapRef.current.delete(id);
      }, duration);

      timeoutMapRef.current.set(id, timeoutId);
      return { id, dismiss: () => clearTimeout(timeoutId) };
    },
    []
  );

  const dismiss = useCallback((id: string) => {
    // Clear the timeout when manually dismissing
    const timeoutId = timeoutMapRef.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutMapRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const value: ToastContextType = {
    toasts,
    success: (message, options) => addToast(message, "success", options),
    error: (message, options) => addToast(message, "error", options),
    warning: (message, options) => addToast(message, "warning", options),
    info: (message, options) => addToast(message, "info", options),
    dismiss,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={() => onDismiss(toast.id)} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: ToastMessage;
  onDismiss: () => void;
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const variantClasses: Record<ToastVariant, { bg: string; border: string; icon: string; text: string }> = {
    success: {
      bg: "bg-[#0d6b3d]",
      border: "border-[#1a9d5d]",
      icon: "✓",
      text: "text-[#3ecf8e]",
    },
    error: {
      bg: "bg-[#7a1f1f]",
      border: "border-[#dc2626]",
      icon: "✕",
      text: "text-[#ff6b6b]",
    },
    warning: {
      bg: "bg-[#7a4200]",
      border: "border-[#f59e0b]",
      icon: "⚠",
      text: "text-[#fbbf24]",
    },
    info: {
      bg: "bg-[#1e3a5f]",
      border: "border-[#3b82f6]",
      icon: "ℹ",
      text: "text-[#60a5fa]",
    },
  };

  const variant = variantClasses[toast.variant];

  return (
    <div
      className={cn(
        "pointer-events-auto rounded-lg border px-4 py-3 shadow-lg animate-in slide-in-from-right-4 fade-in",
        variant.bg,
        variant.border,
        "flex items-start gap-3"
      )}
    >
      <span className={cn("flex-shrink-0 font-bold mt-0.5", variant.text)}>{variant.icon}</span>
      <div className="flex-1">
        <p className="text-sm text-[#ededed]">{toast.message}</p>
        {toast.action && (
          <button
            onClick={() => {
              toast.action?.handler();
              onDismiss();
            }}
            className="mt-2 inline-block text-xs font-semibold underline text-[#3ecf8e] hover:text-[#5edea0]"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={onDismiss}
        className="flex-shrink-0 text-[#8c8c8c] hover:text-[#ededed] mt-0.5"
        aria-label="Close"
      >
        ✕
      </button>
    </div>
  );
}

export default ToastProvider;
