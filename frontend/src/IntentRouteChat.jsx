import React, { useState, useRef, useEffect } from 'react';
import './index.css';

const NODE_STEPS = [
  "parse_intent",
  "enrich_context", 
  "search_catalog",
  "map_constraints",
  "verify",
  "checkout"
];

export const IntentRouteChat = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! Tell me what you need, and I\'ll find the perfect snack or drink.' }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const [agentState, setAgentState] = useState(null);
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const prompt = input;
    setAgentState({ current_step: "Starting" });
    setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    setInput('');
    setIsProcessing(true);

    try {
      const baseUrl = import.meta.env.PROD ? "" : "http://localhost:8000";
      const eventSource = new EventSource(`${baseUrl}/api/chat?prompt=${encodeURIComponent(prompt)}`);
      
      eventSource.onmessage = (event) => {
        if (event.data === '{}') return;
        const data = JSON.parse(event.data);
        
        setAgentState(prevState => ({
            ...prevState,
            ...data.state,
            current_step: data.node
        }));
      };

      eventSource.addEventListener('done', () => {
        eventSource.close();
        setIsProcessing(false);
        setAgentState(prevState => {
          if (prevState?.final_order && !prevState.final_order.error) {
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              content: `I've prepared ${prevState.final_order.item.name} for you!` 
            }]);
          } else {
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              content: 'I couldn\'t find anything matching your constraints.' 
            }]);
          }
          return prevState;
        });
      });

      eventSource.addEventListener('error', (event) => {
        console.error("SSE Error", event);
        eventSource.close();
        setIsProcessing(false);
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, there was an error processing your request.' }]);
      });

    } catch (err) {
      console.error(err);
      setIsProcessing(false);
    }
  };

  const renderNodeCard = (nodeName) => {
    const isActive = agentState?.current_step === nodeName;
    let content = null;
    
    if (nodeName === "parse_intent" && agentState?.raw_entities) {
      const entities = { ...agentState.raw_entities };
      if (entities.details) delete entities.details;
      content = entities;
    } else if (nodeName === "enrich_context" && agentState?.weather) {
      content = agentState.weather;
    } else if (nodeName === "search_catalog" && agentState?.candidates) {
      content = { found: agentState.candidates.length, items: agentState.candidates.map(c => c.name).slice(0,3) };
    } else if (nodeName === "map_constraints" && agentState?.candidates) {
      content = { 
        analyzed_items: agentState.candidates.length,
        macros: agentState.candidates.map(c => ({
          name: c.name,
          ...c.macros
        })).slice(0, 2)
      };
    } else if (nodeName === "verify" && (agentState?.rejected_reasons?.length > 0 || agentState?.candidates)) {
      if (agentState.rejected_reasons?.length > 0 && agentState.candidates?.length === 0) {
        content = { rejected: agentState.rejected_reasons, retries: agentState.retry_count };
      } else {
        content = { accepted: agentState.candidates.length, top_item: agentState.candidates[0]?.name };
      }
    } else if (nodeName === "checkout" && agentState?.final_order) {
      content = agentState.final_order;
    }

    if (!content || Object.keys(content).length === 0) {
      if (!isActive) return null;
      content = "Processing...";
    }

    return (
      <div key={nodeName} className={`node-card ${isActive ? 'active' : ''}`}>
        <div className="node-header">
          <span style={{ textTransform: 'capitalize' }}>{nodeName.replace('_', ' ')}</span>
          {isActive && <span className="badge active">Active</span>}
        </div>
        <pre style={{ margin: 0, fontSize: '13px', color: 'var(--muted)', overflowX: 'auto', overflowY: 'auto', maxHeight: '300px', background: '#f4f4f5', padding: '12px', borderRadius: '8px' }}>
          {JSON.stringify(content, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="intentroute-container">
      <div className="chat-pane">
        <h2 style={{ fontSize: '24px', fontWeight: 600, letterSpacing: '-0.03em', marginBottom: '8px' }}>Tell us what you need.</h2>
        <p style={{ color: 'var(--muted)', fontSize: '15px', marginBottom: '32px' }}>We'll figure out the rest.</p>
        
        <div className="premium-scroll" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', paddingBottom: '24px', paddingRight: '12px' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {isProcessing && (
            <div className="message assistant" style={{opacity: 0.7}}>
              Thinking... ({agentState?.current_step})
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', marginTop: 'auto' }}>
          <input 
            type="text" 
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="I pulled an all-nighter..."
            disabled={isProcessing}
          />
          <button type="submit" className="primary-button" disabled={isProcessing || !input.trim()}>
            Send
          </button>
        </form>
      </div>

      <div className="state-pane">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Agent State</h3>
          <span className={`badge ${isProcessing ? 'active' : ''}`}>
            {isProcessing ? 'Running' : 'Idle'}
          </span>
        </div>
        
        <div className="premium-scroll" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '12px' }}>
          {!agentState ? (
            <div style={{ color: 'var(--muted)', fontSize: '14px', textAlign: 'center', marginTop: '40px' }}>
              Waiting for user query...
            </div>
          ) : (
            NODE_STEPS.map(step => renderNodeCard(step))
          )}
        </div>
      </div>
    </div>
  );
};
