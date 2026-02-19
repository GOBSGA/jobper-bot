import { useState } from "react";

export function useFormSubmit(onSubmit) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onSubmit();
    } catch (err) {
      const msg = err.debug ? `${err.error} — ${err.debug}` : (err.error || "Error al procesar");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading, error, setError };
}
