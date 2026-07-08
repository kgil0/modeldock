import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ taskId: string }> }
) {
  const { taskId } = await params;

  const res = await fetch(`http://127.0.0.1:8000/tasks/${taskId}`);
  const data = await res.json();

  return NextResponse.json(data);
}
