type Props = {
  label: string;
  value: string | number;
  note?: string;
  tone?: 'info' | 'good' | 'warn' | 'accent';
};

export default function KPI({ label, value, note, tone = 'info' }: Props) {
  return (
    <div className={`kpi-card tone-${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {note && <div className="kpi-note">{note}</div>}
    </div>
  );
}
