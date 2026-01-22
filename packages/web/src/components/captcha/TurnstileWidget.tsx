"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Cloudflare Turnstile CAPTCHA widget.
 * 
 * A privacy-friendly CAPTCHA alternative that uses behavioral analysis
 * instead of visual puzzles.
 * 
 * @see https://developers.cloudflare.com/turnstile/
 */

type TurnstileTheme = "light" | "dark" | "auto";
type TurnstileSize = "normal" | "compact";

interface TurnstileRenderOptions {
  sitekey: string;
  theme: TurnstileTheme;
  size: TurnstileSize;
  callback: (token: string) => void;
  "error-callback": (error: string) => void;
  "expired-callback": () => void;
}

interface TurnstileWidgetProps {
  siteKey?: string;
  onVerify: (token: string) => void;
  onError?: (error: string) => void;
  onExpire?: () => void;
  theme?: TurnstileTheme;
  size?: TurnstileSize;
  className?: string;
}

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: TurnstileRenderOptions) => string;
      reset: (widgetId: string) => void;
      remove: (widgetId: string) => void;
      getResponse: (widgetId: string) => string;
    };
  }
}

export function TurnstileWidget({
  siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || "",
  onVerify,
  onError,
  onExpire,
  theme = "auto",
  size = "normal",
  className = "",
}: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [scriptError, setScriptError] = useState(false);

  // Load Turnstile script
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check if script is already loaded
    if (window.turnstile) {
      setIsLoaded(true);
      return;
    }

    // Check if script is already in DOM
    const existingScript = document.querySelector(
      'script[src*="turnstile"]'
    );
    if (existingScript) {
      existingScript.addEventListener("load", () => setIsLoaded(true));
      existingScript.addEventListener("error", () => setScriptError(true));
      return;
    }

    // Load Turnstile script
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    script.async = true;
    script.defer = true;

    script.onload = () => {
      setIsLoaded(true);
    };

    script.onerror = () => {
      setScriptError(true);
      onError?.("Failed to load CAPTCHA script");
    };

    document.head.appendChild(script);

    return () => {
      // Cleanup is handled in the render effect
    };
  }, [onError]);

  // Render widget when script is loaded
  useEffect(() => {
    if (!isLoaded || !containerRef.current || !siteKey) return;
    if (!window.turnstile) return;

    // Render the widget
    try {
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        theme,
        size,
        callback: (token: string) => {
          onVerify(token);
        },
        "error-callback": (error: string) => {
          onError?.(error);
        },
        "expired-callback": () => {
          onExpire?.();
        },
      });
    } catch (error) {
      console.error("Failed to render Turnstile widget:", error);
      onError?.("Failed to initialize CAPTCHA");
    }

    // Cleanup
    return () => {
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch {
          // Ignore cleanup errors
        }
      }
    };
  }, [isLoaded, siteKey, theme, size, onVerify, onError, onExpire]);

  // Don't render if no site key
  if (!siteKey) {
    return null;
  }

  // Show error state
  if (scriptError) {
    return (
      <div className={`text-red-500 text-sm ${className}`}>
        Failed to load CAPTCHA. Please refresh the page.
      </div>
    );
  }

  return (
    <div className={className}>
      <div ref={containerRef} />
    </div>
  );
}

/**
 * Hook for managing Turnstile verification state.
 */
export function useTurnstile() {
  const [token, setToken] = useState<string | null>(null);
  const [isVerified, setIsVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = (verifiedToken: string) => {
    setToken(verifiedToken);
    setIsVerified(true);
    setError(null);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setIsVerified(false);
    setToken(null);
  };

  const handleExpire = () => {
    setIsVerified(false);
    setToken(null);
  };

  const reset = () => {
    setToken(null);
    setIsVerified(false);
    setError(null);
  };

  return {
    token,
    isVerified,
    error,
    handleVerify,
    handleError,
    handleExpire,
    reset,
  };
}
