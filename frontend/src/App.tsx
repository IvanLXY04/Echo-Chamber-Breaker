import { useState, useEffect, useRef } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// This is a stub for the A2UI Rendering Engine
// In production, this would use a library to parse the A2UI JSON payload
// and map it to our React components.
function A2UIRenderer({ payload }: { payload: any }) {
  if (!payload || !payload.components) return null;

  return (
    <div className="a2ui-container">
      <h3>Referee Scorecard</h3>
      {payload.components.map((comp: any, index: number) => {
        if (comp.component === 'WarningCard') {
          return (
            <div key={index} className="warning-card">
              <h4>⚠️ {comp.title}</h4>
              <p>{comp.message}</p>
            </div>
          )
        }
        if (comp.component === 'ProgressBar') {
          return (
            <div key={index} className="progress-bar">
              <label>
                <span>{comp.label}</span>
                <span>{comp.value}/{comp.max}</span>
              </label>
              <progress value={comp.value} max={comp.max}></progress>
            </div>
          )
        }
        return null;
      })}
    </div>
  )
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<any[]>([])
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userEmail, setUserEmail] = useState('')
  const [chatList, setChatList] = useState<any[]>([])
  const [currentChatId, setCurrentChatId] = useState<number | null>(null)
  const [editingChatId, setEditingChatId] = useState<number | null>(null)
  const [editChatName, setEditChatName] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [activeModal, setActiveModal] = useState<{title: string, content: React.ReactNode} | null>(null)
  const [isTransitioning, setIsTransitioning] = useState(false)
  
  // New Feature States
  const [isLightMode, setIsLightMode] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [selectedPersona, setSelectedPersona] = useState('Socratic')
  const [selectedDifficulty, setSelectedDifficulty] = useState('Normal')
  const [isRecording, setIsRecording] = useState(false)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isLightMode) {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
  }, [isLightMode])

  // Load chat list when user logs in
  useEffect(() => {
    if (userEmail) {
      fetchChats();
    }
  }, [userEmail])

  const fetchChats = async () => {
    try {
      const res = await fetch(`${API_URL}/chats?email=${encodeURIComponent(userEmail)}`);
      const data = await res.json();
      setChatList(data);
    } catch (e) {
      console.error('Failed to fetch chats', e);
    }
  }

  const loadChat = async (chatId: number) => {
    try {
      const res = await fetch(`${API_URL}/chats/${chatId}`);
      const data = await res.json();
      setMessages(data);
      setCurrentChatId(chatId);
    } catch (e) {
      console.error('Failed to load chat', e);
    }
  }

  const handleNewDebateClick = () => {
    setShowSettingsModal(true);
  }

  const confirmCreateChat = async () => {
    setShowSettingsModal(false);
    try {
      const res = await fetch(`${API_URL}/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail, persona: selectedPersona, difficulty: selectedDifficulty })
      });
      const data = await res.json();
      setChatList([data, ...chatList]);
      setCurrentChatId(data.id);
      setMessages([]);
    } catch (e) {
      console.error('Failed to create chat', e);
    }
  }

  const saveChatName = async (chatId: number) => {
    try {
      await fetch(`${API_URL}/chats/${chatId}/name`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editChatName })
      });
      setChatList(chatList.map(c => c.id === chatId ? { ...c, name: editChatName } : c));
      setEditingChatId(null);
    } catch (e) {
      console.error('Failed to update chat name', e);
    }
  }

  const deleteChat = async (chatId: number) => {
    try {
      await fetch(`${API_URL}/chats/${chatId}`, {
        method: 'DELETE'
      });
      setChatList(chatList.filter(c => c.id !== chatId));
      if (currentChatId === chatId) {
        setCurrentChatId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error('Failed to delete chat', e);
    }
  }

  const handleMicClick = () => {
    if (isRecording) return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in your browser.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    
    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(prev => prev + (prev ? ' ' : '') + transcript);
    };
    recognition.onerror = (e: any) => console.error("Speech recognition error", e);
    recognition.onend = () => setIsRecording(false);
    
    recognition.start();
  }

  const handleConcludeDebate = async () => {
    if (!currentChatId) return;
    setIsGeneratingReport(true);
    
    // Show immediate feedback
    setActiveModal({
      title: 'Analyzing Debate...',
      content: (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <div className="typing-indicator" style={{ margin: '0 auto 20px auto' }}>
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
          <p>Please wait while the AI generates your report card.</p>
        </div>
      )
    });

    try {
      const res = await fetch(`${API_URL}/chats/${currentChatId}/report`, { method: 'POST' });
      const report = await res.json();
      
      const errorMessage = report.error || report.detail;
      if (!res.ok || errorMessage) {
        let displayError = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
        if (displayError.includes('429') || displayError.includes('RESOURCE_EXHAUSTED')) {
          displayError = "Gemini API Quota Exceeded. You've reached the free tier limit. Please wait a minute before trying again.";
        }
        setActiveModal({
          title: 'Error Generating Report',
          content: (
            <div className="warning-card">
              <h4>Something went wrong</h4>
              <p>{displayError}</p>
            </div>
          )
        });
        return;
      }

      // Handle nested structures or camelCase variations
      let data = report;
      if (report.report_card) data = report.report_card;
      else if (report.ReportCard) data = report.ReportCard;
      else if (Object.keys(report).length === 1 && typeof Object.values(report)[0] === 'object') {
        data = Object.values(report)[0];
      }

      const score = data.logical_consistency_score || data.logicalConsistencyScore || data.logical_score || data.score || "N/A";
      const summary = data.summary || data.Summary || "";
      const fallacies = data.frequent_fallacies || data.frequentFallacies || data.fallacies || data.FrequentFallacies || [];
      const tips = data.improvement_tips || data.improvementTips || data.tips || data.ImprovementTips || [];

      if (!summary && score === "N/A" && fallacies.length === 0) {
        // Fallback: Dump raw JSON if nothing matched
        setActiveModal({
          title: 'Report Output',
          content: <pre style={{whiteSpace: 'pre-wrap', fontSize: '12px'}}>{JSON.stringify(report, null, 2)}</pre>
        });
        return;
      }
      
      setActiveModal({
        title: 'Debate Report Card',
        content: (
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px'}}>
              <strong>Logical Consistency Score</strong>
              <span style={{fontWeight: 'bold', color: '#93c5fd'}}>{score}</span>
            </div>
            <div className="report-card-summary">
              <strong>Summary:</strong> {summary}
            </div>
            
            <div style={{marginTop: '20px'}}>
              <strong>Frequent Fallacies:</strong>
              <ul>
                {Array.isArray(fallacies) ? fallacies.map((f: string, i: number) => <li key={i}>{f}</li>) : <li>{String(fallacies)}</li>}
              </ul>
            </div>
            
            <div style={{marginTop: '20px'}}>
              <strong>Improvement Tips:</strong>
              <ul>
                {Array.isArray(tips) ? tips.map((t: string, i: number) => <li key={i}>{t}</li>) : <li>{String(tips)}</li>}
              </ul>
            </div>
          </div>
        )
      });
    } catch (e) {
      console.error(e);
      alert("Failed to generate report.");
    } finally {
      setIsGeneratingReport(false);
    }
  }

  const handleExportTranscript = () => {
    if (!currentChatId || messages.length === 0) return;
    let md = `# Debate Transcript\n\n`;
    messages.forEach(msg => {
      md += `**${msg.sender === 'user' ? 'You' : 'Opponent'}**: \n${msg.text}\n\n`;
    });
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debate_${currentChatId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const handleSend = async () => {
    if (!input.trim() || !currentChatId) return;
    
    const newMessages = [...messages, { sender: 'user', text: input }];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_URL}/chats/${currentChatId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: input, 
          persona: chatList.find(c => c.id === currentChatId)?.persona || 'Socratic',
          difficulty: chatList.find(c => c.id === currentChatId)?.difficulty || 'Normal'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Network response was not ok');
      }

      const data = await response.json();
      
      const errorMessage = data.error || data.detail;
      if (!response.ok || errorMessage) {
        let displayError = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
        if (displayError.includes('429') || displayError.includes('RESOURCE_EXHAUSTED')) {
          displayError = "Gemini API Quota Exceeded. You've reached the free tier limit. Please wait a minute before sending another message.";
        }
        const errorMsg = { sender: 'opponent', text: `⚠️ **Error:** ${displayError}` };
        setMessages([...newMessages, errorMsg]);
        return;
      }

      setMessages([...newMessages, { 
        sender: 'opponent', 
        text: data.opponent_response,
        a2ui_payload: data.referee_scorecard
      }]);
    } catch (error: any) {
      console.error("Failed to fetch response:", error);
      setMessages([...newMessages, { 
        sender: 'opponent', 
        text: `Backend Error: ${error.message}`
      }]);
    } finally {
      setIsTyping(false);
    }
  }

  const handleStarterTopic = async (topic: string) => {
    try {
      const res = await fetch(`${API_URL}/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail })
      });
      const data = await res.json();
      setChatList([data, ...chatList]);
      setCurrentChatId(data.id);
      
      const initialMessages = [{ sender: 'user', text: topic }];
      setMessages(initialMessages);
      setIsTyping(true);

      const response = await fetch(`${API_URL}/chats/${data.id}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: topic, persona: 'Socratic' })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const responseData = await response.json();
      setMessages([...initialMessages, { 
        sender: 'opponent', 
        text: responseData.opponent_response,
        a2ui_payload: responseData.referee_scorecard
      }]);
    } catch (error: any) {
      console.error("Failed to fetch response:", error);
    } finally {
      setIsTyping(false);
    }
  }

  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const userInfo = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        const data = await userInfo.json();
        setUserEmail(data.email);
        
        setIsTransitioning(true);
        setTimeout(() => {
          setIsLoggedIn(true);
          setIsTransitioning(false);
        }, 500);
      } catch (error) {
        console.error('Failed to fetch user info', error);
      }
    },
    onError: () => console.log('Login Failed'),
  });

  if (!isLoggedIn) {
    const showModal = (title: string, content: React.ReactNode) => {
      setActiveModal({ title, content });
    };

    return (
      <div className={`landing-page ${isTransitioning ? 'fade-out' : ''}`}>
        {activeModal && (
          <div className="modal-overlay" onClick={() => setActiveModal(null)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <button className="close-modal-btn" onClick={() => setActiveModal(null)}>×</button>
              <h2>{activeModal.title}</h2>
              <div className="modal-body">{activeModal.content}</div>
            </div>
          </div>
        )}

        <div className="bg-orbs">
          <div className="orb orb-1"></div>
          <div className="orb orb-2"></div>
          <div className="orb orb-3"></div>
        </div>
        
        <nav className="navbar">
          <div className="nav-logo">
            <img src="/echo_chamber_breaker_logo.png" alt="Logo" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
            <span>Echo-Chamber Breaker</span>
          </div>
          <div className="nav-links">
            <a href="#" onClick={(e) => {
              e.preventDefault();
              showModal("Features", (
                <ul>
                  <li><strong>Socratic AI Coach:</strong> Debates you intelligently to test your premises.</li>
                  <li><strong>Real-time Fallacy Detection:</strong> Flags logical errors instantly.</li>
                  <li><strong>Objective Scoring:</strong> Quantifies the strength of your arguments.</li>
                </ul>
              ));
            }}>Features</a>
            <a href="#" onClick={(e) => {
              e.preventDefault();
              showModal("How it Works", (
                <ol>
                  <li><strong>Start a Debate:</strong> Enter a claim or choose a starter topic.</li>
                  <li><strong>Defend Your Stance:</strong> The AI Coach will counter your points using Socratic questioning.</li>
                  <li><strong>Get Scored:</strong> The Referee Agent monitors the exchange and flags fallacies like Ad Hominem or Strawman in real-time.</li>
                </ol>
              ));
            }}>How it Works</a>
            <button className="nav-login-btn" onClick={() => login()}>Sign In</button>
          </div>
        </nav>

        <header className="hero">
          <h1>Break Out of Your Echo Chamber</h1>
          <p>Test your strongest arguments against a ruthless Socratic AI coach. Sharpen your logic, detect fallacies, and discover the truth in real-time.</p>
          <button className="hero-cta-btn" onClick={() => login()}>
            <svg className="google-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              <path fill="none" d="M0 0h48v48H0z"/>
            </svg>
            Start Debating for Free
          </button>
        </header>

        <section id="features" className="features-section">
          <div className="feature-card clickable" onClick={() => showModal("Socratic AI Coach", <p>Powered by Gemini 2.5 Flash, the coach adopts a specialized persona to debate you. It uses Socratic questioning to expose contradictions in your reasoning rather than just telling you you're wrong. It's designed to make you think critically about your own beliefs.</p>)}>
            <div className="feature-icon">🧠</div>
            <h3>Socratic AI Coach</h3>
            <p>Our AI doesn't just agree with you. It challenges your premises and forces you to think deeper.</p>
            <span className="learn-more">Click to learn more →</span>
          </div>
          <div className="feature-card clickable" onClick={() => showModal("Real-time Fallacy Detection", <p>A secondary background agent evaluates every turn of the debate independently. If you rely on a logical fallacy (like Ad Hominem, Strawman, or Appeal to Emotion), you'll receive a warning card explaining exactly where your logic broke down.</p>)}>
            <div className="feature-icon">⚖️</div>
            <h3>Real-time Fallacy Detection</h3>
            <p>A secondary Referee Agent watches the debate and red-flags logical fallacies as they happen.</p>
            <span className="learn-more">Click to learn more →</span>
          </div>
          <div className="feature-card clickable" onClick={() => showModal("Objective Scoring", <p>Your debate performance is quantified in real-time. Maintain a strong, logically sound argument to keep your score high, but beware—repeated fallacies will deplete your credibility progress bar!</p>)}>
            <div className="feature-icon">📊</div>
            <h3>Objective Scoring</h3>
            <p>Track your argument strength with live progress bars and warning cards based on your performance.</p>
            <span className="learn-more">Click to learn more →</span>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="app-container">
      {activeModal && (
        <div className="modal-overlay" onClick={() => { if (!isGeneratingReport) setActiveModal(null); }}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            {!isGeneratingReport && (
              <button className="close-modal-btn" onClick={() => setActiveModal(null)}>×</button>
            )}
            <h2>{activeModal.title}</h2>
            <div className="modal-body">{activeModal.content}</div>
          </div>
        </div>
      )}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-modal-btn" onClick={() => setShowSettingsModal(false)}>×</button>
            <h2>New Debate Settings</h2>
            <div className="form-group">
              <label>Opponent Persona</label>
              <select value={selectedPersona} onChange={e => setSelectedPersona(e.target.value)}>
                <option value="Socratic">Socratic (Balanced, insightful)</option>
                <option value="Devil's Advocate">Devil's Advocate (Aggressively disagrees)</option>
                <option value="Conspiracy Theorist">Conspiracy Theorist (Wild logical leaps)</option>
              </select>
            </div>
            <div className="form-group">
              <label>Referee Strictness</label>
              <select value={selectedDifficulty} onChange={e => setSelectedDifficulty(e.target.value)}>
                <option value="Casual">Casual (Flags only major fallacies)</option>
                <option value="Normal">Normal (Balanced moderation)</option>
                <option value="Hardcore">Hardcore (Flags every minor cognitive bias)</option>
              </select>
            </div>
            <button className="hero-cta-btn" style={{width: '100%', marginTop: '20px', justifyContent: 'center'}} onClick={confirmCreateChat}>
              Start Debate
            </button>
          </div>
        </div>
      )}
      <div className="sidebar">
        <div className="sidebar-header">
          <img src="/echo_chamber_breaker_logo.png" alt="Logo" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          <h3>Chats</h3>
          <button className="theme-toggle-btn" onClick={() => setIsLightMode(!isLightMode)} title="Toggle Theme" style={{marginLeft: 'auto'}}>
            {isLightMode ? '🌙' : '☀️'}
          </button>
        </div>
        <button className="new-chat-btn" onClick={handleNewDebateClick}>+ New Debate</button>
        <div className="chat-list">
          {chatList.map((chat) => (
            <div key={chat.id} className={`chat-list-item ${currentChatId === chat.id ? 'active' : ''}`}>
              {editingChatId === chat.id ? (
                <input 
                  autoFocus
                  value={editChatName} 
                  onChange={(e) => setEditChatName(e.target.value)}
                  onBlur={() => saveChatName(chat.id)}
                  onKeyDown={(e) => e.key === 'Enter' && saveChatName(chat.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <div className="chat-item-content" onClick={() => loadChat(chat.id)}>
                  <span className="chat-title" onDoubleClick={(e) => {
                    e.stopPropagation();
                    setEditChatName(chat.name);
                    setEditingChatId(chat.id);
                  }}>
                    {chat.name}
                  </span>
                  <button 
                    className="edit-chat-btn" 
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditChatName(chat.name);
                      setEditingChatId(chat.id);
                    }}
                    title="Rename chat"
                  >
                    Rename
                  </button>
                  <button 
                    className="delete-chat-btn" 
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Delete this chat?')) deleteChat(chat.id);
                    }}
                    title="Delete chat"
                  >
                    🗑️
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div className="chat-interface">
        <h2>
          Debate Coach
          <div className="chat-header-actions">
            {currentChatId && (
              <>
                <button className="action-btn" onClick={handleConcludeDebate} disabled={isGeneratingReport}>
                  {isGeneratingReport ? 'Generating...' : 'Conclude & Score'}
                </button>
                <button className="action-btn" onClick={handleExportTranscript}>
                  Export .md
                </button>
              </>
            )}
          </div>
        </h2>
        
        {!currentChatId ? (
          <div className="empty-state">
            <p>Select a chat or start a new debate to begin.</p>
            <div className="starter-topics">
              <button onClick={() => handleStarterTopic('AI will inevitably replace software engineers within a decade.')}>AI replaces SWEs</button>
              <button onClick={() => handleStarterTopic('Universal Basic Income is necessary for a stable future society.')}>Universal Basic Income</button>
              <button onClick={() => handleStarterTopic('Social media has been a net negative for human civilization.')}>Social Media</button>
            </div>
          </div>
        ) : (
          <>
            <div className="messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.sender}`}>
                  <p><strong>{msg.sender === 'user' ? 'You' : 'Opponent'}:</strong></p>
                  <div className="message-text">
                    {msg.sender === 'opponent' ? (
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    ) : (
                      <p>{msg.text}</p>
                    )}
                  </div>
                  
                  {/* Render A2UI components if present (e.g., from the Referee Agent) */}
                  {msg.a2ui_payload && <A2UIRenderer payload={msg.a2ui_payload} />}
                </div>
              ))}
              {isTyping && (
                <div className="message opponent typing-indicator">
                  <div className="dot"></div>
                  <div className="dot"></div>
                  <div className="dot"></div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <div className="input-area">
              <button className={`mic-btn ${isRecording ? 'recording' : ''}`} onClick={handleMicClick} title="Hold to speak">
                🎤
              </button>
              <input 
                value={input} 
                onChange={(e) => setInput(e.target.value)} 
                placeholder={isRecording ? "🔴 Recording... Speak now" : "State your argument..."}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button onClick={handleSend}>Send</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default App
