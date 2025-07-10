'use client';

import { useEffect, useContext, useState } from 'react';
import { AuthContext } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

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
  const { login, user } = useContext(AuthContext);
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: '', password: '' },
  });

  // 1) Redirect away if already logged in
  useEffect(() => {
    if (user) {
      router.replace('/generate');
    }
  }, [user, router]);

  async function onSubmit(values: FormValues) {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await login(values.email, values.password);
      router.push('/generate');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string }; status?: number } };
      const msg = error.response?.data?.detail || 'Login failed.';
      setFormError(msg);
      if (error.response?.status === 401) {
        form.setValue('password', '');
      }
    } finally {
      setIsSubmitting(false);
    }
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