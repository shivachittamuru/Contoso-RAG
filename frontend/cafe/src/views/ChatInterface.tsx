import React, { useReducer, useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { useAuth } from '../security/AuthContext';

// Define a type for chat messages
type ChatMessage = {
  sender: 'user' | 'bot';
  text: string;
  completed?: boolean;
};

type ConversationState = ChatMessage[];

// Define the action types
type ConversationAction =
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'APPEND_TO_LAST_MESSAGE'; payload: { text: string } }
  | { type: 'END_OF_MESSAGE' }; 

const ADD_MESSAGE = 'ADD_MESSAGE';
const APPEND_TO_LAST_MESSAGE = 'APPEND_TO_LAST_MESSAGE';
const END_OF_MESSAGE = 'END_OF_MESSAGE';

// Define a reducer to manage the conversation state
const conversationReducer = (state: ConversationState, action: ConversationAction): ConversationState => {
    switch (action.type) {
      case ADD_MESSAGE:{
        if (action.payload.text.trim() === '') {
          return state;
        }
        return [...state, action.payload];
      }
      case APPEND_TO_LAST_MESSAGE: {
        const newState = [...state];
        const lastMessageIndex = newState.findIndex(
          (msg) => msg.sender === 'bot' && !msg.completed
        );

        if (lastMessageIndex !== -1) {
          const lastMessage = newState[lastMessageIndex];
          newState[lastMessageIndex] = {
            ...lastMessage,
            text: lastMessage.text + action.payload.text,
          };
        } else {
          newState.push({
            sender: 'bot',
            text: action.payload.text,
            completed: false,
          });
        }
        return newState;
      }
      case END_OF_MESSAGE: {
        return state.map((msg) =>
          msg.sender === 'bot' && !msg.completed
            ? { ...msg, completed: true }
            : msg
        );
      }
      default: {
        return state;
      }
    }
};

  

export const ChatInterface = () => {
  const initialState: ConversationState = []; 
  const [conversation, dispatch] = useReducer(conversationReducer, initialState);
  const [input, setInput] = useState('');
  const { userToken } = useAuth();
  const endOfMessagesRef = useRef<null | HTMLDivElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  // Scrolls to the end of the messages
  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [conversation]);

// Clean up the WebSocket when the component unmounts
  useEffect(() => {
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!userToken) return;
  
    const ws = new WebSocket(`ws://localhost:8000/agent/ws/chat?token=${userToken.token}`);
    
    ws.onopen = () => {
        console.log('WebSocket Client Connected');
        dispatch({type: ADD_MESSAGE, payload: { sender: 'user', text: 'Hello' }});
    };
    
    ws.onmessage = (event) => {
        if (event.data.length > 0) {
            const data = JSON.parse(event.data);
        
            if (!data.end_of_message) {
            dispatch({
                type: 'APPEND_TO_LAST_MESSAGE',
                payload: { text: data.message },
            });
            } else {
            dispatch({ type: 'END_OF_MESSAGE' });  // No payload needed for this action
            }
        }
    };
      
      
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  
    // Store the WebSocket reference
    websocketRef.current = ws;
  
    // Define the cleanup function
    return () => {
      ws.close();
    };
  }, [userToken]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput) {
    console.log(`calling initial dispatch with ${trimmedInput}`); 
    dispatch({type: ADD_MESSAGE, payload: { sender: 'user', text: trimmedInput }});

    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({ message: trimmedInput }));
    }
      // Initialize a new WebSocket
    //   if (websocketRef.current) {
    //     websocketRef.current.close();
    //   }

    //   websocketRef.current = new WebSocket(`ws://localhost:8000/agent/ws/chat?token=${userToken?.token}`);
  
    //   websocketRef.current.onopen = () => {
    //     console.log('WebSocket Client Connected');
    //     websocketRef.current?.send(JSON.stringify({ message: trimmedInput }));
    //   };
  
    //   websocketRef.current.onmessage = (event) => {
    //     console.log('Received message from server: ', event.data);
    //     // Assume the server sends a special "end_of_message" property to indicate the end of a message
    //     if (event.data.length > 0) {
    //         const data = JSON.parse(event.data);
    //         console.log('Parsed data: ', data);
    //         console.log('Message text received:', data.message);
      
    //         if (data.end_of_message) {
    //             if (data.message.trim() !== '') {
    //                 console.log('Dispatching ADD_MESSAGE with data:', data.message);
    //                 dispatch({ type: 'ADD_MESSAGE', payload: { sender: 'bot', text: data.message } });
    //             }
    //         } else {
    //             console.log('Dispatching APPEND_TO_LAST_MESSAGE with data:', data.message);
    //             dispatch({ type: 'APPEND_TO_LAST_MESSAGE', payload: { text: data.message } });
    //         }
    //     }
    //   };
      
    //   websocketRef.current.onerror = (error) => {
    //     // Handle any errors that occur
    //     console.error('WebSocket error:', error);
    //   };
    }
  
    // Reset the input field
    setInput('');
  };

return (
    <div className="chat-container">
      <div className="message-container">
        {conversation.map((message: ChatMessage, index: number) => (
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
