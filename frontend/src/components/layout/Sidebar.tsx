import { NavLink } from "react-router-dom";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Overview", icon: "📊" },
  { to: "/endpoints", label: "Endpoints", icon: "💻" },
  { to: "/software", label: "Software", icon: "📦" },
  { to: "/updates", label: "Windows Updates", icon: "🔄" },
  { to: "/patch-catalog", label: "Patch Catalog", icon: "📋" },
  { to: "/sync", label: "Sync Jobs", icon: "⚙️" },
  { to: "/settings", label: "Settings", icon: "🔧" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-700">
        <h1 className="text-sm font-bold text-blue-400 uppercase tracking-wider">Endpoint Dashboard</h1>
      </div>
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )
            }
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
