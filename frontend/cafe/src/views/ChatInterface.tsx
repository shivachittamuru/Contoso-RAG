import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { useAuth } from '../security/AuthContext';

// Define a type for chat messages
type ChatMessage = {
  sender: 'user' | 'bot';
  text: string;
};

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const { userToken } = useAuth();
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const endOfMessagesRef = useRef<null | HTMLDivElement>(null);

  // Scrolls to the end of the messages
  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Call this function whenever you want to
  // refresh the messages in the chat
  useEffect(scrollToBottom, [conversation]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput) {
      // Add the user's message to the conversation
      setConversation((prev) => [...prev, { sender: 'user', text: trimmedInput }]);
      
      // Call the API
      try {
        const response = await fetch('/user/hello', {
            headers: {
              Accept: 'application/json',
              Authorization: `Bearer ${userToken?.token}`
            }
          });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();
        // Add the bot's response to the conversation
        setConversation((prev) => [...prev, { sender: 'bot', text: data.message }]);
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
      }
    }

    // Reset the input field
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="message-container">
        {conversation.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.text}
          </div>
        ))}
        <div ref={endOfMessagesRef} />
      </div>
      <form onSubmit={handleSubmit} className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="input-field"
        />
        <button type="submit" className="submit-button">Send</button>
      </form>
    </div>
  );
};

export default ChatInterface;
