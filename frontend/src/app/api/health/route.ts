import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  return Response.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    checks: {
      api_keys: {
        groq: !!process.env.GROQ_API_KEY,
        huggingface: !!process.env.HUGGINGFACE_API_KEY,
      },
      database: {
        status: process.env.DATABASE_URL_SYNC ? "configured" : "missing",
      },
    },
    version: "2.0.0",
    engine: "nextjs-native",
  });
}
