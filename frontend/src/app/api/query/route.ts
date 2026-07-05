import { NextRequest } from "next/server";

// Lazy pool — only created at request time, never at build time
let pool: any = null;

function getPool() {
  if (!pool) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { Pool } = require("pg");
    const connStr = process.env.DATABASE_URL_SYNC || "";
    if (!connStr) return null;
    pool = new Pool({
      connectionString: connStr.replace("postgresql+asyncpg://", "postgresql://"),
      ssl: { rejectUnauthorized: false },
      max: 2,
    });
  }
  return pool;
}

// Lazy Groq client — same reason
function getGroqClient() {
  if (!process.env.GROQ_API_KEY) return null;
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const OpenAI = require("openai");
  return new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1",
  });
}

export async function POST(request: NextRequest) {
  const startMs = Date.now();
  try {
    const { query } = await request.json();
    if (!query || typeof query !== "string") {
      return Response.json({ error: "query is required" }, { status: 400 });
    }

    // Fetch relevant reviews from DB (keyword search)
    const keywords = query
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, " ")
      .split(" ")
      .filter((w: string) => w.length > 3)
      .slice(0, 5);

    let reviews: any[] = [];
    const db = getPool();
    if (db) {
      try {
        const client = await db.connect();
        try {
          const conditions = keywords
            .map((_: string, i: number) => `(rr.body ILIKE $${i + 1} OR cr.key_frustration_phrase ILIKE $${i + 1})`)
            .join(" OR ");
          const values = keywords.map((k: string) => `%${k}%`);
          const sql =
            keywords.length > 0
              ? `SELECT cr.id, rr.body, rr.source, rr.published_at, rr.rating, cr.sentiment, cr.user_segment_signal as segment, cr.key_frustration_phrase, cr.unmet_need
                 FROM classified_reviews cr
                 JOIN raw_reviews rr ON cr.raw_review_id = rr.id
                 WHERE ${conditions}
                 ORDER BY rr.published_at DESC NULLS LAST
                 LIMIT 20`
              : `SELECT cr.id, rr.body, rr.source, rr.published_at, rr.rating, cr.sentiment, cr.user_segment_signal as segment, cr.key_frustration_phrase, cr.unmet_need
                 FROM classified_reviews cr
                 JOIN raw_reviews rr ON cr.raw_review_id = rr.id
                 ORDER BY rr.published_at DESC NULLS LAST
                 LIMIT 20`;
          const result = await client.query(sql, keywords.length > 0 ? values : []);
          reviews = result.rows;
        } finally {
          client.release();
        }
      } catch (dbErr: any) {
        console.error("DB error:", dbErr.message);
      }
    }

    // Build context
    const context =
      reviews.length > 0
        ? reviews
            .map(
              (r: any, i: number) =>
                `[${i + 1}] Source: ${r.source} | Sentiment: ${r.sentiment} | Segment: ${r.segment}\nFrustration: ${r.key_frustration_phrase}\nUnmet Need: ${r.unmet_need}\nReview: ${(r.body || "").slice(0, 300)}`
            )
            .join("\n\n")
        : "No specific reviews found. Answer based on common Spotify user feedback patterns.";

    // Call Groq
    let answer = "Unable to generate AI response — GROQ_API_KEY may be missing.";
    let followUpQuestions: string[] = [];
    let confidence = reviews.length > 5 ? "High" : reviews.length > 0 ? "Medium" : "Low";
    let confidenceReason = reviews.length > 0 ? `Based on ${reviews.length} matching reviews` : "No matching reviews found";
    let evidence: any[] = [];

    const groq = getGroqClient();
    if (groq) {
      try {
        const completion = await groq.chat.completions.create({
          model: "llama3-70b-8192",
          messages: [
            {
              role: "system",
              content: `You are a product research analyst at Spotify.
Answer the PM's question based ONLY on the provided user feedback data.
Be specific, cite evidence, and structure your answer clearly.

Respond with a JSON object:
{
  "answer": "string (2-3 sentences, direct answer)",
  "evidence": [
    {"text": "quote or finding", "source": "source name", "date": "YYYY-MM-DD"}
  ],
  "confidence": "High / Medium / Low",
  "confidence_reason": "string (why this confidence level)",
  "follow_up_questions": ["string", "string", "string"]
}`,
            },
            {
              role: "user",
              content: `USER QUESTION: ${query}\n\nRELEVANT FEEDBACK DATA:\n${context}`,
            },
          ],
          response_format: { type: "json_object" },
          max_tokens: 800,
          temperature: 0.3,
        });
        const raw = completion.choices[0]?.message?.content || "{}";
        const parsed = JSON.parse(raw);
        
        answer = parsed.answer || answer;
        evidence = parsed.evidence || [];
        confidence = parsed.confidence || confidence;
        confidenceReason = parsed.confidence_reason || confidenceReason;
        followUpQuestions = parsed.follow_up_questions || [];
      } catch (aiErr: any) {
        console.error("Groq error:", aiErr.message);
        answer =
          reviews.length > 0
            ? `Found ${reviews.length} matching reviews. Top frustration: "${reviews[0]?.key_frustration_phrase}". Unmet need: "${reviews[0]?.unmet_need}".`
            : "No matching reviews found.";
      }
    } else if (reviews.length > 0) {
      answer = `Found ${reviews.length} matching reviews. Top frustration: "${reviews[0]?.key_frustration_phrase}". Unmet need: "${reviews[0]?.unmet_need}".`;
    }

    // Fallback evidence if AI didn't provide any or failed
    if (evidence.length === 0 && reviews.length > 0) {
      evidence = reviews.slice(0, 5).map((r: any) => ({
        text: r.key_frustration_phrase || (r.body || "").slice(0, 200),
        source: r.source || "unknown",
        date: r.published_at
          ? new Date(r.published_at).toISOString().split("T")[0]
          : undefined,
      }));
    }

    return Response.json({
      answer,
      evidence,
      confidence,
      confidence_reason: confidenceReason,
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
