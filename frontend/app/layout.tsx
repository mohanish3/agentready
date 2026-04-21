import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "agentready — AI Agent Readiness Scanner",
  description: "Find out if AI purchasing agents can discover, parse, and act on your website.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#030712] text-gray-100">
        {children}
      </body>
    </html>
  );
}
