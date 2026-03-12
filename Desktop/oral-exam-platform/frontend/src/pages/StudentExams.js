import { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/StudentExams.css';

function StudentExams() {
  const [exams, setExams] = useState([]);
  const [myExams, setMyExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('available'); // "available" or "my-exams"
  
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchExams();
  }, []);

  const fetchExams = async () => {
    try {
      // Get available exams
      const availableRes = await axios.get('http://localhost:8000/api/exams/available', {
        params: { token }
      });
      
      if (availableRes.data.success) {
        setExams(availableRes.data.exams);
      }

      // Get my exams
      const myRes = await axios.get('http://localhost:8000/api/my-exams', {
        params: { token }
      });
      
      if (myRes.data.success) {
        setMyExams(myRes.data.student_exams);
      }
    } catch (error) {
      setMessage('Error loading exams');
    }
    setLoading(false);
  };

  const handleStartExam = async (examId) => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/exams/${examId}/start`,
        {},
        { params: { token } }
      );

      if (response.data.success) {
        setMessage('✅ Exam started!');
        fetchExams(); // Refresh lists
        setActiveTab('my-exams');
      }
    } catch (error) {
      setMessage('❌ Error starting exam');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  if (loading) {
    return <div className="student-container"><p>Loading...</p></div>;
  }

  return (
    <div className="student-container">
      <div className="student-header">
        <h1>Oral Exam Platform</h1>
        <div className="user-info">
          <span>Student: {user.username}</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div className="student-content">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'available' ? 'active' : ''}`}
            onClick={() => setActiveTab('available')}
          >
            Available Exams ({exams.length})
          </button>
          <button 
            className={`tab ${activeTab === 'my-exams' ? 'active' : ''}`}
            onClick={() => setActiveTab('my-exams')}
          >
            My Exams ({myExams.length})
          </button>
        </div>

        {message && <p className="message">{message}</p>}

        {activeTab === 'available' ? (
          <div className="exams-section">
            <h2>Available Exams</h2>
            {exams.length === 0 ? (
              <p className="empty-state">No exams available yet.</p>
            ) : (
              <div className="exams-grid">
                {exams.map((exam) => (
                  <div key={exam.id} className="exam-card">
                    <h3>{exam.name}</h3>
                    <p>{exam.description}</p>
                    <div className="topics">
                      {exam.topics.map((topic, idx) => (
                        <span key={idx} className="topic-tag">{topic}</span>
                      ))}
                    </div>
                    <button 
                      className="start-btn"
                      onClick={() => handleStartExam(exam.id)}
                    >
                      Start Exam
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="exams-section">
            <h2>My Exams</h2>
            {myExams.length === 0 ? (
              <p className="empty-state">You haven't taken any exams yet.</p>
            ) : (
              <div className="my-exams-list">
                {myExams.map((se) => (
                  <div key={se.id} className="my-exam-card">
                    <div className="exam-info">
                      <h3>{se.exam_name}</h3>
                      <p className="status">
                        Status: <span className={se.status}>{se.status}</span>
                      </p>
                      <p className="date">
                        Started: {new Date(se.started_at).toLocaleString()}
                      </p>
                      {se.completed_at && (
                        <p className="date">
                          Completed: {new Date(se.completed_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentExams;