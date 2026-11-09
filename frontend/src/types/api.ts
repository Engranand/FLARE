export interface HealthResponse {
  status: 'ok';
  application_name: string;
  version: string;
}
export type ConnectionStatus = 'Checking' | 'Connected' | 'Disconnected';
