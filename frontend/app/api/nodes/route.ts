import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const userId = url.searchParams.get("user_id") || "";

  const res = await fetch(`http://127.0.0.1:8000/nodes?user_id=${userId}`);
  const data = await res.json();

  return NextResponse.json(data);
}
