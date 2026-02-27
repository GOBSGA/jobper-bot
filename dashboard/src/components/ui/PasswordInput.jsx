import { useState } from "react";
import Input from "./Input";
import { Eye, EyeSlash } from "@phosphor-icons/react";

export default function PasswordInput({ label = "Contraseña", ...props }) {
  const [show, setShow] = useState(false);

  return (
    <div className="relative">
      <Input label={label} type={show ? "text" : "password"} {...props} />
      <button
        type="button"
        onClick={() => setShow(!show)}
        className="absolute right-3 top-[30px] text-ink-400 hover:text-ink-600 transition-colors"
        tabIndex={-1}
      >
        {show ? <EyeSlash size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}
