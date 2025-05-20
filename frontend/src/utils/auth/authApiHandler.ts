import { NextApiRequest, NextApiResponse } from "next";
import axios, { AxiosRequestConfig } from "axios";
import createClient from "@/utils/supabase/api";

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
interface AuthenticatedRequest extends NextApiRequest {
  user: any;
  accessToken: string;
}

type ApiHandler = (
  req: AuthenticatedRequest,
  res: NextApiResponse
) => Promise<void>;

export function withApiAuth(handler: ApiHandler) {
  return async (req: NextApiRequest, res: NextApiResponse) => {
    try {
      // 1. Validate user
      const supabase = createClient(req, res);
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();

      if (error || !user) {
        return res.status(401).json({ message: "Not authenticated" });
      }

      // 2. Get access token from cookie using shared parser
      const projectRef = process.env.SUPABASE_PROJECT_ID;
      const authCookie = req.cookies[`sb-${projectRef}-auth-token`];
      const accessToken = parseAuthTokenFromCookie(authCookie);

      if (!accessToken) {
        return res.status(401).json({ message: "No valid auth token found" });
      }

      // 3. Extend request with user and token
      (req as AuthenticatedRequest).user = user;
      (req as AuthenticatedRequest).accessToken = accessToken;

      // 4. Call the actual handler
      return await handler(req as AuthenticatedRequest, res);
    } catch (error) {
      console.error("Auth handler error:", error);
      return res.status(500).json({
        message: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      });
    }
  };
}

// Helper function to make authenticated backend requests using axios
export async function makeApiAuthRequest(
  accessToken: string,
  endpoint: string,
  options: {
    method?: string;
    body?: any;
    params?: Record<string, string>;
  } = {}
) {
  const baseURL = process.env.NEXT_PUBLIC_BACKEND_URL;
  
  const config: AxiosRequestConfig = {
    method: options.method || "GET",
    url: endpoint,
    baseURL,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    params: options.params,
    data: options.body,
  };
  console.log("config", config);
  console.log("accessToken", accessToken);

  try {
    const response = await axios(config);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Backend request failed: ${error.response?.statusText || error.message}`);
    }
    throw error;
  }
}