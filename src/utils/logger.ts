/**
 * Centralized logging utility for frontend.
 * Only logs in development mode to avoid console noise in production.
 */

const isDev = import.meta.env.DEV

export const logger = {
  log: (...args: unknown[]) => {
    if (isDev) {
      console.log(...args)
    }
  },
  
  info: (...args: unknown[]) => {
    if (isDev) {
      console.info(...args)
    }
  },
  
  warn: (...args: unknown[]) => {
    if (isDev) {
      console.warn(...args)
    }
  },
  
  error: (...args: unknown[]) => {
    // Always log errors, even in production
    console.error(...args)
  },
  
  debug: (...args: unknown[]) => {
    if (isDev) {
      console.debug(...args)
    }
  }
}

