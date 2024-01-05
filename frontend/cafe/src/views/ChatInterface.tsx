import React, { useReducer, useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { useAuth } from '../security/AuthContext';

// Define a type for chat messages
type ChatMessage = {
  sender: 'user' | 'bot';
  text: string;
};

const actionTypes = {
    APPEND_TO_CURRENT_MESSAGE: 'APPEND_TO_CURRENT_MESSAGE',
    ADD_MESSAGE_TO_CONVERSATION: 'ADD_MESSAGE_TO_CONVERSATION',
};

// Define a reducer to manage the conversation state
const conversationReducer = (state, action) => {
    switch (action.type) {
      case actionTypes.APPEND_TO_CURRENT_MESSAGE:
        return { ...state, currentMessage: state.currentMessage + action.payload };
      case actionTypes.ADD_MESSAGE_TO_CONVERSATION:
        return {
          ...state,
          conversation: [...state.conversation, { sender: 'bot', text: state.currentMessage }],
          currentMessage: '', // Reset currentMessage after adding it to the conversation
        };
      default:
        return state;
    }
};

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const { userToken } = useAuth();
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const endOfMessagesRef = useRef<null | HTMLDivElement>(null);
//   const eventSourceRef = useRef<EventSource | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  const [state, dispatch] = useReducer(conversationReducer, {
    conversation: [],
    currentMessage: '',
  });

  // Scrolls to the end of the messages
  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Call this function whenever you want to
  // refresh the messages in the chat
  useEffect(scrollToBottom, [conversation]);

//   useEffect(() => {
//     // Clean up the event source when the component unmounts
//     return () => {
//       if (eventSourceRef.current) {
//         eventSourceRef.current.close();
//       }
//     };
//   }, []);

// Clean up the WebSocket when the component unmounts
  useEffect(() => {
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput) {
      // Add the user's message to the conversation
      setConversation((prev) => [...prev, { sender: 'user', text: trimmedInput }]);
      console.log(`setting conversation to ${conversation} from user input`);
  
      // Initialize a new WebSocket
      if (websocketRef.current) {
        websocketRef.current.close();
      }

      websocketRef.current = new WebSocket(`ws://localhost:8000/agent/ws/chat?token=${userToken?.token}`);
  
      websocketRef.current.onopen = () => {
        console.log('WebSocket Client Connected');
        websocketRef.current?.send(JSON.stringify({ message: trimmedInput }));
      };
  
      websocketRef.current.onmessage = (event) => {
        console.log('Received message from server: ', event.data);
        
        // Assume the server sends a special "end_of_message" property to indicate the end of a message
        const data = JSON.parse(event.data);
        console.log('data: ', data);

        if (data.end_of_message) {
           console.log('end of message is true');
          // End of message received, push the accumulated message to the conversation
          setConversation((prev) => [
            ...prev,
            { sender: 'bot', text: prev[prev.length - 1]?.text + data.message },
          ]);
        } else {
            console.log(`end of message is false - conversation: ${conversation}`);
          // Append token to the current message (or start a new message if there isn't one)
          if (conversation.length > 0 && conversation[conversation.length - 1].sender === 'bot') {
            console.log('condition met');
            setConversation((prev) => [
              ...prev.slice(0, -1),
              { ...prev[prev.length - 1], text: prev[prev.length - 1].text + data.message },
            ]);
          } else {
            console.log(`condition not met. conversation.length: ${conversation.length}. conversation[conversation.length - 1]: ${conversation[conversation.length - 1]}`);
            setConversation((prev) => [...prev, { sender: 'bot', text: data.message }]);
          }
        }
      };
      
  
      websocketRef.current.onerror = (error) => {
        // Handle any errors that occur
        console.error('WebSocket error:', error);
      };
    }
  
    // Reset the input field
    setInput('');
  };

//   const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
//     event.preventDefault();
//     const trimmedInput = input.trim();
//     if (trimmedInput) {
//         // Add the user's message to the conversation
//         setConversation((prev) => [...prev, { sender: 'user', text: trimmedInput }]);
        
//         // Initialize a new EventSource
//         if (eventSourceRef.current) {
//           eventSourceRef.current.close();
//         }
//         eventSourceRef.current = new EventSource(`/proxy?query=${encodeURIComponent(trimmedInput)}`);

//         // Listen for messages from the server
//         eventSourceRef.current.onmessage = (event) => {
//           const data = JSON.parse(event.data);
//           // Add the bot's response to the conversation
//           setConversation((prev) => [...prev, { sender: 'bot', text: data.message }]);
//         };
  
//         eventSourceRef.current.onerror = (error) => {
//           console.error('EventSource failed:', error);
//           eventSourceRef.current?.close();
//         };
//       }

//     // Reset the input field
//     setInput('');
//   };

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
