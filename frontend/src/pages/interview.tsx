import { useEffect, useState } from "react";
import CoachCard from "../components/CoachCard";
import { startAudioStream } from "../lib/audioStream";

export default function InterviewPage() {
  const [tips, setTips] = useState<string[]>([]);
  const [follow, setFollow] = useState<string | null>(null);

  useEffect(() => {
    startAudioStream((msg) => {
      const data = JSON.parse(msg);
      setTips(data.bullets || []);
      setFollow(data.follow_up || null);
    });
  }, []);

  return (
    <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
      <CoachCard bullets={tips} followUp={follow} />
    </div>
  );
}
