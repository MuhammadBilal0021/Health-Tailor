import type { Metadata } from "next";
import { Provider } from "@/lib/store";
import "./globals.css";
export const metadata: Metadata = {
  title: {
    default: "Health Tailor · Food that fits your life",
    template: "%s · Health Tailor",
  },
  description:
    "A bilingual graduation project connecting thoughtful food discovery, dietary preferences and restaurant ordering.",
  robots: { index: true, follow: true },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
