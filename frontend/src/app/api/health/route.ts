import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'oil-gas-futures-frontend',
    timestamp: new Date().toISOString()
  });
}
