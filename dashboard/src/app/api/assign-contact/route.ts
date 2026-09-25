import { NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

import { getSupabaseAdmin } from "@/lib/supabaseServer";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const companyId = String(body.companyId || "");
    const roleId = body.roleId ? String(body.roleId) : null;
    const contactId = body.contactId ? String(body.contactId) : null;
    const fullName = String(body.contactName || "").trim();
    const email = String(body.email || "").trim() || null;
    const linkedinUrl = String(body.linkedinUrl || "").trim() || null;

    if (!companyId || !fullName || (!roleId && !contactId)) {
      return NextResponse.json({ success: false, error: "Company, role, and contact name are required" }, { status: 400 });
    }

    const supabase = getSupabaseAdmin();
    if (roleId) {
      const { data: role, error: roleError } = await supabase
        .from("target_roles")
        .select("id")
        .eq("id", roleId)
        .eq("company_id", companyId)
        .maybeSingle();
      if (roleError) throw roleError;
      if (!role) return NextResponse.json({ success: false, error: "Target role not found" }, { status: 404 });
    }

    let existingId = contactId;
    if (existingId) {
      const { data: existing, error } = await supabase
        .from("contacts")
        .select("id")
        .eq("id", existingId)
        .eq("company_id", companyId)
        .maybeSingle();
      if (error) throw error;
      if (!existing) return NextResponse.json({ success: false, error: "Contact not found" }, { status: 404 });
    } else if (roleId) {
      const { data: existing, error } = await supabase
        .from("contacts")
        .select("id")
        .eq("company_id", companyId)
        .eq("target_role_id", roleId)
        .ilike("full_name", fullName)
        .limit(1)
        .maybeSingle();
      if (error) throw error;
      existingId = existing?.id || null;
    }

    const values = {
      company_id: companyId,
      ...(roleId ? { target_role_id: roleId } : {}),
      full_name: fullName,
      email,
      linkedin_url: linkedinUrl,
      source: "manual_assignment",
    };
    const query = existingId
      ? supabase.from("contacts").update(values).eq("id", existingId)
      : supabase.from("contacts").insert(values);
    const { data: contact, error } = await query.select("id,full_name,email,linkedin_url").single();
    if (error) throw error;

    revalidatePath("/companies");
    revalidatePath("/contacts");
    revalidatePath("/outreach");
    return NextResponse.json({ success: true, contact });
  } catch (error) {
    console.error("Error assigning contact:", error);
    return NextResponse.json({ success: false, error: "Failed to save contact" }, { status: 500 });
  }
}
