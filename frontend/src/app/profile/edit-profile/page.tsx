// frontend/src/app/profile/edit-profile/page.tsx
'use client';

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import { AuthGuard } from "@/components/AuthGuard";
import { useSession } from "@/contexts/SessionContext";
import { apiUpdateProfile, apiDeleteAccount } from "@/services/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { CheckCircle2, AlertCircle } from "lucide-react";
import { ApiError } from "@/types/api-error";


/**
 * 1) currentPassword is REQUIRED (always sent as current_password to backend).
 * 2) firstName, lastName, email, password, confirmPassword are all optional.
 * 3) If password is non‐empty, confirmPassword must match.
 * 4) At least one of (firstName, lastName, email, password) must be present.
 */
const formSchema = z
  .object({
    currentPassword: z
      .string()
      .min(1, { message: "Current password is required." }),

    firstName: z
      .string()
      .min(1, { message: "First name must be at least 1 character." })
      .optional(),

    lastName: z
      .string()
      .min(1, { message: "Last name must be at least 1 character." })
      .optional(),

    email: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .refine((v) => v === undefined || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), {
        message: "Please enter a valid email.",
      })
      .optional(),

    password: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .refine((v) => v === undefined || v.length >= 6, {
        message: "New password must be at least 6 characters.",
      })
      .optional(),

    confirmPassword: z
      .string()
      .transform((v) => (v === "" ? undefined : v))
      .optional(),
  })
  .refine(
    (data) => {
      if (data.password !== undefined) {
        return data.confirmPassword !== undefined && data.password === data.confirmPassword;
      }
      return true;
    },
    {
      message: "Passwords do not match.",
      path: ["confirmPassword"],
    }
  )
  .refine(
    (data) => {
      // Make sure at least one of firstName/lastName/email/password was provided
      return (
        data.firstName !== undefined ||
        data.lastName !== undefined ||
        data.email !== undefined ||
        data.password !== undefined
      );
    },
    {
      message: "Please change at least one field.",
      path: [],
    }
  );

type FormValues = z.infer<typeof formSchema>;

