import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body className="antialiased">
        <Main />
        <NextScript />
        <script async src="https://cdn.tailwindcss.com"></script>
      </body>
    </Html>
  );
}
