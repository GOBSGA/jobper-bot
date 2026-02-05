import { Link } from "react-router-dom";
import Logo from "../../components/ui/Logo";
import { ArrowLeft } from "lucide-react";

export default function Terms() {
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
        <h1>Términos y Condiciones de Uso</h1>
        <p className="text-sm text-gray-500">Última actualización: {new Date().toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" })}</p>

        <h2>1. Aceptación de los Términos</h2>
        <p>
          Al acceder y utilizar la plataforma Jobper (en adelante "la Plataforma"), operada por Jobper S.A.S. con domicilio en Colombia,
          usted acepta estos Términos y Condiciones en su totalidad. Si no está de acuerdo, no utilice la Plataforma.
        </p>

        <h2>2. Descripción del Servicio</h2>
        <p>
          Jobper es un CRM de contratos que permite a freelancers, consultores y PyMEs colombianas buscar, organizar y gestionar
          licitaciones públicas y privadas. La Plataforma ofrece:
        </p>
        <ul>
          <li>Búsqueda inteligente de contratos (SECOP, BID, Banco Mundial, entre otros)</li>
          <li>Pipeline CRM para gestión de oportunidades</li>
          <li>Marketplace de contratos privados</li>
          <li>Alertas y notificaciones personalizadas</li>
          <li>Herramientas de análisis con inteligencia artificial</li>
        </ul>

        <h2>3. Registro y Cuenta</h2>
        <p>
          Para acceder a la Plataforma debe registrarse con un correo electrónico válido. Usted es responsable de mantener
          la confidencialidad de su cuenta y de todas las actividades que ocurran bajo ella.
        </p>

        <h2>4. Planes y Pagos</h2>
        <p>
          La Plataforma ofrece planes de suscripción mensual. Los pagos se procesan a través de Wompi, proveedor de pagos
          autorizado por la Superintendencia Financiera de Colombia. Los precios están en pesos colombianos (COP) e incluyen IVA.
        </p>
        <ul>
          <li>El período de prueba gratuita es de 14 días calendario</li>
          <li>Las suscripciones se renuevan automáticamente</li>
          <li>Puede cancelar en cualquier momento desde la configuración de su cuenta</li>
          <li>No se realizan reembolsos por períodos parciales</li>
        </ul>

        <h2>5. Uso Aceptable</h2>
        <p>Al utilizar la Plataforma, usted se compromete a:</p>
        <ul>
          <li>No compartir información falsa o engañosa en el Marketplace</li>
          <li>No utilizar la Plataforma para actividades ilegales</li>
          <li>No intentar acceder a cuentas o datos de otros usuarios</li>
          <li>No realizar scraping, ingeniería inversa o cualquier extracción automatizada de datos</li>
          <li>Respetar los derechos de propiedad intelectual de terceros</li>
        </ul>

        <h2>6. Marketplace</h2>
        <p>
          Los contratos publicados en el Marketplace son responsabilidad exclusiva del usuario que los publica.
          Jobper actúa como intermediario tecnológico y no es parte de las negociaciones entre usuarios.
          Jobper no garantiza la veracidad de la información publicada por terceros.
        </p>

        <h2>7. Propiedad Intelectual</h2>
        <p>
          Todo el contenido, diseño, código y tecnología de la Plataforma es propiedad de Jobper S.A.S.
          Los datos de contratos públicos provienen de fuentes gubernamentales abiertas (datos.gov.co, SECOP).
        </p>

        <h2>8. Limitación de Responsabilidad</h2>
        <p>
          Jobper proporciona información de contratos recopilada de fuentes públicas. No garantizamos la exactitud,
          completitud o vigencia de dicha información. La decisión de participar en cualquier licitación es
          responsabilidad exclusiva del usuario.
        </p>

        <h2>9. Suspensión y Terminación</h2>
        <p>
          Jobper se reserva el derecho de suspender o terminar cuentas que violen estos términos,
          sin previo aviso y sin obligación de reembolso.
        </p>

        <h2>10. Ley Aplicable</h2>
        <p>
          Estos términos se rigen por las leyes de la República de Colombia. Cualquier disputa se resolverá
          ante los tribunales competentes de Bogotá D.C., Colombia.
        </p>

        <h2>11. Contacto</h2>
        <p>
          Para preguntas sobre estos términos, contáctenos en <strong>soporte@jobper.co</strong>.
        </p>
      </article>
    </div>
  );
}
