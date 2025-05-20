import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { createClient } from '@/utils/supabase/component'
import { Card, CardContent } from "@/components/ui/card"

export default function AuthCallback() {
  const router = useRouter()
  const [message, setMessage] = useState('Processing authentication...')
  const supabase = createClient()
  
  useEffect(() => {
    // Only run once the router is ready and we have query params
    if (!router.isReady) return
    
    const handleAuthCallback = async () => {
      try {
        // Check if we have a session already
        const { data: { session } } = await supabase.auth.getSession()
        
        if (session) {
          setMessage('You are logged in. Redirecting to home page...')
          router.push('/')
          return
        }
        
        // Get the token from the URL if present
        const { token, type } = router.query
        
        if (token) {
          setMessage('Verifying your email...')
          
          // Exchange the token for a session
          const { error } = await supabase.auth.verifyOtp({
            token_hash: token as string,
            type: (type as string || 'signup') as 'signup' | 'email' | 'recovery' | 'invite',
          })
          
          if (error) {
            console.error('Error verifying token:', error)
            setMessage(`Error: ${error.message}`)
            return
          }
          
          setMessage('Email verified! Redirecting to home page...')
          router.push('/')
        } else {
          // No token found, redirect to login
          setMessage('No authentication token found. Redirecting to login...')
          router.push('/login')
        }
      } catch (error) {
        console.error('Auth callback error:', error)
        setMessage('An error occurred during authentication. Please try logging in again.')
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    }
    
    handleAuthCallback()
  }, [router.isReady, router.query, router, supabase])
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 text-center">
          <div className="mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          </div>
          <p>{message}</p>
        </CardContent>
      </Card>
    </div>
  )
} 