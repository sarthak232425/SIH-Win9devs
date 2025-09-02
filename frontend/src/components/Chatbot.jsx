import { useState, useRef, useEffect } from "react";
import axios from "axios";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I'm your medical AI assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        query: input,
        conversation_history: messages.map((m) => ({
          role: m.role === "user" ? "user" : "assistant",
          content: m.text,
        })),
      });

      const aiMessage = { role: "ai", text: res.data.response };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      const aiMessage = { 
        role: "ai", 
        text: "⚠️ Sorry, I'm having trouble connecting. Please try again." 
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Container with proper scrolling - FIXED */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-1 space-y-3 mb-3"
        style={{ maxHeight: '400px' }} // Fixed height to prevent layout shifts
      >
        <div className="space-y-2">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={
                msg.role === "ai"
                  ? "flex items-start space-x-2"
                  : "flex items-start space-x-2 justify-end"
              }
            >
              {msg.role === "ai" && (
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs">
                  AI
                </div>
              )}
              <div
                className={
                  msg.role === "ai"
                    ? "bg-blue-50 text-gray-800 p-3 rounded-lg max-w-[80%] border border-blue-100"
                    : "bg-gray-100 text-gray-800 p-3 rounded-lg max-w-[80%] border border-gray-200"
                }
              >
                <div className="text-sm whitespace-pre-wrap">{msg.text}</div>
              </div>
              {msg.role === "user" && (
                <div className="flex-shrink-0 w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center text-white text-xs">
                  You
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs">
                AI
              </div>
              <div className="bg-blue-50 text-gray-800 p-3 rounded-lg max-w-[80%] border border-blue-100">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <div className="animate-pulse">Thinking</div>
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Fixed position within container */}
      <div className="border-t border-gray-200 pt-3">
        <div className="flex space-x-2 bg-white p-1 rounded-lg border border-gray-300 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-200 transition-all">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a disease or medical term..."
            className="flex-1 border-none px-3 py-2 text-sm outline-none bg-transparent"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center min-w-[44px]"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send
        </p>
      </div>
    </div>
  );
}