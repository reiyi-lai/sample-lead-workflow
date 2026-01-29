import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '..', 'data');

function sanitizeName(name: string): string {
  return name.replace(/[^\w\s-]/g, '').replace(/\s+/g, ' ').trim();
}

function roleFilePrefix(title: string): string {
  return sanitizeName(title).replace(/ /g, '_');
}

export async function POST(request: Request) {
  try {
    const { companyName, roleTitle, contactName, linkedinUrl, email } = await request.json();

    if (!companyName || !roleTitle || !contactName) {
      return NextResponse.json(
        { success: false, error: 'companyName, roleTitle, and contactName are required' },
        { status: 400 }
      );
    }

    const companyFolder = sanitizeName(companyName);
    const prefix = roleFilePrefix(roleTitle);
    const contactsDir = path.join(DATA_DIR, 'contacts', companyFolder);

    const analysisPath = path.join(contactsDir, `${prefix}_analysis.json`);
    const outreachPath = path.join(contactsDir, `${prefix}_outreach.json`);

    // Check that role-based outreach exists
    if (!fs.existsSync(analysisPath) || !fs.existsSync(outreachPath)) {
      return NextResponse.json(
        { success: false, error: 'Role outreach not yet generated. Run the pipeline first.' },
        { status: 404 }
      );
    }

    // Read and update analysis
    const analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf-8'));
    const analysisStr = JSON.stringify(analysis);
    const updatedAnalysis = JSON.parse(analysisStr.replace(/\[Name\]/g, contactName));
    updatedAnalysis.contact_details = {
      contact_name: contactName,
      linkedin_url: linkedinUrl || null,
      email: email || null,
      assigned_at: new Date().toISOString(),
    };
    fs.writeFileSync(analysisPath, JSON.stringify(updatedAnalysis, null, 2));

    // Read and update outreach
    const outreach = JSON.parse(fs.readFileSync(outreachPath, 'utf-8'));
    const outreachStr = JSON.stringify(outreach);
    const updatedOutreach = JSON.parse(outreachStr.replace(/\[Name\]/g, contactName));
    fs.writeFileSync(outreachPath, JSON.stringify(updatedOutreach, null, 2));

    return NextResponse.json({
      success: true,
      analysis: updatedAnalysis,
      outreach: updatedOutreach,
    });
  } catch (error) {
    console.error('Error assigning contact:', error);
    return NextResponse.json(
      { success: false, error: String(error) },
      { status: 500 }
    );
  }
}
