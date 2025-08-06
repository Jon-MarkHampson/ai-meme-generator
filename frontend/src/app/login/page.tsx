// frontend/src/app/login/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useSession } from '@/contexts/SessionContext';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { DEFAULT_PROTECTED_ROUTE } from '@/config/routes';
import { apiLogin } from '@/services/auth';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel } from '@/components/ui/form';
import { Input } from '@/components/ui/input';

const formSchema = z.object({
  email: z.string().email({ message: 'Enter a valid email.' }),
  password: z.string().min(1, { message: 'Enter your password.' }),
});
type FormValues = z.infer<typeof formSchema>;

export default function LoginPage() {
  const { state, revalidateSession } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: ''
    },
    mode: 'onChange'
  });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    setIsSubmitting(true);

    try {
      // Call login API
      await apiLogin(values.email, values.password);

      // Revalidate session to update state immediately
      await revalidateSession();

      // Success! The SessionContext will detect the new session
      // toast.success('Welcome back!');

      // Redirect to intended destination
      const redirect = searchParams.get('redirect');
      const redirectTo = redirect || DEFAULT_PROTECTED_ROUTE;

      // Use router.push for client-side navigation
      router.push(redirectTo);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string }; status?: number } };
      const msg = error.response?.data?.detail || 'Login failed. Please check your credentials.';

      setFormError(msg);
      toast.error(msg);

      if (error.response?.status === 401) {
        form.resetField('password');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  // Handle authenticated users
  useEffect(() => {
    if (state.isAuthenticated && state.user && !state.isValidating) {
      const redirect = searchParams.get('redirect');
      const redirectTo = redirect || DEFAULT_PROTECTED_ROUTE;
      router.replace(redirectTo);
    }
  }, [state.isAuthenticated, state.user, state.isValidating, searchParams, router]);

  // Show loading state during session validation
  if (state.isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {/* Hidden heading for screen readers */}
      <h1 className="sr-only">Log In</h1>

      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Log In</CardTitle>
        </CardHeader>

        <CardContent>
          {formError && (
            <p
              role="alert"
              aria-live="assertive"
              className="mb-4 text-center text-sm text-red-600"
            >
              {formError}
            </p>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Email */}
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="john@example.com"
                        disabled={isSubmitting}
                        autoComplete="username"
                        {...field}
                      />
                    </FormControl>
                    {form.formState.errors.email && (
                      <p className="mt-1 text-sm text-red-600">
                        {form.formState.errors.email.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Password */}
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••••"
                        disabled={isSubmitting}
                        autoComplete="current-password"
                        {...field}
                      />
                    </FormControl>
                    {form.formState.errors.password && (
                      <p className="mt-1 text-sm text-red-600">
                        {form.formState.errors.password.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* Submit Button */}
              <div className="mt-4">
                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? 'Logging In…' : 'Log In'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}