import React, { useRef } from 'react'
import { UploadCloud, FileText, X } from 'lucide-react'

interface UploadZoneProps {
  label: string
  description: string
  accept?: string
  multiple?: boolean
  files: File[]
  onFilesChange: (files: File[]) => void
  required?: boolean
  yearTagging?: boolean
  years?: { [filename: string]: number }
  onYearChange?: (filename: string, year: number) => void
}

export default function UploadZone({
  label,
  description,
  accept = '.pdf',
  multiple = false,
  files,
  onFilesChange,
  required = false,
  yearTagging = false,
  years = {},
  onYearChange,
}: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'))
      if (multiple) {
        onFilesChange([...files, ...droppedFiles])
      } else if (droppedFiles.length > 0) {
        onFilesChange([droppedFiles[0]])
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = Array.from(e.target.files)
      if (multiple) {
        onFilesChange([...files, ...selected])
      } else {
        onFilesChange([selected[0]])
      }
    }
  }

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index)
    onFilesChange(updated)
  }

  const currentYear = new Date().getFullYear()

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-semibold text-navy">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        <span className="text-xs text-navy-400">PDF format</span>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-navy-200 hover:border-gold hover:bg-gold-50/20 transition-colors rounded-2xl p-6 text-center cursor-pointer bg-white"
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="w-12 h-12 mx-auto bg-navy-50 text-navy rounded-full flex items-center justify-center mb-3">
          <UploadCloud size={24} />
        </div>
        <p className="text-sm font-medium text-navy">
          Click to upload or drag and drop
        </p>
        <p className="text-xs text-navy-400 mt-1">{description}</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2 mt-3">
          {files.map((file, idx) => (
            <div
              key={`${file.name}-${idx}`}
              className="flex items-center justify-between p-3 bg-white border border-navy-100 rounded-xl shadow-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 bg-red-50 text-red-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-navy truncate">{file.name}</p>
                  <p className="text-xs text-navy-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {yearTagging && onYearChange && (
                  <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                    <span className="text-xs text-navy-500 font-medium">Exam Year:</span>
                    <input
                      type="number"
                      min={1990}
                      max={currentYear + 1}
                      value={years[file.name] || (currentYear - idx)}
                      onChange={(e) => onYearChange(file.name, parseInt(e.target.value) || currentYear)}
                      className="w-20 px-2 py-1 text-xs border border-navy-200 rounded-md focus:outline-none focus:border-navy text-navy font-semibold"
                    />
                  </div>
                )}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile(idx)
                  }}
                  className="p-1.5 text-navy-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
