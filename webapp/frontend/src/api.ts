export async function guestLogin(
  apiBase: string,
  displayName: string,
): Promise<JsonRecord> {
  const response = await fetch(`${apiBase}/api/auth/guest-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName }),
  });
  return parseJson<JsonRecord>(response);
}

export async function tutorChat(
  apiBase: string,
  payload: {
    user_id: string;
    session_id: string;
    user_message: string;
    lesson_id?: string;
    conversation: JsonRecord[];
    memory: JsonRecord;
    exercise_history: JsonRecord[];
  },
): Promise<JsonRecord> {
  const response = await fetch(`${apiBase}/api/tutor/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<JsonRecord>(response);
}

export type PipelinePayload = {
  user_id: string;
  session_id: string;
  answer1: string;
  answer2: string;
  answer3: string;
  answer4: string;
  user_input: string;
  speak_language?: string;
  learn_language?: string;
  lessons_per_week?: number;
};

type JsonRecord = Record<string, unknown>;

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as { detail?: string; message?: string };
      const detail = payload.detail || payload.message || "Unknown API error";
      throw new Error(`API error ${response.status}: ${detail}`);
    }
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text || "Unknown API error"}`);
  }
  return response.json() as Promise<T>;
}

export async function runPipeline(
  apiBase: string,
  payload: PipelinePayload,
): Promise<JsonRecord> {
  const response = await fetch(`${apiBase}/api/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<JsonRecord>(response);
}

export async function fetchDashboard(
  apiBase: string,
  userId: string,
  sessionId: string,
): Promise<JsonRecord> {
  const params = new URLSearchParams({ user_id: userId, session_id: sessionId });
  const response = await fetch(`${apiBase}/api/dashboard?${params.toString()}`);
  return parseJson<JsonRecord>(response);
}

export async function startLesson(
  apiBase: string,
  userId: string,
  sessionId: string,
  week: number | null,
  lessonId?: string,
): Promise<JsonRecord> {
  const payload: Record<string, unknown> = {
    user_id: userId,
    session_id: sessionId,
  };
  if (typeof week === "number") payload.week = week;
  if (lessonId) payload.lesson_id = lessonId;
  const response = await fetch(`${apiBase}/api/lesson/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<JsonRecord>(response);
}

export async function submitLessonPhase(
  apiBase: string,
  payload: {
    user_id: string;
    session_id: string;
    week?: number;
    lesson_id?: string;
    phase: string;
    payload: JsonRecord;
    score: number;
    hints_used: number;
    retries: number;
    duration_seconds: number;
  },
): Promise<JsonRecord> {
  const response = await fetch(`${apiBase}/api/lesson/phase-submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<JsonRecord>(response);
}

export async function completeLessonApi(
  apiBase: string,
  payload: {
    user_id: string;
    session_id: string;
    week?: number;
    lesson_id?: string;
    accuracy: number;
    xp_earned: number;
    weak_topics: string[];
  },
): Promise<JsonRecord> {
  const response = await fetch(`${apiBase}/api/lesson/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<JsonRecord>(response);
}
