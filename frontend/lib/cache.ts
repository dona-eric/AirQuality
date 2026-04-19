/**
 * Smart caching layer for API responses
 * - Client-side cache with TTL (Time To Live)
 * - Request deduplication
 * - Automatic cleanup of stale data
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class APICache {
  private cache = new Map<string, CacheEntry<any>>();
  private pendingRequests = new Map<string, Promise<any>>();

  // TTL in milliseconds
  private TTL = {
    DATA: 5 * 60 * 1000,      // Data: 5 minutes
    PREDICTION: 3 * 60 * 1000, // Prediction: 3 minutes
    HISTORY: 10 * 60 * 1000,   // History: 10 minutes
  };

  /**
   * Get from cache or fetch
   * @param key - Cache key
   * @param fetcher - Async function to fetch data
   * @param ttl - Time to live in ms
   */
  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    // Return cached data if valid
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }

    // Deduplicate pending requests
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!;
    }

    // Fetch and cache
    const promise = fetcher();
    this.pendingRequests.set(key, promise);

    try {
      const data = await promise;
      this.cache.set(key, { data, timestamp: Date.now(), ttl });
      return data;
    } finally {
      this.pendingRequests.delete(key);
    }
  }

  /**
   * Invalidate cache entry
   */
  invalidate(key: string): void {
    this.cache.delete(key);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
    this.pendingRequests.clear();
  }

  /**
   * Get TTL for specific data type
   */
  getTTL(type: "data" | "prediction" | "history"): number {
    return this.TTL[type.toUpperCase() as keyof typeof this.TTL];
  }
}

export const apiCache = new APICache();
