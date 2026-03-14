import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../styles/ExamInProgress.css';

function ExamInProgress({ studentExamId, onComplete }) {
  const [question, setQuestion] = useState('');
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [userAnswer, setUserAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [message, setMessage] = useState('');
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const token = localStorage.getItem('token');

  // Initialize exam
  useEffect(() => {
    initializeExam();
  }, []);

  // Timer countdown
  useEffect(() => {
    if (timeLeft <= 0) {
      handleCompleteExam();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(t => t - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const initializeExam = async () => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/conversations/start`,
        null,
        { params: { student_exam_id: studentExamId, token } }
      );

      if (response.data.success) {
        setQuestion(response.data.question);
        setQuestionNumber(response.data.question_number);
        setTotalQuestions(response.data.total_questions);
      }
    } catch (error) {
      setMessage('Failed to start exam');
    }
  };

  const [hasRecording, setHasRecording] = useState(false);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        // In real implementation, send to speech-to-text API
        setMessage('✅ Recording saved. Click "Submit Answer" to proceed.');
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setMessage('Recording... Click "Stop Recording" to submit your answer');
    } catch (error) {
      setMessage('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => {
          track.stop();
        });
      }
      setHasRecording(true);
    }
  };

  const handleAnswerSubmitted = async () => {
    setIsWaiting(true);
    setMessage('Processing your answer...');

    try {
      const answerToSubmit = userAnswer.trim() || "Student provided audio response";
    
      const response = await axios.post(
        'http://localhost:8000/api/conversations/message',
        {
          student_exam_id: studentExamId,
          message: answerToSubmit,
          current_question_number: questionNumber
        },
        { params: { token } }
      );

      if (response.data.success) {
        if (response.data.is_complete) {
          setMessage('✅ Exam completed!');
          setTimeout(() => handleCompleteExam(), 2000);
        } else {
          setQuestion(response.data.next_question);
          setQuestionNumber(questionNumber + 1);
          setUserAnswer('');
          setHasRecording(false);
          setMessage('Next question loaded. Take your time!');
        }
      }
    } catch (error) {
      setMessage('Error processing answer');
    }
    setIsWaiting(false);
  };

  const handleCompleteExam = async () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach(track => {
        track.stop();
      });
    }

    try {
      await axios.post(
        `http://localhost:8000/api/conversations/complete`,
        null,
        { params: { student_exam_id: studentExamId, token } }
      );
      onComplete();
    } catch (error) {
      console.error('Error completing exam:', error);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="exam-container">
      <div className="exam-header">
        <div className="progress-info">
          <span className="question-counter">Question {questionNumber}/{totalQuestions}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
            ></div>
          </div>
        </div>
        <div className="timer">
          <span className={timeLeft < 60 ? 'warning' : ''}>
            ⏱️ {formatTime(timeLeft)}
          </span>
        </div>
      </div>

      <div className="exam-content">
        <div className="question-box">
          <h2>Question {questionNumber}</h2>
          <p className="question-text">{question}</p>
          <p className="instruction">Please answer in your own words</p>
        </div>

        <div className="answer-section">
          <textarea
            className="answer-input"
            placeholder="Type your answer here... or use the microphone button to speak your answer"
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            disabled={isWaiting}
          ></textarea>

          <div className="button-group">
            {!isRecording ? (
              <button 
                className="mic-btn"
                onClick={startRecording}
                disabled={isWaiting}
              >
                🎤 Record Answer
              </button>
            ) : (
              <button 
                className="stop-btn"
                onClick={stopRecording}
              >
                ⏹️ Stop Recording
              </button>
            )}
            
            <button 
              className="submit-btn"
              onClick={handleAnswerSubmitted}
              disabled={isWaiting || (!userAnswer.trim() && !hasRecording)}
            >
              {isWaiting ? 'Processing...' : 'Submit Answer'}
            </button>
          </div>
        </div>

        {message && (
          <div className={`message ${message.includes('✅') ? 'success' : 'info'}`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default ExamInProgress;