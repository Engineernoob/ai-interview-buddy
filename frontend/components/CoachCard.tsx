type CoachCardProps = {
  bullets: string[]
  followUp?: string
}

export default function CoachCard({ bullets, followUp }: CoachCardProps) {
  return (
    <div className="p-6 rounded-xl bg-gray-800 shadow-lg w-80">
      <h2 className="text-lg font-semibold mb-2">AI Suggestions</h2>
      <ul className="space-y-2">
        {bullets.map((b: string, i: number) => <li key={i}>• {b}</li>)}
      </ul>
      {followUp && <p className="text-sm mt-3 text-gray-400">Ask: {followUp}</p>}
    </div>
  );
}
