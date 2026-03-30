"use client";

/**
 * /admin/users → /admin 리다이렉트 (통합됨)
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminUsersRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin");
  }, [router]);
  return null;
}
