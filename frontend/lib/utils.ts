import { type ClassValue, clsx } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(paise: number): string {
  return `₹${(paise / 100).toFixed(2)}`;
}
