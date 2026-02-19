export default function SuccessCard({ icon: Icon, title, message, action }) {
  return (
    <div className="rounded-xl bg-green-50 border border-green-200 p-6 text-center">
      <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-green-600" />
      </div>
      <h2 className="font-semibold text-green-800">{title}</h2>
      <p className="mt-2 text-sm text-green-700 leading-relaxed">{message}</p>
      {action}
    </div>
  );
}
