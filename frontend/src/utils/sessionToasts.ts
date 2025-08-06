// frontend/src/lib/sessionToasts.ts
import { toast } from "sonner";

/**
 * Show session warning with countdown
 */
export function showSessionWarning(seconds: number): string | number {
  return toast.warning(`Session expires in ${seconds}s`, {
    description: "Due to inactivity.",
    duration: Infinity,
  });
}

/**
 * Update existing session warning
 */
export function updateSessionWarning(
  id: string | number,
  seconds: number
): void {
  toast.warning(`Session expires in ${seconds}s`, {
    id,
    description: "Due to inactivity.",
    duration: Infinity,
  });
}

/**
 * Dismiss session warning
 */
export function dismissSessionWarning(id: string | number): void {
  toast.dismiss(id);
}
