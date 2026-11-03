import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found">
      <p className="eyebrow">404 / HEALTH TAILOR</p>
      <h1>
        This page went
        <br />
        <em>off the menu.</em>
      </h1>
      <p>Let’s find you something good.</p>
      <Link className="button" href="/explore">
        Explore the menu →
      </Link>
    </main>
  );
}
