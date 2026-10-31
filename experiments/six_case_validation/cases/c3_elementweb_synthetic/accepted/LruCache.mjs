// Independent Node.js transcription of the accepted DeepSeek LruCache
// (findings/ew_lru_deepseek.ts), with the matrix-js-sdk logger import stubbed.
// Behaviour is byte-for-byte equivalent to the accepted candidate.
const logger = { warn() {} };

export class LruCache {
    constructor(capacity) {
        this.capacity = capacity;
        this.map = new Map();
        this.recentlyUsed = [];
        if (capacity < 1) {
            throw new Error("Cache capacity must be at least 1");
        }
    }

    has(key) {
        if (!this.map.has(key)) {
            return false;
        }
        this.markAsRecentlyUsed(key);
        return true;
    }

    get(key) {
        if (!this.map.has(key)) {
            return undefined;
        }
        this.markAsRecentlyUsed(key);
        return this.map.get(key);
    }

    set(key, value) {
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

    delete(key) {
        if (!this.map.delete(key)) {
            return;
        }
        const index = this.recentlyUsed.indexOf(key);
        if (index !== -1) {
            this.recentlyUsed.splice(index, 1);
        }
    }

    clear() {
        this.map.clear();
        this.recentlyUsed.length = 0;
    }

    values() {
        return this.map.values();
    }

    markAsRecentlyUsed(key) {
        const index = this.recentlyUsed.indexOf(key);
        if (index !== -1) {
            this.recentlyUsed.splice(index, 1);
        }
        this.recentlyUsed.push(key);
    }

    evict() {
        while (this.map.size > this.capacity && this.recentlyUsed.length > 0) {
            const key = this.recentlyUsed.shift();
            this.map.delete(key);
        }
    }
}
