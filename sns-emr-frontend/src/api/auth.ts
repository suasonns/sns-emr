import { clearAccessToken, clearCurrentUser, setAccessToken, setCurrentUser, type SessionUser } from "./session";

export type AuthenticatedUser = SessionUser;

export async function login(email: string, password: string) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error("Invalid email or password");
  }

  const data = (await response.json()) as {
    access_token: string;
    token_type: string;
    user: AuthenticatedUser;
  };

  setAccessToken(data.access_token);
  setCurrentUser(data.user);
  return data;
}

export function logout() {
  clearAccessToken();
  clearCurrentUser();
}
