import { useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { ShieldCheck, LogOut } from "lucide-react";

/**
 * Mandatory privacy policy acceptance page.
 * Shown full-screen (no sidebar/nav) when user hasn't accepted
 * the current privacy policy version. Cannot be dismissed.
 */
export default function PrivacyAcceptance() {
  const { user, logout, setUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAccept = async () => {
    setLoading(true);
    setError("");
    try {
      await api.post("/user/accept-privacy-policy", {});
      // Optimistic update: mark as accepted locally so PrivateRoute re-renders immediately.
      // Do NOT call refresh() here — it can trigger doLogout() on 401 and eject the user.
      setUser({ ...user, needs_privacy_acceptance: false });
    } catch (err) {
      setError(err.error || "Error al aceptar. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-brand-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Politica de Privacidad
              </h2>
              <p className="text-sm text-gray-500">
                Debes aceptar para continuar usando Jobper
              </p>
            </div>
          </div>
        </div>

        {/* Policy content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="prose prose-sm max-w-none text-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 mt-0">1. Introduccion</h3>
            <p>
              En Jobper, tu privacidad es nuestra prioridad. Esta politica describe como recopilamos,
              usamos y protegemos tu informacion personal, en cumplimiento con la Ley 1581 de 2012
              de Proteccion de Datos Personales de Colombia y sus decretos reglamentarios.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">2. Responsable del Tratamiento</h3>
            <p>
              Jobper es el responsable del tratamiento de tus datos personales.
              Contacto: <a href="mailto:soporte@jobper.co" className="text-brand-600 hover:underline">soporte@jobper.co</a>
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">3. Informacion que Recopilamos</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Informacion de cuenta: email, nombre de empresa</li>
              <li>Informacion de perfil: sector, ciudad, presupuesto</li>
              <li>Datos de uso: contratos guardados, busquedas realizadas</li>
              <li>Informacion de pago: procesada mediante transferencia bancaria</li>
              <li>Datos tecnicos: direccion IP, tipo de navegador (solo para seguridad)</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">4. Finalidad del Tratamiento</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Proporcionar nuestro servicio de inteligencia de contratos</li>
              <li>Enviarte alertas personalizadas de oportunidades relevantes</li>
              <li>Mejorar y personalizar tu experiencia</li>
              <li>Procesar pagos y gestionar suscripciones</li>
              <li>Comunicarnos contigo sobre actualizaciones del servicio</li>
              <li>Garantizar la seguridad de la plataforma</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">5. Proteccion de Datos</h3>
            <p>
              Implementamos medidas de seguridad tecnicas y organizativas para proteger tu informacion:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Cifrado SSL/TLS para todas las comunicaciones</li>
              <li>Contrasenas hasheadas con bcrypt</li>
              <li>Autenticacion segura con JWT</li>
              <li>Validacion de entradas contra XSS e inyeccion SQL</li>
              <li>Rate limiting y logs de auditoria</li>
              <li>Acceso restringido a datos personales</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">6. Compartir Informacion</h3>
            <p>
              NO vendemos, alquilamos ni comercializamos tu informacion personal. Solo compartimos datos con:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Resend (servicio de email transaccional) para enviar notificaciones</li>
              <li>Autoridades competentes cuando sea requerido por ley colombiana</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">7. Tus Derechos (Ley 1581 de 2012)</h3>
            <p>Como titular de datos, tienes derecho a:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Conocer, actualizar y rectificar tus datos personales</li>
              <li>Solicitar prueba de la autorizacion otorgada</li>
              <li>Ser informado sobre el uso de tus datos</li>
              <li>Presentar quejas ante la SIC (Superintendencia de Industria y Comercio)</li>
              <li>Revocar la autorizacion y/o solicitar la supresion de datos</li>
              <li>Acceder gratuitamente a tus datos personales</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">8. Cookies y Almacenamiento Local</h3>
            <p>
              Usamos unicamente tokens JWT en localStorage para la autenticacion.
              No usamos cookies de terceros, ni herramientas de tracking o publicidad.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">9. Retencion de Datos</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Datos de cuenta: mientras tu cuenta este activa + 6 meses post-eliminacion</li>
              <li>Logs de auditoria: 2 anos (requerimiento legal)</li>
              <li>Datos de pago: 5 anos (requerimiento tributario colombiano)</li>
              <li>Magic links: 24 horas (auto-eliminados)</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">10. Cambios a esta Politica</h3>
            <p>
              Nos reservamos el derecho de actualizar esta politica. Te notificaremos de
              cambios importantes por email y te solicitaremos aceptar la nueva version
              antes de continuar usando el servicio.
            </p>

            <h3 className="text-lg font-semibold text-gray-900 mt-6">11. Contacto y Quejas</h3>
            <p>
              Para ejercer tus derechos o realizar consultas:{" "}
              <a href="mailto:soporte@jobper.co" className="text-brand-600 hover:underline">
                soporte@jobper.co
              </a>
            </p>
            <p>
              Para quejas ante la autoridad de proteccion de datos:{" "}
              <a href="https://www.sic.gov.co" target="_blank" rel="noopener noreferrer" className="text-brand-600 hover:underline">
                Superintendencia de Industria y Comercio (SIC)
              </a>
            </p>
          </div>
        </div>

        {/* Actions — sticky at bottom, NO dismiss */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex gap-3 rounded-b-2xl">
          <button
            onClick={logout}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 disabled:opacity-50 inline-flex items-center justify-center font-medium"
            disabled={loading}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Rechazar y cerrar sesion
          </button>
          <button
            onClick={handleAccept}
            className="flex-1 px-4 py-3 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 inline-flex items-center justify-center font-medium"
            disabled={loading}
          >
            {loading ? (
              "Aceptando..."
            ) : (
              <>
                <ShieldCheck className="h-4 w-4 mr-2" />
                Aceptar y continuar
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
