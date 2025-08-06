/** Matches FastAPI's UserRead model exactly */
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface SignupResponse {
  user: User;
  access_token: string;
  token_type: string;
}