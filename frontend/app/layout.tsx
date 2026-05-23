import type { Metadata } from "next";
import "./globals.css";
import { Atmosphere } from "@/components/Atmosphere";
import { AppLayout } from "@/components/AppLayout";
import { NavigationProgress } from "@/components/NavigationProgress";
import { criticalCss } from "@/lib/critical-css";

export const metadata: Metadata = {
  title: "Churn Prediction Dashboard",
  description: "Model comparison dashboard for churn prediction.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <style dangerouslySetInnerHTML={{ __html: criticalCss }} />
      </head>
      <body>
        <NavigationProgress />
        <Atmosphere />
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
