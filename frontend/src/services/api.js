/* API Client Service for CodeMentor AI Backend */

const API_BASE_URL = 'http://127.0.0.1:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.error || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  // Health check
  async healthCheck() {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return handleResponse(res);
  },

  // Repository Ingestion
  async ingestRepo(githubUrl) {
    const res = await fetch(`${API_BASE_URL}/api/repository/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ github_url: githubUrl }),
    });
    return handleResponse(res);
  },

  // Check Ingestion Status
  async getRepoStatus(repoId) {
    const res = await fetch(`${API_BASE_URL}/api/repository/${repoId}/status`);
    return handleResponse(res);
  },

  // List Ingested Repositories
  async listRepos() {
    const res = await fetch(`${API_BASE_URL}/api/repository/list`);
    return handleResponse(res);
  },

  // Delete Repository
  async deleteRepo(repoId) {
    const res = await fetch(`${API_BASE_URL}/api/repository/${repoId}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  // Search Vector Store Chunks
  async searchChunks(repoId, question) {
    const url = new URL(`${API_BASE_URL}/api/repository/search`);
    url.searchParams.append('repo_id', repoId);
    url.searchParams.append('question', question);
    const res = await fetch(url, { method: 'POST' });
    return handleResponse(res);
  },

  // Ask RAG Question
  async askQuestion(repoId, question) {
    const res = await fetch(`${API_BASE_URL}/api/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_id: repoId, question: question }),
    });
    return handleResponse(res);
  },

  // Fetch Chat History
  async getChatHistory(repoId) {
    const res = await fetch(`${API_BASE_URL}/api/chat/${repoId}/history`);
    return handleResponse(res);
  },

  // Clear Chat History
  async clearChatHistory(repoId) {
    const res = await fetch(`${API_BASE_URL}/api/chat/${repoId}/history`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },
};
