import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Alert from "../../components/ui/Alert";
import AuthLayout from "../../components/auth/AuthLayout";
import SuccessCard from "../../components/auth/SuccessCard";
import { useFormSubmit } from "../../hooks/useFormSubmit";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const { submit, loading, error } = useFormSubmit(async () => {
    await api.post("/auth/forgot-password", { email });
    setSent(true);
  });

  if (sent) {
    return (
      <AuthLayout title="Revisa tu email" subtitle="Te enviamos un link de acceso">
        <SuccessCard
          icon={CheckCircle}
          title=""
          message={
            <>
              Enviamos un link mágico a <strong>{email}</strong>. Haz clic en el link para acceder sin contraseña.
            </>
          }
          action={
            <Link
              to="/login"
              className="mt-5 inline-flex items-center gap-1 text-sm text-brand-600 hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Volver al login
            </Link>
          }
        />
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Recuperar contraseña"
      subtitle="Te enviaremos un link para acceder sin contraseña"
    >
      {error && <Alert variant="error">{error}</Alert>}

      <form onSubmit={submit} className="space-y-5">
        <Input
          label="Email"
          type="email"
          placeholder="tu@empresa.co"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Enviando..." : (
            <>
              <Mail className="h-4 w-4 mr-2" />
              Enviar link de recuperación
            </>
          )}
        </Button>
        <Link
          to="/login"
          className="block text-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-3.5 w-3.5 inline mr-1" />
          Volver al login
        </Link>
      </form>
    </AuthLayout>
  );
}
