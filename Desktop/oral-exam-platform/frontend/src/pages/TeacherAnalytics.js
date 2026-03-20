import { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/TeacherAnalytics.css';

function TeacherAnalytics({ onBack }) {
  const [analytics, setAnalytics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/teacher/analytics',
        { params: { token } }
      );

      if (response.data.success) {
        setAnalytics(response.data.analytics);
      } else {
        setError('Failed to load analytics');
      }
    } catch (err) {
      setError('Error loading analytics');
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="analytics-container"><p>Loading...</p></div>;
  }

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1>📊 Student Analytics Dashboard</h1>
        {onBack && (
          <button className="back-btn" onClick={onBack}>
            ← Back to Dashboard
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {analytics.length === 0 ? (
        <p className="no-data">No completed exams yet</p>
      ) : (
        <div className="analytics-list">
          {analytics.map((exam) => (
            <div key={exam.exam_id} className="exam-analytics-card">
              <div className="exam-header">
                <h2>{exam.exam_name}</h2>
                <p className="description">{exam.description}</p>
              </div>

              <div className="stats-grid">
                <div className="stat-item">
                  <label>Total Students</label>
                  <span className="stat-value">{exam.completed_students}</span>
                </div>
                <div className="stat-item">
                  <label>Completion Rate</label>
                  <span className="stat-value">{exam.completion_rate}</span>
                </div>
                <div className="stat-item">
                  <label>Average Score</label>
                  <span className="stat-value">{exam.average_score}/{exam.max_score}</span>
                </div>
                <div className="stat-item">
                  <label>Highest Score</label>
                  <span className="stat-value highest">{exam.highest_score}/{exam.max_score}</span>
                </div>
                <div className="stat-item">
                  <label>Lowest Score</label>
                  <span className="stat-value lowest">{exam.lowest_score}/{exam.max_score}</span>
                </div>
              </div>

              <div className="students-section">
                <h3>Student Results</h3>
                <div className="students-table">
                  <div className="table-header">
                    <div className="col-rank">Rank</div>
                    <div className="col-name">Student</div>
                    <div className="col-email">Email</div>
                    <div className="col-score">Score</div>
                    <div className="col-percentage">Percentage</div>
                    <div className="col-date">Completed</div>
                  </div>
                  {exam.students.map((student, idx) => (
                    <div key={student.student_id} className="table-row">
                      <div className="col-rank">
                        {idx === 0 && <span className="medal">🥇</span>}
                        {idx === 1 && <span className="medal">🥈</span>}
                        {idx === 2 && <span className="medal">🥉</span>}
                        {idx > 2 && <span>{idx + 1}</span>}
                      </div>
                      <div className="col-name">{student.student_name}</div>
                      <div className="col-email">{student.student_email}</div>
                      <div className="col-score">{student.score}/{exam.max_score}</div>
                      <div className="col-percentage">
                        <div className="progress-bar">
                          <div 
                            className={`progress-fill ${
                              student.score_percentage >= 70 ? 'high' : 'low'
                            }`}
                            style={{ width: `${student.score_percentage}%` }}
                          ></div>
                        </div>
                        <span>{student.score_percentage}%</span>
                      </div>
                      <div className="col-date">
                        {new Date(student.completed_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TeacherAnalytics;