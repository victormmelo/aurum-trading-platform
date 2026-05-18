"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { postApi, type ExportJob } from "@/lib/api";

const exportSections = ["market", "portfolio", "operations", "decisions"] as const;

export async function createExport(formData: FormData) {
  const sections = formData
    .getAll("sections")
    .filter((section): section is (typeof exportSections)[number] => {
      return typeof section === "string" && exportSections.some((item) => item === section);
    });

  const payload = {
    format: textValue(formData, "format", "txt"),
    sections: sections.length > 0 ? sections : [...exportSections],
    period_start: nullableText(formData, "period_start"),
    period_end: nullableText(formData, "period_end"),
    decision: nullableText(formData, "decision"),
    order_side: nullableText(formData, "order_side"),
    order_status: nullableText(formData, "order_status"),
  };

  const result = await postApi<ExportJob>("/exports", payload);
  if (!result.ok) redirect(`/exports?error=${encodeURIComponent(result.error)}`);

  revalidatePath("/exports");
  redirect(`/exports?success=exportacao criada&id=${result.data.id}`);
}

function rawValue(formData: FormData, field: string) {
  const value = formData.get(field);
  return typeof value === "string" ? value.trim() : "";
}

function textValue(formData: FormData, field: string, fallback: string) {
  return rawValue(formData, field) || fallback;
}

function nullableText(formData: FormData, field: string) {
  return rawValue(formData, field) || null;
}
