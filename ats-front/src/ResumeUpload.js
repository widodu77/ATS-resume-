// src/ResumeUpload.js
import React, { useState } from 'react';

function ResumeUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }
    setError('');
    setLoading(true);
    const formData = new FormData();
    formData.append("resume_file", file);

    try {
      const response = await fetch("http://localhost:8000/api/score/", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("API error: " + response.statusText);
      }
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Upload Your Resume</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} accept=".pdf" />
        <button type="submit">Submit</button>
      </form>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {result && (
        <div>
          <h2>Results:</h2>
          <p><strong>Final Verdict:</strong> {result.final_verdict}</p>
          <h3>Detailed Feedback</h3>
          {result.history && Object.keys(result.history).map(category => (
            <div key={category}>
              <h4>{category}</h4>
              <ul>
                {Object.entries(result.history[category]).map(([facet, feedback]) => (
                  <li key={facet}><strong>{facet}:</strong> {feedback}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ResumeUpload;
