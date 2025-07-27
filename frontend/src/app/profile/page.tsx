// frontend/src/app/profile/page.tsx
'use client'

import { useSession } from '@/contexts/SessionContext'
import { useRouter } from 'next/navigation'
import { AuthGuard } from '@/components/AuthGuard'

// Shadcn/UI imports
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

function ProfileContent() {
  const { state, logout } = useSession()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const user = state.user

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Your Profile</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Full Name */}
          <div className="space-y-1">
            <Label htmlFor="full-name">Full Name</Label>
            <p id="full-name" className="text-lg font-medium">
              {user.first_name} {user.last_name}
            </p>
          </div>

          <Separator />

          {/* Email */}
          <div className="space-y-1">
            <Label htmlFor="email">Email</Label>
            <p id="email" className="text-lg font-medium">
              {user.email}
            </p>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-2 pt-4">
          <Button
            variant="secondary"
            onClick={() => router.push('/profile/edit-profile')}
            className="w-full"
          >
            Edit Profile
          </Button>
          <Button
            variant="destructive"
            onClick={handleLogout}
            className="w-full"
          >
            Log Out
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileContent />
    </AuthGuard>
  )
}
