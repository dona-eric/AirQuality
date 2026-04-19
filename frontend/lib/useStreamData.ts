/**
 * Performance optimization hook for streaming data
 * Debounces repeated requests and handles partial updates
 */

import { useEffect, useRef, useCallback, useState } from "react";

interface UseStreamOptions {
  debounceMs?: number;
  maxRetries?: number;
}

export function useStreamData<T>(
  fetcher: () => Promise<T>,
  onData: (data: T) => void,
  options: UseStreamOptions = {}
) {
  const { debounceMs = 300, maxRetries = 3 } = options;
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchWithRetry = useCallback(
    async (retries = 0) => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetcher();
        onData(data);
      } catch (err) {
        if (retries < maxRetries) {
          setTimeout(() => fetchWithRetry(retries + 1), Math.pow(2, retries) * 1000);
        } else {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      } finally {
        setIsLoading(false);
      }
    },
    [fetcher, onData, maxRetries]
  );

  const debouncedFetch = useCallback(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchWithRetry();
    }, debounceMs);
  }, [fetchWithRetry, debounceMs]);

  useEffect(() => {
    debouncedFetch();
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [debouncedFetch]);

  return { isLoading, error };
}
