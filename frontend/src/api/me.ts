interface ProfileResponse {
  display_name?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
}

export const getMe = async (): Promise<ProfileResponse | null> => {
  return null;
};
