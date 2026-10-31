/*
Copyright 2023 The Matrix.org Foundation C.I.C.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

import { logger } from "matrix-js-sdk/src/logger";

/**
 * A Least Recently Used cache.
 *
 * Values are stored in a native Map so that the values iterator keeps the
 * insertion order of the surviving keys. Recency is tracked separately so
 * that reading an existing key does not move it in the values iterator.
 */
export class LruCache<K, V> {
    private readonly map = new Map<K, V>();
    private readonly recentlyUsed: K[] = [];

    public constructor(private readonly capacity: number) {
        if (capacity < 1) {
            throw new Error("Cache capacity must be at least 1");
        }
    }

    /**
     * Check whether the cache contains an item under this key.
     * Marks the item as most recently used.
     */
    public has(key: K): boolean {
        if (!this.map.has(key)) {
            return false;
        }

        this.markAsRecentlyUsed(key);
        return true;
    }

    /**
     * Returns an item from the cache.
     * Marks the item as most recently used.
     */
    public get(key: K): V | undefined {
        if (!this.map.has(key)) {
            return undefined;
        }

        this.markAsRecentlyUsed(key);
        return this.map.get(key);
    }

    /**
     * Adds an item to the cache.
     * A newly added item is set as the most recently used.
     */
    public set(key: K, value: V): void {
        try {
            const isUpdate = this.map.has(key);
            this.map.set(key, value);

            if (isUpdate) {
                this.markAsRecentlyUsed(key);
            } else {
                this.recentlyUsed.push(key);
                this.evict();
            }
        } catch (error) {
            logger.warn("LruCache error", error);
            this.clear();
        }
    }

    /**
     * Deletes an item from the cache.
     */
    public delete(key: K): void {
        if (!this.map.delete(key)) {
            return;
        }

        const index = this.recentlyUsed.indexOf(key);
        if (index !== -1) {
            this.recentlyUsed.splice(index, 1);
        }
    }

    /**
     * Clears all items from the cache.
     */
    public clear(): void {
        this.map.clear();
        this.recentlyUsed.length = 0;
    }

    /**
     * Returns an iterator over the cached values in Map insertion order for
     * the surviving keys.
     */
    public values(): IterableIterator<V> {
        return this.map.values();
    }

    private markAsRecentlyUsed(key: K): void {
        const index = this.recentlyUsed.indexOf(key);
        if (index !== -1) {
            this.recentlyUsed.splice(index, 1);
        }
        this.recentlyUsed.push(key);
    }

    private evict(): void {
        while (this.map.size > this.capacity && this.recentlyUsed.length > 0) {
            const key = this.recentlyUsed.shift()!;
            this.map.delete(key);
        }
    }
}
