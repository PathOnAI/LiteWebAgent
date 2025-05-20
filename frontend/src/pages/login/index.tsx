import { useRouter } from 'next/router';
import { useState } from 'react';
import type { User } from '@supabase/supabase-js';
import type { GetServerSidePropsContext } from 'next';
import { createClient } from '@/utils/supabase/component';
import { createClient as createServerClient } from '@/utils/supabase/server-props';
import { Lock, Mail, LogOut, User as UserIcon } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";

interface LoginPageProps {
  user: User | null;
}

export default function LoginPage({ user: initialUser }: LoginPageProps) {
  const router = useRouter();
  const supabase = createClient();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  
  async function logIn() {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      console.error(error);
      return;
    }
    router.push('/');
  }
  
  async function signUp() {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    
    if (error) {
      console.error(error);
      return;
    }
    
    // Show a message that verification email has been sent
    alert("Check your email for a verification link");
  }

  async function logOut() {
    const { error } = await supabase.auth.signOut();
    if (error) {
      console.error(error);
      return;
    }
    
    setEmail('');
    setPassword('');
    router.push('/login');
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            {initialUser ? 'Account' : 'Welcome back'}
          </CardTitle>
          <CardDescription className="text-center">
            {initialUser ? 'You are currently signed in' : 'Enter your email to sign in to your account'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {initialUser ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2 p-4 bg-gray-50 rounded-lg">
                <UserIcon className="h-5 w-5 text-gray-500" />
                <span className="text-sm text-gray-600">{initialUser.email}</span>
              </div>
              <Button
                type="button"
                variant="destructive"
                className="w-full"
                onClick={logOut}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign Out
              </Button>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    className="pl-10"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    type="password"
                    className="pl-10"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(checked) => setRememberMe(checked === true)}
                />
                <label
                  htmlFor="remember"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Remember me
                </label>
              </div>
              <div className="space-y-2">
                <Button
                  type="button"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                  onClick={logIn}
                >
                  Sign In
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full border-gray-300 hover:bg-gray-100 text-gray-800"
                  onClick={signUp}
                >
                  Sign Up
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  const supabase = createServerClient(context);

  const { data, error } = await supabase.auth.getUser();

  if (error) {
    return {
      props: {
        user: null,
      },
    };
  }

  return {
    props: {
      user: data.user,
    },
  };
}