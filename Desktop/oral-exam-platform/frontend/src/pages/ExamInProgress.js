import { useState, useEffect, useRef, useCallback } from 'react';
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
  const [timeLeft, setTimeLeft] = useState(600);
  const [hasRecording, setHasRecording] = useState(false);
  const [questionAudio, setQuestionAudio] = useState(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRefRef = useRef(null);
  const token = localStorage.getItem('token');

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const [lastScore, setLastScore] = useState(null);
  const [lastFeedback, setLastFeedback] = useState('');

  useEffect(() => {
    initializeExam();
  }, []);

  // handle Speech Recognition result
  useEffect(() => {
    if (!recognitionRef.current) return;
  
    recognitionRef.current.onstart = () => {
      setIsListening(true);
    };
  
    recognitionRef.current.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';
    
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
      
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
    
      if (interimTranscript) {
      }
    
      if (finalTranscript) {
        setUserAnswer(prev => prev + finalTranscript);
      }
    };
  
    recognitionRef.current.onerror = (event) => {
      console.log('Speech recognition error:', event.error);
      setMessage('❌ Speech recognition error: ' + event.error);
    };
  
    recognitionRef.current.onend = () => {
      setIsListening(false);
    };
  }, []);

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

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognitionRef.current = recognition;
    }
  }, []);

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
        
        if (response.data.question_audio) {
          setQuestionAudio(response.data.question_audio);
          playAudio(response.data.question_audio);
        }
      }
    } catch (error) {
      setMessage('Failed to start exam');
    }
  };

  const playAudio = async (audioDataUrl) => {
    if (!audioRefRef.current) return;

    try {
      audioRefRef.current.pause();
      audioRefRef.current.src = audioDataUrl;
      await audioRefRef.current.play();
    } catch (err) {
      console.warn("Audio playback prevented:", err);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };
      
      mediaRecorder.onstop = () => {
        setMessage('✅ Recording saved.');
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setHasRecording(true);

      // initialize and start Speech Recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
      
        recognition.onresult = (event) => {
          let finalTranscript = '';
        
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
          
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' ';
            }
          }
        
          if (finalTranscript) {
            setUserAnswer(prev => prev + finalTranscript);
            console.log('Transcribed:', finalTranscript);  // 调试用
          }
        };
      
        recognition.onerror = (event) => {
          console.log('Speech error:', event.error);
          setMessage('❌ Speech error: ' + event.error);
        };
      
        recognitionRef.current = recognition;
        recognition.start();
        setIsListening(true);
        setMessage('🎤 Recording... Say your answer');
      }
    
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

    // stop Speech Recognition
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
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
        // show score and feedback
        setLastScore(response.data.score);
        setLastFeedback(response.data.feedback);
        setMessage(`✅ Score: ${response.data.score}/100`);
      
        if (response.data.is_complete) {
          setMessage('✅ Exam completed!');
          setTimeout(() => handleCompleteExam(), 3000);
        } else {
          // let the user see the score
          setTimeout(() => {
            setQuestion(response.data.next_question);
            setQuestionNumber(questionNumber + 1);
            setUserAnswer('');
            setHasRecording(false);
            setLastScore(null);
            setLastFeedback('');
            setMessage('Next question loaded. Take your time!');
          
            if (response.data.next_question_audio) {
              setQuestionAudio(response.data.next_question_audio);
              const audio = new Audio(response.data.next_question_audio);
              audio.play().catch(err => console.log('Audio play error:', err));
            }
          }, 2000);
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
          
          {lastScore !== null && (
            <div style={{ 
              background: lastScore >= 70 ? '#d4edda' : '#fff3cd',
              padding: '15px',
              borderRadius: '8px',
              marginBottom: '15px',
              border: '1px solid #ccc'
            }}>
              <p><strong>Score: {lastScore}/100</strong></p>
              <p style={{ margin: '10px 0 0 0', fontSize: '14px' }}>{lastFeedback}</p>
            </div>
          )}
          
          {/* hidden audio player */}
          <audio 
            ref={audioRefRef}
            style={{ display: 'none' }}
            onPlay={() => setIsPlayingAudio(true)}
            onEnded={() => setIsPlayingAudio(false)}
          ></audio>

          {/* replay button */}
          {questionAudio && (
            <button 
              className="replay-btn"
              onClick={() => playAudio(questionAudio)}
              disabled={isPlayingAudio}
            >
              🔊 {isPlayingAudio ? 'Playing...' : 'Replay Question'}
            </button>
          )}
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
                ⏹️ Stop Recording {isListening && '(Listening...)'}
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