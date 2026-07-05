import { NextRequest } from "next/server";
import { Pool } from "pg";
import OpenAI from "openai";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL_SYNC!.replace(
    "postgresql+asyncpg://",
    "postgresql://"
  ),
  ssl: { rejectUnauthorized: false },
  max: 1,
});

const groq = new OpenAI({
  apiKey: process.env.GROQ_API_KEY!,
  baseURL: "https://api.groq.com/openai/v1",
});

export async function POST(request: NextRequest) {
  const startMs = Date.now();
  try {
    const { query } = await request.json();
    if (!query || typeof query !== "string") {
      return Response.json({ error: "query is required" }, { status: 400 });
    }

    // Fetch relevant reviews from DB (keyword search fallback)
    const keywords = query
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, " ")
      .split(" ")
      .filter((w) => w.length > 3)
      .slice(0, 5);

    let reviews: any[] = [];
    try {
      const client = await pool.connect();
      try {
        const conditions = keywords
          .map((_, i) => `(body ILIKE $${i + 1} OR key_frustration_phrase ILIKE $${i + 1})`)
          .join(" OR ");
        const values = keywords.map((k) => `%${k}%`);
        const sql =
          keywords.length > 0
            ? `SELECT id, body, source, published_at, rating, sentiment, segment, key_frustration_phrase, unmet_need
               FROM classified_reviews
               WHERE ${conditions}
               ORDER BY published_at DESC NULLS LAST
               LIMIT 20`
            : `SELECT id, body, source, published_at, rating, sentiment, segment, key_frustration_phrase, unmet_need
               FROM classified_reviews
               ORDER BY published_at DESC NULLS LAST
               LIMIT 20`;
        const result = await client.query(sql, keywords.length > 0 ? values : []);
        reviews = result.rows;
      } finally {
        client.release();
      }
    } catch (dbErr: any) {
      console.error("DB error:", dbErr.message);
      // Continue with empty reviews — Groq will still give an answer
    }

    // Build context from reviews
    const context =
      reviews.length > 0
        ? reviews
            .map(
              (r, i) =>
                `[${i + 1}] Source: ${r.source} | Sentiment: ${r.sentiment} | Segment: ${r.segment}\nFrustration: ${r.key_frustration_phrase}\nUnmet Need: ${r.unmet_need}\nBody: ${(r.body || "").slice(0, 300)}`
            )
            .join("\n\n")
        : "No specific reviews found. Please provide a general answer based on common Spotify user feedback patterns.";

    // Call Groq
    const systemPrompt = `You are a product intelligence analyst for Spotify. You analyze user reviews to surface insights for the Spotify growth team. Answer questions concisely based on the review data provided. Be specific and evidence-based.`;
    const userPrompt = `User Question: ${query}\n\nReview Evidence:\n${context}\n\nProvide a structured analysis with:\n1. A direct answer (2-3 sentences)\n2. Key themes from the evidence\n3. 2-3 follow-up questions a PM might ask`;

    let answer = "Unable to generate AI response.";
    let followUpQuestions: string[] = [];

    try {
      const completion = await groq.chat.completions.create({
        model: "llama3-70b-8192",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        max_tokens: 800,
        temperature: 0.3,
      });
      const raw = completion.choices[0]?.message?.content || "";
      answer = raw;

      // Extract follow-up questions heuristically
      const lines = raw.split("\n").filter((l) => l.trim().endsWith("?"));
      followUpQuestions = lines.slice(0, 3).map((l) => l.replace(/^\d+\.\s*/, "").trim());
    } catch (aiErr: any) {
      console.error("Groq error:", aiErr.message);
      answer = reviews.length > 0
        ? `Found ${reviews.length} relevant reviews. Top frustration: "${reviews[0]?.key_frustration_phrase}". Unmet need: "${reviews[0]?.unmet_need}".`
        : "No matching reviews found for your query.";
    }

    // Build evidence list
    const evidence = reviews.slice(0, 5).map((r) => ({
      text: r.key_frustration_phrase || r.body?.slice(0, 200) || "",
      source: r.source || "unknown",
      date: r.published_at ? new Date(r.published_at).toISOString().split("T")[0] : undefined,
    }));

    return Response.json({
      answer,
      evidence,
      confidence: reviews.length > 5 ? "high" : reviews.length > 0 ? "medium" : "low",
      confidence_reason:
        reviews.length > 0
          ? `Based on ${reviews.length} matching reviews`
          : "No matching reviews found",
      follow_up_questions: followUpQuestions,
      result_count: reviews.length,
      query_time_ms: Date.now() - startMs,
    });
  } catch (err: any) {
    console.error("Query route error:", err);
    return Response.json(
      { error: "Internal server error", detail: err.message },
      { status: 500 }
    );
  }
}
