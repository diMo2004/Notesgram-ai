import type { ReactNode } from "react";

export const metadata = {
  title: "Notesgram",
  description: "AI Knowledge Workspace MVP",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#f5efe6", color: "#1f2937" }}>{children}</body>
    </html>
  );
}