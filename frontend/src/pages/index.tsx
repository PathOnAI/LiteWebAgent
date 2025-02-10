import { useState } from "react"
import Playground from "./playground"
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from "@/components/ui/button"
import { AlertCircle } from 'lucide-react'

export default function Page() {
  const [showWelcomeModal, setShowWelcomeModal] = useState(true)

  return (
    <>
      <Playground 
        initialSteps_={[]} 
        processId="x" 
        onSessionEnd={() => console.log('done')} 
      />
      
      <AlertDialog open={showWelcomeModal} onOpenChange={setShowWelcomeModal}>
        <AlertDialogContent className="max-w-xl !bg-white/95">
          <div className="space-y-4">
            <AlertDialogTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-yellow-500" />
              Important Notice
            </AlertDialogTitle>
            <AlertDialogDescription className="text-gray-700 text-base leading-relaxed">
              We are using the BrowserBase hobby plan 🔄, which only supports 3 concurrent browsers. If you are not able to get the web agent up and running ⚠️, it is most likely because someone else is using a remote BrowserBase browser 💻. The BrowserBase startup and scale plans 💰 are too expensive for our open source project 🔓.
            </AlertDialogDescription>
            <div className="flex justify-end pt-4">
              <Button 
                onClick={() => setShowWelcomeModal(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                I Understand
              </Button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}