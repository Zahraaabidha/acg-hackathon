import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { PillButton } from "../PillButton";

const NAV_LINKS = [
  { label: "Overview", href: "#overview" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Model", href: "#model" },
];

export function LandingNav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="relative z-20 px-2 pt-3 sm:px-3">
      <div className="mx-auto max-w-[1200px]">
        <div className="flex items-center justify-between rounded-full bg-white p-[5px]">
          <div className="flex items-center gap-6">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-ink-900)] sm:h-10 sm:w-10">
              <span className="font-display text-[10px] font-bold tracking-tight text-white">ACG</span>
            </div>
            <div className="hidden items-center gap-6 md:flex">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-[14px] text-[var(--color-ink-900)] transition-colors duration-300 hover:text-neutral-500"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div className="hidden items-center gap-4 md:flex">
            <span className="hidden text-[13px] text-neutral-500 lg:block">Raw Material Intelligence</span>
            <PillButton label="Open Dashboard" variant="dark" href="/dashboard" />
          </div>

          <button
            className="flex items-center justify-center rounded-full bg-[var(--color-ink-900)] p-2 md:hidden"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={18} className="text-white" /> : <Menu size={18} className="text-white" />}
          </button>
        </div>
      </div>

      <div
        className={`fixed inset-0 z-50 transition-opacity duration-300 md:hidden ${open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}
        style={{ backgroundColor: "rgba(0,0,0,0.6)" }}
        onClick={() => setOpen(false)}
      >
        <div
          className={`absolute bottom-0 left-0 right-0 mx-3 mb-3 rounded-2xl bg-white p-6 transition-transform duration-500 ${open ? "translate-y-0" : "translate-y-full"}`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="mb-8 flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-[28px] font-medium text-[var(--color-ink-900)]"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </div>
          <Link
            to="/dashboard"
            className="flex w-full items-center justify-between rounded-full bg-[var(--color-ink-900)] px-5 py-3 text-[14px] font-medium text-white no-underline"
          >
            Open Dashboard
          </Link>
        </div>
      </div>
    </nav>
  );
}
