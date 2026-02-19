import { useState } from "react";
import Input from "./Input";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput({ label = "Contraseña", ...props }) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative">
      <Input
        label={label}
        type={showPassword ? "text" : "password"}
        {...props}
      />
      <button
        type="button"
        onClick={() => setShowPassword(!showPassword)}
        className="absolute right-3 top-[34px] text-gray-400 hover:text-gray-600"
        tabIndex={-1}
      >
        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}
