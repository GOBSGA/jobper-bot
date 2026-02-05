import { Link } from "react-router-dom";
import Logo from "../../components/ui/Logo";
import { ArrowLeft } from "lucide-react";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="sticky top-0 z-30 glass">
        <div className="max-w-3xl mx-auto flex items-center gap-3 px-6 py-4">
          <Link to="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition">
            <ArrowLeft className="h-4 w-4" /> <Logo size={24} /> <span className="font-bold text-gray-900">Jobper</span>
          </Link>
        </div>
      </nav>

      <article className="max-w-3xl mx-auto px-6 py-12 prose prose-gray prose-sm">
        <h1>Política de Privacidad y Protección de Datos</h1>
        <p className="text-sm text-gray-500">Última actualización: {new Date().toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" })}</p>

        <p>
          Jobper S.A.S. (en adelante "Jobper") se compromete a proteger la privacidad de sus usuarios
          en cumplimiento de la <strong>Ley 1581 de 2012</strong> (Protección de Datos Personales) y el
          <strong> Decreto 1377 de 2013</strong> de la República de Colombia.
        </p>

        <h2>1. Responsable del Tratamiento</h2>
        <ul>
          <li><strong>Razón social:</strong> Jobper S.A.S.</li>
          <li><strong>Domicilio:</strong> Bogotá D.C., Colombia</li>
          <li><strong>Correo:</strong> soporte@jobper.co</li>
        </ul>

        <h2>2. Datos que Recopilamos</h2>
        <h3>Datos proporcionados por el usuario:</h3>
        <ul>
          <li>Correo electrónico (para autenticación)</li>
          <li>Nombre de la empresa</li>
          <li>Sector de industria</li>
          <li>Palabras clave de interés profesional</li>
        </ul>
        <h3>Datos generados por el uso:</h3>
        <ul>
          <li>Historial de búsquedas de contratos</li>
          <li>Contratos guardados como favoritos</li>
          <li>Actividad en el Pipeline CRM</li>
          <li>Publicaciones en el Marketplace</li>
          <li>Registros de auditoría (accesos, acciones)</li>
        </ul>
        <h3>Datos técnicos:</h3>
        <ul>
          <li>Dirección IP (para seguridad y rate limiting)</li>
          <li>Tipo de navegador y dispositivo</li>
          <li>Fecha y hora de acceso</li>
        </ul>

        <h2>3. Finalidad del Tratamiento</h2>
        <p>Sus datos personales se utilizan para:</p>
        <ul>
          <li>Autenticación y gestión de su cuenta</li>
          <li>Personalización de resultados de búsqueda y alertas</li>
          <li>Procesamiento de pagos y facturación</li>
          <li>Envío de notificaciones relevantes sobre contratos</li>
          <li>Mejora del servicio y análisis estadístico (datos anonimizados)</li>
          <li>Cumplimiento de obligaciones legales</li>
          <li>Seguridad de la plataforma (prevención de fraude y abuso)</li>
        </ul>

        <h2>4. Medidas de Seguridad</h2>
        <p>Implementamos las siguientes medidas para proteger sus datos:</p>
        <ul>
          <li><strong>Autenticación sin contraseña:</strong> Usamos magic links por email, eliminando riesgos de contraseñas débiles o robadas</li>
          <li><strong>Tokens JWT:</strong> Sesiones con expiración automática y rotación de tokens</li>
          <li><strong>Cifrado en tránsito:</strong> Todas las comunicaciones usan HTTPS/TLS</li>
          <li><strong>Validación de entrada:</strong> Sanitización de todos los datos de usuario para prevenir inyección SQL y XSS</li>
          <li><strong>Rate limiting:</strong> Protección contra abuso y ataques de fuerza bruta</li>
          <li><strong>Auditoría:</strong> Registro de acciones sensibles (acceso a contactos, modificaciones)</li>
          <li><strong>Verificación HMAC:</strong> Webhooks de pago verificados criptográficamente</li>
        </ul>

        <h2>5. Compartición de Datos</h2>
        <p>Jobper <strong>no vende</strong> datos personales. Solo compartimos información con:</p>
        <ul>
          <li><strong>Wompi:</strong> Procesador de pagos (datos de transacción)</li>
          <li><strong>Resend:</strong> Servicio de envío de correo electrónico (dirección de email)</li>
          <li><strong>Autoridades:</strong> Cuando sea requerido por ley colombiana</li>
        </ul>
        <p>
          En el Marketplace, los datos de contacto (email, teléfono) solo se revelan a otros usuarios
          registrados que lo soliciten explícitamente, y cada revelación queda registrada en auditoría.
        </p>

        <h2>6. Derechos del Titular (Ley 1581 de 2012)</h2>
        <p>Como titular de datos personales, usted tiene derecho a:</p>
        <ul>
          <li><strong>Conocer:</strong> Qué datos tenemos sobre usted</li>
          <li><strong>Actualizar:</strong> Corregir datos inexactos o incompletos</li>
          <li><strong>Rectificar:</strong> Solicitar la corrección de información errónea</li>
          <li><strong>Suprimir:</strong> Solicitar la eliminación de sus datos</li>
          <li><strong>Revocar:</strong> Retirar la autorización otorgada</li>
        </ul>
        <p>
          Para ejercer estos derechos, envíe un correo a <strong>soporte@jobper.co</strong> con el asunto
          "Derechos de datos personales". Responderemos en un plazo máximo de 15 días hábiles conforme a la ley.
        </p>

        <h2>7. Retención de Datos</h2>
        <ul>
          <li>Datos de cuenta: mientras la cuenta esté activa + 6 meses después de cancelación</li>
          <li>Registros de auditoría: 2 años (requisito legal)</li>
          <li>Datos de pago: según requisitos tributarios colombianos (5 años)</li>
          <li>Magic links: eliminados después de uso o expiración (24 horas)</li>
        </ul>

        <h2>8. Cookies y Almacenamiento Local</h2>
        <p>
          Jobper utiliza localStorage del navegador para almacenar tokens de sesión (JWT).
          No utilizamos cookies de rastreo ni servicios de analytics de terceros.
        </p>

        <h2>9. Menores de Edad</h2>
        <p>
          La Plataforma está dirigida a profesionales y empresas. No recopilamos
          intencionalmente datos de menores de 18 años.
        </p>

        <h2>10. Cambios a esta Política</h2>
        <p>
          Nos reservamos el derecho de actualizar esta política. Notificaremos cambios
          significativos por correo electrónico. El uso continuado de la Plataforma después de
          cambios constituye aceptación de la política actualizada.
        </p>

        <h2>11. Contacto y Quejas</h2>
        <p>
          Para cualquier inquietud sobre privacidad: <strong>soporte@jobper.co</strong>
        </p>
        <p>
          También puede presentar quejas ante la <strong>Superintendencia de Industria y Comercio (SIC)</strong> de Colombia,
          entidad encargada de vigilar el cumplimiento de la Ley 1581 de 2012.
        </p>
      </article>
    </div>
  );
}
