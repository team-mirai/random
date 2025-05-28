export interface PullRequest {
  number: number;
  title: string;
  labels: Array<{ name: string }>;
  user: {
    login: string;
  };
}

export interface FileChange {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
}
