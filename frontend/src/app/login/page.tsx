'use client';

import { useContext, useState } from 'react';
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
  const { login } = useContext(AuthContext);
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: '', password: '' },
  });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await login(values.email, values.password);
      router.push('/profile');
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Login failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Log In</CardTitle>
        </CardHeader>
        <CardContent>
          {formError && (
            <p className="mb-4 text-center text-sm text-red-600">{formError}</p>
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
                      <Input type="email" placeholder="john@example.com" {...field} />
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
                      <Input type="password" placeholder="••••••••" {...field} />
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
              <div className="mt-4 flex flex-col space-y-2">
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