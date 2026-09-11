import type { TopicItem } from '../lib/types'

interface TopicCardProps {
  topic: TopicItem
  rank: number
  totalYears: number
  style?: React.CSSProperties
}

function frequencyLabel(score: number) {
  if (score >= 0.7) return { label: 'Very High', cls: 'badge-high' }
  if (score >= 0.4) return { label: 'High', cls: 'badge-medium' }
  return { label: 'Moderate', cls: 'badge-low' }
}

export default function TopicCard({ topic, rank, totalYears, style }: TopicCardProps) {
  const freq = frequencyLabel(topic.frequency_score)
  const pct = Math.round(topic.frequency_score * 100)
  const marksPct = Math.round(topic.marks_weight * 100)

  return (
    <div
      className="card hover:shadow-card-hover transition-all duration-200 cursor-default"
      style={style}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {/* Rank badge */}
          <span className="flex-shrink-0 w-8 h-8 bg-navy rounded-lg flex items-center justify-center text-white text-sm font-bold">
            {rank}
          </span>
          <div className="min-w-0">
            <h3 className="font-display text-navy text-base font-semibold leading-tight truncate">
              {topic.name}
            </h3>
            <p className="text-xs text-navy-400 mt-0.5">
              {topic.appeared_in_years.length > 0
                ? `Appeared in: ${topic.appeared_in_years.join(', ')}`
                : 'Pattern detected from questions'}
            </p>
          </div>
        </div>
        <span className={`flex-shrink-0 ${freq.cls}`}>{freq.label}</span>
      </div>

      {/* Bars */}
      <div className="mt-4 space-y-2">
        <div>
          <div className="flex justify-between text-xs text-navy-500 mb-1">
            <span>Repeat frequency</span>
            <span className="font-semibold text-navy">{pct}%</span>
          </div>
          <div className="h-2 bg-navy-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-navy rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs text-navy-500 mb-1">
            <span>Marks weight</span>
            <span className="font-semibold text-gold">{marksPct}%</span>
          </div>
          <div className="h-2 bg-gold-50 rounded-full overflow-hidden">
            <div
              className="h-full bg-gold rounded-full transition-all duration-700"
              style={{ width: `${marksPct}%` }}
            />
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-navy-400">
        <span>Est. prep: <strong className="text-navy">{topic.prep_time_hrs}h</strong></span>
        {totalYears > 0 && (
          <span>{topic.appeared_in_years.length} of {totalYears} years</span>
        )}
      </div>
    </div>
  )
}
