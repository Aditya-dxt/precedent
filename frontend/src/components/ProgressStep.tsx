import { CheckCircle, Circle, Loader } from 'lucide-react'

interface Step {
  id: string
  label: string
  description: string
}

interface ProgressStepProps {
  steps: Step[]
  currentStep: string
  progress: number
}

const STEP_ORDER = [
  'pending', 'parsing', 'parsing_pyqs', 'embedding',
  'saving', 'planning', 'generating_papers', 'done'
]

export default function ProgressStep({ steps, currentStep, progress }: ProgressStepProps) {
  const currentIndex = STEP_ORDER.indexOf(currentStep)

  return (
    <div className="space-y-3">
      {steps.map((step, i) => {
        const stepIndex = STEP_ORDER.indexOf(step.id)
        const isDone = stepIndex < currentIndex || currentStep === 'done'
        const isActive = step.id === currentStep
        const isPending = stepIndex > currentIndex

        return (
          <div
            key={step.id}
            className={`flex items-start gap-3 p-3 rounded-xl transition-all duration-300 ${
              isActive ? 'bg-navy-50 border border-navy-200' :
              isDone   ? 'opacity-70' : 'opacity-30'
            }`}
          >
            <div className="mt-0.5 flex-shrink-0">
              {isDone ? (
                <CheckCircle size={18} className="text-green-500" />
              ) : isActive ? (
                <Loader size={18} className="text-navy animate-spin" />
              ) : (
                <Circle size={18} className="text-navy-300" />
              )}
            </div>
            <div>
              <p className={`text-sm font-medium ${isActive ? 'text-navy' : isDone ? 'text-navy-600' : 'text-navy-400'}`}>
                {step.label}
              </p>
              {isActive && (
                <p className="text-xs text-navy-500 mt-0.5">{step.description}</p>
              )}
            </div>
          </div>
        )
      })}

      {/* Progress bar */}
      <div className="mt-4 bg-navy-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-navy to-gold rounded-full transition-all duration-700"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-center text-xs text-navy-500">{progress}% complete</p>
    </div>
  )
}
