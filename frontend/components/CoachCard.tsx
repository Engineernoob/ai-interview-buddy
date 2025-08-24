'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Lightbulb, MessageSquare, Loader2 } from 'lucide-react'

type CoachingData = {
  bullets: string[]
  follow_up: string
  transcript?: string
}

type CoachCardProps = {
  data: CoachingData | null
  isLoading: boolean
}

export function CoachCard({ data, isLoading }: CoachCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            AI Coach
          </CardTitle>
          <CardDescription>
            Analyzing your response and generating suggestions...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="ml-2 text-sm text-gray-600">Generating coaching tips...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            AI Coach
          </CardTitle>
          <CardDescription>
            Your personalized interview coaching will appear here
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
              <MessageSquare className="w-8 h-8 text-blue-500" />
            </div>
            <p className="text-sm text-gray-600">
              Start recording to receive AI-powered coaching suggestions based on your resume and the job description.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-500" />
          AI Coach Suggestions
        </CardTitle>
        <CardDescription>
          Personalized tips based on your resume and the job requirements
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Bullet Point Suggestions */}
        {data.bullets && data.bullets.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              Key Points to Mention
            </h3>
            <ul className="space-y-2">
              {data.bullets.map((bullet, index) => (
                <li 
                  key={index}
                  className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border-l-3 border-blue-500"
                >
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span className="text-sm text-gray-800 leading-relaxed">{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Follow-up Question */}
        {data.follow_up && (
          <div>
            <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-green-600" />
              Suggested Follow-up
            </h3>
            <div className="p-4 bg-green-50 rounded-lg border-l-3 border-green-500">
              <p className="text-sm text-gray-800 leading-relaxed italic">
                "{data.follow_up}"
              </p>
            </div>
          </div>
        )}
        
        {/* Response Context (if available) */}
        {data.transcript && (
          <div className="pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Based on your response: "{data.transcript.substring(0, 100)}..."
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}