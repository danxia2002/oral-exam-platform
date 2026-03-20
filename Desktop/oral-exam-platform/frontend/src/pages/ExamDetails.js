import { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/ExamDetails.css';

function ExamDetails({ studentExamId, onBack }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchExamDetails();
  }, []);

  const fetchExamDetails = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/student-exams/${studentExamId}/details`,
        { params: { token } }
      );

      if (response.data.success) {
        setDetails(response.data);
      } else {
        setError('Failed to load exam details');
      }
    } catch (err) {
      setError('Error loading exam details');
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="exam-details-container"><p>Loading...</p></div>;
  }

  if (error) {
    return (
      <div className="exam-details-container">
        <p className="error">{error}</p>
        <button onClick={onBack}>Go Back</button>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="exam-details-container">
        <p>No details found</p>
        <button onClick={onBack}>Go Back</button>
      </div>
    );
  }

  const averageScore = details.answers.length > 0
    ? Math.round(details.answers.reduce((sum, ans) => sum + ans.score, 0) / details.answers.length)
    : 0;

  return (
    <div className="exam-details-container">
      <div className="details-header">
        <h1>{details.exam_name}</h1>
        <button className="back-btn" onClick={onBack}>← Back</button>
      </div>

      <div className="summary">
        <div className="summary-item">
          <label>Total Score:</label>
          <span className="total-score">{details.total_score}/500</span>
        </div>
        <div className="summary-item">
          <label>Average Score:</label>
          <span>{averageScore}/100</span>
        </div>
        <div className="summary-item">
          <label>Started:</label>
          <span>{new Date(details.started_at).toLocaleString()}</span>
        </div>
        {details.completed_at && (
          <div className="summary-item">
            <label>Completed:</label>
            <span>{new Date(details.completed_at).toLocaleString()}</span>
          </div>
        )}
      </div>

      <div className="answers-section">
        <h2>Question Responses</h2>
        {details.answers.map((ans, idx) => (
          <div key={idx} className="answer-card">
            <div className="question-header">
              <h3>Question {ans.question_number}</h3>
              <span className={`score-badge score-${ans.score >= 70 ? 'high' : 'low'}`}>
                {ans.score}/100
              </span>
            </div>

            <div className="question-text">
              <label>Question:</label>
              <p>{ans.question}</p>
            </div>

            <div className="answer-text">
              <label>Your Answer:</label>
              <p>{ans.answer}</p>
            </div>

            <div className="feedback-section">
              <label>Feedback:</label>
              <p className="feedback">{ans.feedback}</p>
            </div>

            {ans.strengths && (
              <div className="strengths">
                <label>Strengths:</label>
                <p>{ans.strengths}</p>
              </div>
            )}

            {ans.improvements && (
              <div className="improvements">
                <label>Areas for Improvement:</label>
                <p>{ans.improvements}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ExamDetails;