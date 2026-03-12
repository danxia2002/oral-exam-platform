import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import StudentExams from './pages/StudentExams';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userType, setUserType] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    
    if (token && user) {
      setIsLoggedIn(true);
      setUserType(user.user_type || 'student');  // 从 user 对象读取 user_type
    }
    setLoading(false);
  }, []);

  const handleLoginSuccess = () => {
    // 从 localStorage 读取登录后的用户信息
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    setIsLoggedIn(true);
    setUserType(user?.user_type || 'student');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isLoggedIn) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  // 根据 user_type 显示不同的页面
  if (userType === 'teacher') {
    return <Dashboard />;
  } else {
    return <StudentExams />;
  }
}

export default App;