// Type for API error responses
export interface ApiError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
    };
  };
}
