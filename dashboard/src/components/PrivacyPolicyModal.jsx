import { useState } from "react";
import { api } from "../lib/api";
import { ShieldCheck, X } from "lucide-react";

// Note: Button component is used inline below instead of import

export default function PrivacyPolicyModal({ onAccept, onReject }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAccept = async () => {
    setLoading(true);
    setError("");
    try {
      await api.post("/user/accept-privacy-policy", {});
      onAccept();
    } catch (err) {
      setError(err.error || "Error al aceptar la política. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const handleReject = () => {
    onReject();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-brand-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Política de Privacidad</h2>
              <p className="text-sm text-gray-500">Última actualización: Febrero 2026</p>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="prose prose-sm max-w-none text-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 mt-0">1. Introducción</h3>
            <p>
              En Jobper, tu privacidad es nuestra prioridad. Esta política describe cómo recopilamos,
              usamos y protegemos tu información personal.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">2. Información que Recopilamos</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Información de cuenta: email, nombre de empresa</li>
              <li>Información de perfil: sector, ciudad, presupuesto</li>
              <li>Datos de uso: contratos guardados, búsquedas realizadas</li>
              <li>Información de pago: procesada de forma segura a través de Wompi</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">3. Cómo Usamos tu Información</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Proporcionar nuestro servicio de inteligencia de contratos</li>
              <li>Enviarte alertas personalizadas de oportunidades relevantes</li>
              <li>Mejorar y personalizar tu experiencia</li>
              <li>Procesar pagos y gestionar suscripciones</li>
              <li>Comunicarnos contigo sobre actualizaciones del servicio</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">4. Protección de Datos</h3>
            <p>
              Implementamos medidas de seguridad técnicas y organizativas para proteger tu información:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Cifrado SSL/TLS para todas las comunicaciones</li>
              <li>Contraseñas hasheadas con bcrypt</li>
              <li>Autenticación segura con JWT</li>
              <li>Backups regulares y encriptados</li>
              <li>Acceso restringido a datos personales</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">5. Compartir Información</h3>
            <p>
              NO vendemos tu información personal. Solo compartimos datos con:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Proveedores de servicios esenciales (hosting, procesamiento de pagos)</li>
              <li>Autoridades legales cuando sea requerido por ley</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">6. Tus Derechos</h3>
            <p>Tienes derecho a:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Acceder a tus datos personales</li>
              <li>Corregir información incorrecta</li>
              <li>Solicitar la eliminación de tu cuenta</li>
              <li>Exportar tus datos</li>
              <li>Revocar consentimientos</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">7. Cookies y Tracking</h3>
            <p>
              Usamos cookies estrictamente necesarias para el funcionamiento del servicio.
              No usamos cookies de terceros para publicidad o tracking.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">8. Retención de Datos</h3>
            <p>
              Conservamos tu información mientras tu cuenta esté activa y hasta 30 días después
              de la eliminación de la cuenta para cumplir con obligaciones legales.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">9. Cambios a esta Política</h3>
            <p>
              Nos reservamos el derecho de actualizar esta política. Te notificaremos de
              cambios importantes por email.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">10. Contacto</h3>
            <p>
              Para preguntas sobre privacidad, contáctanos en:{" "}
              <a href="mailto:privacy@jobper.co" className="text-brand-600 hover:underline">
                privacy@jobper.co
              </a>
            </p>
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex gap-3">
          <button
            onClick={handleReject}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 disabled:opacity-50 inline-flex items-center justify-center"
            disabled={loading}
          >
            <X className="h-4 w-4 mr-2" />
            Rechazar
          </button>
          <button
            onClick={handleAccept}
            className="flex-1 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 inline-flex items-center justify-center"
            disabled={loading}
          >
            {loading ? "Aceptando..." : (
              <>
                <ShieldCheck className="h-4 w-4 mr-2" />
                Aceptar Política
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
