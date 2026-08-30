import { useState, useEffect } from "react";

interface User {
  email: string;
  name: string;
  role: string;
  org_type?: string;
  org_id?: string;
  org_mail?: string;
  employee_id?: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    try {
      const u = localStorage.getItem("hres_user");
      if (u) {
        setUser(JSON.parse(u));
      }
    } catch (e) {
      console.error("Failed to parse user from local storage", e);
    }
  }, []);

  return { user };
}
