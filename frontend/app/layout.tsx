import { AuthProvider } from "@/lib/auth";

export const metadata = {
  title: "Decisio",
  description: "AI that turns any meeting into action",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#0b0f14", color: "#e6edf3" }}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
