// frontend/src/components/shared/StatCard.jsx
export default function StatCard({ label, value, sub }) {
  return (
    <div className="bg-gray-800 border border-gray-700/50 p-4 rounded-xl mb-3 hover:border-gray-600 transition-colors">
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
        {label}
      </div>
      <div className="text-2xl font-mono font-bold text-white">
        {value}
      </div>
      <div className="text-[11px] text-gray-400 mt-1">
        {sub}
      </div>
    </div>
  );
}