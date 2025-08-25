'use client'

import React, { useEffect, useState } from 'react'
import { AlertCircle, X, RefreshCw } from 'lucide-react'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { cn } from '@/lib/utils'

export interface ErrorToastProps {
  error: {
    message: string
    code?: string
    context?: string
  }
  onClose: () => void
  onRetry?: () => void
  duration?: number
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}

export function ErrorToast({ 
  error, 
  onClose, 
  onRetry, 
  duration = 8000,
  position = 'top-right' 
}: ErrorToastProps) {
  const [isVisible, setIsVisible] = useState(true)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [duration])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => {
      setIsVisible(false)
      onClose()
    }, 300)
  }

  const handleRetry = () => {
    if (onRetry) {
      onRetry()
      handleClose()
    }
  }

  if (!isVisible) return null

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  }

  return (
    <div className={cn(
      "fixed z-50 transition-all duration-300",
      positionClasses[position],
      isExiting ? 'opacity-0 translate-x-2' : 'opacity-100 translate-x-0'
    )}>
      <Card className="max-w-sm w-full bg-red-50 border-red-200 shadow-lg">
        <div className="p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800 mb-1">
                    Error {error.code && `(${error.code})`}
                  </p>
                  <p className="text-sm text-red-700 break-words">
                    {error.message}
                  </p>
                  {error.context && (
                    <p className="text-xs text-red-600 mt-1 opacity-75">
                      Context: {error.context}
                    </p>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClose}
                  className="h-6 w-6 p-0 text-red-600 hover:text-red-800 hover:bg-red-100"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              {onRetry && (
                <div className="mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRetry}
                    className="h-8 text-xs border-red-300 text-red-700 hover:bg-red-100"
                  >
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Try Again
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

// Toast container for managing multiple error toasts
export function ErrorToastContainer({ 
  errors, 
  onDismiss, 
  onRetry 
}: {
  errors: Array<{ id: string; error: ErrorToastProps['error']; onRetry?: () => void }>
  onDismiss: (id: string) => void
  onRetry?: (id: string) => void
}) {
  return (
    <>
      {errors.map((errorItem, index) => (
        <div
          key={errorItem.id}
          style={{
            transform: `translateY(${index * 80}px)`
          }}
        >
          <ErrorToast
            error={errorItem.error}
            onClose={() => onDismiss(errorItem.id)}
            onRetry={errorItem.onRetry || (onRetry ? () => onRetry(errorItem.id) : undefined)}
            position="top-right"
          />
        </div>
      ))}
    </>
  )
}