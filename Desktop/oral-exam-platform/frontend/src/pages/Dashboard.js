import { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/Dashboard.css';
import TeacherAnalytics from './TeacherAnalytics';

function Dashboard() {
  const [exams, setExams] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    topics: ''
  });

  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchExams();
  }, [token]);

  const fetchExams = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/exams', {
        params: { token }
      });
      
      if (response.data.success) {
        setExams(response.data.exams);
      }
    } catch (error) {
      setMessage('Error loading exams');
    }
    setLoading(false);
  };

  const handleCreateExam = async () => {
    if (!formData.name || !formData.description || !formData.topics) {
      setMessage('Please fill in all fields');
      return;
    }

    const topicsArray = formData.topics.split(',').map(t => t.trim());

    try {
      const response = await axios.post(
        'http://localhost:8000/api/exams',
        {
          name: formData.name,
          description: formData.description,
          topics: topicsArray
        },
        { params: { token } }
      );

      if (response.data.success) {
        setMessage('✅ Exam created successfully!');
        setFormData({ name: '', description: '', topics: '' });
        setShowCreateForm(false);
        fetchExams();
      }
    } catch (error) {
      setMessage('❌ Error creating exam');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  const [showAnalytics, setShowAnalytics] = useState(false);

  if (showAnalytics) {
    return <TeacherAnalytics onBack={() => setShowAnalytics(false)} />;
  }

  if (loading) {
    return <div className="dashboard-container"><p>Loading...</p></div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Oral Exam Platform</h1>
        <div className="user-info">
          <span>Welcome, {user.username}!</span>
          <button 
            className="analytics-btn"
            onClick={() => setShowAnalytics(true)}  // 改成 state，不用 window.location
          >
            📊 View Analytics
          </button>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="exams-section">
          <div className="section-header">
            <h2>Your Exams</h2>
            <button 
              className="create-btn"
              onClick={() => setShowCreateForm(!showCreateForm)}
            >
              {showCreateForm ? 'Cancel' : '+ Create Exam'}
            </button>
          </div>

          {showCreateForm && (
            <div className="create-form">
              <h3>Create New Exam</h3>
              <input
                type="text"
                placeholder="Exam Name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
              />
              <textarea
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              ></textarea>
              <input
                type="text"
                placeholder="Topics (comma-separated, e.g. AI, Machine Learning, NLP)"
                value={formData.topics}
                onChange={(e) => setFormData({...formData, topics: e.target.value})}
              />
              <button onClick={handleCreateExam}>Create Exam</button>
              {message && <p className="message">{message}</p>}
            </div>
          )}

          <div className="exams-list">
            {exams.length === 0 ? (
              <p className="empty-state">No exams yet. Create one to get started!</p>
            ) : (
              exams.map((exam) => (
                <div key={exam.id} className="exam-card">
                  <h3>{exam.name}</h3>
                  <p>{exam.description}</p>
                  <div className="topics">
                    {exam.topics.map((topic, idx) => (
                      <span key={idx} className="topic-tag">{topic}</span>
                    ))}
                  </div>
                  <p className="created-date">
                    Created: {new Date(exam.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;