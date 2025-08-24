'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, FileText, Briefcase, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Home() {
  const [resume, setResume] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleResumeUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      setResume(file)
    } else {
      alert('Please upload a PDF file')
    }
  }

  const handleStartInterview = async () => {
    if (!resume || !jobDescription.trim()) {
      alert('Please upload your resume and enter the job description')
      return
    }

    setIsLoading(true)
    
    // Upload resume and job description to backend
    const formData = new FormData()
    formData.append('resume', resume)
    formData.append('job_description', jobDescription)

    try {
      const apiUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/upload'
        : '/api/upload'
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        router.push('/interview')
      } else {
        alert('Failed to upload documents. Please try again.')
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12 max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Interview Buddy
          </h1>
          <p className="text-lg text-gray-600">
            Upload your resume and job description to get personalized interview coaching
          </p>
        </div>

        <div className="space-y-6">
          {/* Resume Upload Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Upload Resume
              </CardTitle>
              <CardDescription>
                Upload your resume in PDF format for personalized suggestions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-2 text-gray-500" />
                    <p className="mb-2 text-sm text-gray-500">
                      {resume ? (
                        <span className="font-semibold text-blue-600">{resume.name}</span>
                      ) : (
                        <>
                          <span className="font-semibold">Click to upload</span> your resume
                        </>
                      )}
                    </p>
                    <p className="text-xs text-gray-500">PDF files only</p>
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleResumeUpload}
                  />
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Job Description Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-600" />
                Job Description
              </CardTitle>
              <CardDescription>
                Paste the job description to get targeted interview preparation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <textarea
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </CardContent>
          </Card>

          {/* Start Interview Button */}
          <div className="text-center">
            <Button
              onClick={handleStartInterview}
              disabled={!resume || !jobDescription.trim() || isLoading}
              size="lg"
              className="px-8 py-3 text-lg"
            >
              {isLoading ? (
                'Preparing...'
              ) : (
                <>
                  Start Interview
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}