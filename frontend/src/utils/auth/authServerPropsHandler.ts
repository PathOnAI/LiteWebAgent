// utils/auth/authServerPropsHandler.ts

import { GetServerSidePropsContext } from "next";
import { createClient } from "@/utils/supabase/server-props";

export function parseAuthTokenFromCookie(
  cookieValue: string | undefined
): string | null {
  if (!cookieValue) return null;

  try {
    const decoded = Buffer.from(
      cookieValue.replace("base64-", ""),
      "base64"
    ).toString();
    const tokenData = JSON.parse(decoded);
    return tokenData.access_token || null;
  } catch (error) {
    console.error("Error parsing auth cookie:", error);
    return null;
  }
}

// Helper to handle auth redirects in getServerSideProps
export async function withServerPropsAuth<T>(
  context: GetServerSidePropsContext,
  handler: (user: any, accessToken: string) => Promise<{ props: T }>
) {
  try {
    const supabase = createClient(context);
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      return {
        redirect: {
          destination: "/login",
          permanent: false,
        },
      };
    }

    // Get access token from cookie
    const projectRef = process.env.SUPABASE_PROJECT_ID;
    const authCookie = context.req.cookies[`sb-${projectRef}-auth-token`];
    const accessToken = parseAuthTokenFromCookie(authCookie);

    if (!accessToken) {
      return {
        redirect: {
          destination: "/login",
          permanent: false,
        },
      };
    }

    return await handler(user, accessToken);
  } catch (error) {
    console.error("Server-side auth error:", error);
    return {
      redirect: {
        destination: "/login",
        permanent: false,
      },
    };
  }
}

export async function makeServerPropsAuthRequest(
  context: GetServerSidePropsContext,
  endpoint: string,
  options: {
    method?: string;
    body?: any;
    params?: Record<string, string>;
  } = {}
) {
  try {
    // 1. Get Supabase client and check user
    const supabase = createClient(context);
    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      throw new Error("Not authenticated");
    }

    // 2. Get access token from cookie
    const projectRef = process.env.SUPABASE_PROJECT_ID;
    const authCookie = context.req.cookies[`sb-${projectRef}-auth-token`];
    const accessToken = parseAuthTokenFromCookie(authCookie);

    if (!accessToken) {
      throw new Error("No valid auth token found");
    }

    // 3. Construct URL with query parameters
    const url = new URL(`${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}`);
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }


    // 4. Make the request with authentication
    const response = await fetch(url.toString(), {
      method: options.method || "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      ...(options.body ? { body: JSON.stringify(options.body) } : {}),
    });
    console.log("response", response);

    if (!response.ok) {
      throw new Error(`Backend request failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Server-side backend request error:", error);
    throw error;
  }
}
