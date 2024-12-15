// pages/api/deepgram.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { DeepgramError, createClient } from "@deepgram/sdk";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Development environment check
  if (process.env.DEEPGRAM_ENV === "development") {
    return res.status(200).json({
      key: process.env.DEEPGRAM_API_KEY ?? "",
    });
  }

  console.log(process.env.DEEPGRAM_API_KEY)

  // Initialize Deepgram client
  const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

  try {
    // Get projects
    const { result: projectsResult, error: projectsError } = 
      await deepgram.manage.getProjects();

    if (projectsError) {
      return res.status(400).json(projectsError);
    }

    const project = projectsResult?.projects[0];
    if (!project) {
      return res.status(404).json(
        new DeepgramError(
          "Cannot find a Deepgram project. Please create a project first."
        )
      );
    }

    // Create new project key
    const { result: newKeyResult, error: newKeyError } = 
      await deepgram.manage.createProjectKey(project.project_id, {
        comment: "Temporary API key",
        scopes: ["usage:write"],
        tags: ["next.js"],
        time_to_live_in_seconds: 60,
      });

    if (newKeyError) {
      return res.status(400).json(newKeyError);
    }

    // Set headers
    res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate");
    res.setHeader("Pragma", "no-cache");
    res.setHeader("Expires", "0");

    // Send response
    return res.status(200).json({ 
      ...newKeyResult, 
      url: req.url 
    });

  } catch (error) {
    console.error('Error in Deepgram API route:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}