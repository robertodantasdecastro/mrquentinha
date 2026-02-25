export type AuthTokens = {
  access: string;
  refresh: string;
};

export type AuthUserProfile = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
};

export type HealthPayload = {
  status?: string;
  service?: string;
  detail?: string;
};