function EditProfileContent() {
  const router = useRouter();
  const { state, logout, revalidateSession } = useSession();
  const user = state.user;

  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<boolean>(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Cleanup ref for unmount during async operations
  const isMountedRef = useRef(true);

  // Initialize React Hook Form with camelCase defaults,
  // but defaultValues pull from user.first_name / user.last_name
  const methods = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      currentPassword: "",
      firstName: user?.first_name || "",
      lastName: user?.last_name || "",
      email: user?.email || "",
      password: "",
      confirmPassword: "",
    },
  });

  // Track which fields have been modified
  const [modifiedFields, setModifiedFields] = useState<Set<string>>(new Set());

  // Watch for field changes to track modifications
  useEffect(() => {
    const subscription = methods.watch((value, { name }) => {
      if (!name || !user) return;

      const newModified = new Set(modifiedFields);

      // Check if field differs from original
      if (name === "firstName" && value.firstName !== user.first_name) {
        newModified.add("firstName");
      } else if (name === "firstName") {
        newModified.delete("firstName");
      }

      if (name === "lastName" && value.lastName !== user.last_name) {
        newModified.add("lastName");
      } else if (name === "lastName") {
        newModified.delete("lastName");
      }

      if (name === "email" && value.email !== user.email) {
        newModified.add("email");
      } else if (name === "email") {
        newModified.delete("email");
      }

      if (name === "password" && value.password) {
        newModified.add("password");
      } else if (name === "password") {
        newModified.delete("password");
      }

      setModifiedFields(newModified);
    });

    return () => subscription.unsubscribe();
  }, [methods, user, modifiedFields]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  async function onSubmit(values: FormValues) {
    setUpdateError(null);
    setUpdateSuccess(false);
    setIsUpdating(true);

    // Build a payload to match the API signature
    const payload: {
      current_password: string;
      first_name?: string;
      last_name?: string;
      email?: string;
      password?: string;
    } = {
      current_password: values.currentPassword,
    };

    // Only include fields that actually changed
    if (values.firstName !== undefined && values.firstName !== user?.first_name) {
      payload.first_name = values.firstName;
    }
    if (values.lastName !== undefined && values.lastName !== user?.last_name) {
      payload.last_name = values.lastName;
    }
    if (values.email !== undefined && values.email !== user?.email) {
      payload.email = values.email;
    }
    if (values.password) {
      payload.password = values.password;
    }

    try {
      const updatedUser = await apiUpdateProfile(payload);

      // Immediately set success and stop loading
      setUpdateSuccess(true);
      setIsUpdating(false);

      // Clear sensitive form fields
      methods.setValue("currentPassword", "");
      methods.setValue("password", "");
      methods.setValue("confirmPassword", "");

      // Try to refresh session data in the background (non-blocking)
      revalidateSession().catch(err => {
        console.warn("Failed to revalidate session after profile update:", err);
      });

      // Navigate after a short delay to show success message
      setTimeout(() => {
        router.push("/profile");
      }, 1500);
    } catch (err: unknown) {
      const error = err as ApiError;
      if (isMountedRef.current) {
        setIsUpdating(false);
        // Provide specific error messages based on status
        if (error.response?.status === 400 && error.response?.data?.detail?.includes("Email already")) {
          setUpdateError("This email is already registered to another account.");
        } else if (error.response?.status === 401) {
          setUpdateError("Current password is incorrect.");
        } else {
          setUpdateError(error.response?.data?.detail || "Failed to update profile. Please try again.");
        }
      }
    }
  }

  async function handleDeleteAccount() {
    setDeleteError(null);
    setIsDeleting(true);
    try {
      await apiDeleteAccount(deletePassword);
      if (isMountedRef.current) {
        await logout();
        router.push("/");
      }
    } catch (err: unknown) {
      const error = err as ApiError;
      if (isMountedRef.current) {
        if (error.response?.status === 401 || error.response?.status === 400) {
          setDeleteError("Incorrect password. Please try again.");
        } else {
          setDeleteError(error.response?.data?.detail || "Failed to delete account. Please try again.");
        }
      }
    } finally {
      if (isMountedRef.current) {
        setIsDeleting(false);
      }
    }
  }

  // Show loading state while session is validating
  if (state.isValidating || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-foreground"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md">
        {/* — Update Profile Section — */}
        <CardHeader>
          <CardTitle className="text-center">Update Your Account</CardTitle>
          <p className="text-center text-sm text-muted-foreground">
            Optionally update your name, email, or password.
            <br />
            (Current password is required to save changes.)
          </p>
        </CardHeader>

        <CardContent>
          {updateError && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{updateError}</AlertDescription>
            </Alert>
          )}

          {updateSuccess && (
            <Alert className="mb-4 border-green-500/20 bg-green-500/10">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertTitle className="text-green-600 dark:text-green-400">Success!</AlertTitle>
              <AlertDescription className="text-green-600/90 dark:text-green-400/90">
                Your profile has been updated successfully.
              </AlertDescription>
            </Alert>
          )}

          {/* ========= Wrap <form> inside Shadcn/UI's <Form> for RHF context ========= */}
          <Form {...methods}>
            <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
              {/* — Current Password (always required) — */}
              <FormField
                control={methods.control}
                name="currentPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Current Password <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Enter your current password"
                        aria-label="Current password"
                        aria-required="true"
                        aria-invalid={!!methods.formState.errors.currentPassword}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.currentPassword && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.currentPassword.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — First Name (optional) — */}
              <FormField
                control={methods.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      First Name
                      {modifiedFields.has("firstName") && (
                        <span className="ml-2 text-xs text-primary">(modified)</span>
                      )}
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={user.first_name}
                        aria-label="First name"
                        aria-invalid={!!methods.formState.errors.firstName}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.firstName && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.firstName.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Last Name (optional) — */}
              <FormField
                control={methods.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Last Name
                      {modifiedFields.has("lastName") && (
                        <span className="ml-2 text-xs text-primary">(modified)</span>
                      )}
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={user.last_name}
                        aria-label="Last name"
                        aria-invalid={!!methods.formState.errors.lastName}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.lastName && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.lastName.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Email (optional) — */}
              <FormField
                control={methods.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Email
                      {modifiedFields.has("email") && (
                        <span className="ml-2 text-xs text-primary">(modified)</span>
                      )}
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder={user.email}
                        aria-label="Email address"
                        aria-invalid={!!methods.formState.errors.email}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.email && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.email.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — New Password (optional) — */}
              <FormField
                control={methods.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      New Password
                      {modifiedFields.has("password") && (
                        <span className="ml-2 text-xs text-primary">(modified)</span>
                      )}
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Enter new password (min 6 characters)"
                        aria-label="New password"
                        aria-invalid={!!methods.formState.errors.password}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.password && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.password.message}
                      </p>
                    )}
                    {field.value && field.value.length > 0 && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Password strength: {field.value.length < 8 ? "Weak" : field.value.length < 12 ? "Medium" : "Strong"}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Confirm New Password (optional) — */}
              <FormField
                control={methods.control}
                name="confirmPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm New Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Retype new password"
                        aria-label="Confirm new password"
                        aria-invalid={!!methods.formState.errors.confirmPassword}
                        {...field}
                      />
                    </FormControl>
                    {methods.formState.errors.confirmPassword && (
                      <p className="mt-1 text-sm text-destructive" role="alert">
                        {methods.formState.errors.confirmPassword.message}
                      </p>
                    )}
                  </FormItem>
                )}
              />

              {/* — Buttons: Save / Cancel — */}
              <div className="mt-6 flex flex-col space-y-2 justify-center">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isUpdating || updateSuccess}
                >
                  {isUpdating ? "Saving…" : updateSuccess ? "Saved!" : "Save Changes"}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => router.push("/profile")}
                  className="w-full"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>

        {/* — Delete Account Section — */}
        <CardContent className="border-t">
          {!confirmDelete ? (
            <div className="flex justify-center mt-4">
              <Button
                variant="destructive"
                className="w-full"
                onClick={() => {
                  setConfirmDelete(true);
                  setDeletePassword("");
                  setDeleteError(null);
                }}
                aria-label="Delete account"
              >
                Delete My Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4 mt-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Warning</AlertTitle>
                <AlertDescription>
                  This action cannot be undone. Your account and all associated data will be permanently deleted.
                </AlertDescription>
              </Alert>

              <p className="text-sm text-destructive text-center font-medium">
                Enter your password to confirm deletion
              </p>

              <div className="space-y-1">
                <label
                  htmlFor="delete-password"
                  className="block text-sm font-medium text-destructive"
                >
                  Password <span aria-label="required">*</span>
                </label>
                <Input
                  id="delete-password"
                  type="password"
                  placeholder="Type your password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="block w-full rounded-md"
                  aria-label="Password for account deletion"
                  aria-required="true"
                  aria-invalid={!!deleteError}
                />
                {deleteError && (
                  <p className="mt-1 text-sm text-destructive text-center" role="alert">
                    {deleteError}
                  </p>
                )}
              </div>

              <div className="flex justify-between">
                <Button
                  variant="destructive"
                  onClick={handleDeleteAccount}
                  disabled={isDeleting || deletePassword === ""}
                  className="flex-1 mr-2"
                  aria-label="Confirm account deletion"
                >
                  {isDeleting ? "Deleting…" : "Confirm Delete"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setConfirmDelete(false);
                    setDeleteError(null);
                    setDeletePassword("");
                  }}
                  className="flex-1 ml-2"
                  aria-label="Cancel account deletion"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


export default function EditProfilePage() {
  return (
    <AuthGuard>
      <EditProfileContent />
    </AuthGuard>
  );
}