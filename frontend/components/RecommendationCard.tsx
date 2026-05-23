export function RecommendationCard({
  title,
  body,
  tone = "blue",
}: {
  title: string;
  body: string;
  tone?: "blue" | "amber" | "green";
}) {
  const styles = {
    blue: "border-mint/50 bg-gradient-to-br from-[#e9fbf7] to-panel text-[#1f4f4c]",
    amber: "border-apricot/50 bg-[#fff6e7] text-[#7a4a12]",
    green: "border-mint/50 bg-mint/15 text-[#1f4f4c]",
  };

  return (
    <section className={`rounded-xl border p-5 shadow-soft ${styles[tone]}`}>
      <p className="text-sm font-semibold uppercase tracking-wide opacity-80">{title}</p>
      <p className="mt-2 text-base font-semibold leading-7">{body}</p>
    </section>
  );
}
