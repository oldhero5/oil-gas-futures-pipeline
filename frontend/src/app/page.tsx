import KeyMetrics from '@/components/dashboard/KeyMetrics';
import Alerts from '@/components/dashboard/Alerts';
import SystemStatus from '@/components/dashboard/SystemStatus';

export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-[var(--accent)] mb-6">
        Dashboard Overview
      </h1>

      <KeyMetrics />
      <Alerts />
      <SystemStatus />
    </div>
  );
}
