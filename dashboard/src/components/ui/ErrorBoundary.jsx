import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import Button from "./Button";

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="mx-auto h-16 w-16 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Algo salió mal</h2>
            <p className="text-sm text-gray-500 mb-6">
              Ocurrió un error inesperado. Intenta recargar la página.
            </p>
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4" /> Recargar página
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
