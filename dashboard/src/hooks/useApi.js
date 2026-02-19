import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";

export function useApi(path, { immediate = true } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate && !!path);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!path) return; // Don't fire if path is null/undefined
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(path);
      setData(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (immediate && path) fetch();
  }, [fetch, immediate, path]);

  return { data, loading, error, refetch: fetch };
}

export function useMutation(method, path) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mutate = useCallback(
    async (body) => {
      setLoading(true);
      setError(null);
      try {
        const res = await api[method](path, body);
        return res;
      } catch (e) {
        setError(e);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [method, path]
  );

  return { mutate, loading, error };
}
