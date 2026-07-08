import { NextResponse } from "next/server";

export async function GET() {
  const res = await fetch("http://127.0.0.1:8000/tasks");
  const data = await res.json();

  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const body = await request.json();

  const res = await fetch("http://127.0.0.1:8000/tasks/download-model", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

    const data = await res.json();

    return NextResponse.json(data);
  }
